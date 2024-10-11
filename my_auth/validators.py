from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import math

# special chars: !"#$%&\'()*+,-./
SPECIAL_CHARS = [chr(x) for x in range(ord(' ')+1, ord('0'))]
# Low entropy = 10 characters including ASCII lower case, upper case, digits
PASSWORD_ENTROPY_LOW = 60
PASSWORD_ENTROPY_MEDIUM = 77
PASSWORD_ENTROPY_HIGH = 144
#
# password strength constants are empirical.
# see notes in the password_strength function

PASSWORD_STRENGTH_LOWEST = 0
PASSWORD_STRENGTH_LOW = 0.3
PASSWORD_STRENGTH_MEDIUM = 0.5
PASSWORD_STRENGTH_HIGH = 0.75
PASSWORD_STRENGTH_HIGHEST = 0.9

STRENGTH_MAP = [
    (PASSWORD_STRENGTH_LOWEST, _("lowest_password_strength"), "PASSWORD_STRENGTH_LOWEST"),
    (PASSWORD_STRENGTH_LOW, _("low_password_strength"), "PASSWORD_STRENGTH_LOW"),
    (PASSWORD_STRENGTH_MEDIUM, _("medium_password_strength"), "PASSWORD_STRENGTH_MEDIUM"),
    (PASSWORD_STRENGTH_HIGH, _("high_password_strength"), "PASSWORD_STRENGTH_HIGH"),
    (PASSWORD_STRENGTH_HIGHEST, _("highest_password_strength"), "PASSWORD_STRENGTH_HIGHEST"),
]


def password_strength_validation(
    password: str,
    min_length: int = 9,
    min_strength: float = PASSWORD_STRENGTH_MEDIUM,
    min_lower: int = 1,
    min_upper: int = 1,
    min_digit: int = 1,
    min_special: int = 1,
):
    """Validate a password strength.
    raise ValiationError if a password strength is below minimal complexity.
    otherwise return none.
    """
    if len(password) < min_length:
        raise ValidationError(
            _("Password should contain at least %(value)d characters"),
            params={"value": min_length},
            code="min_length_error",
        )
    stats = password_stats(password)
    if (
        stats.get("lower", 0) < min_lower
        or stats.get("upper", 0) < min_upper
        or stats.get("digit", 0) < min_digit
        or stats.get("special", 0) < min_special
    ):
        raise ValidationError(
            _("Password does not meet the minimal character requirements."),
            code="min_char_error",
        )
    strength = password_strength(password, stats)
    if strength < min_strength:
        raise ValidationError(
            _("This password is too weak."), code="min_strength_error"
        )


def password_strength_from_symbol(strength_symbol: str) -> float:
    """Interprets the parameter as a constant name defining a password strength,
    as defined in this module in STRENGTH_MAP"""
    map = {symb: val for val, _, symb in STRENGTH_MAP}
    return map.get(strength_symbol, None)


def password_strength_grade(strength: float) -> str:
    """Returns a human readable string representing
    the qualitative estimation of a password strength, as a grade:
    "LOWEST", "LOW", "MEDIUM", "HIGH", "HIGHEST"
    """
    grade = None
    for s, g, x in STRENGTH_MAP:
        if strength < s:
            break
        else:
            grade = g
    return grade


def password_strength(password: str, stats: dict[str, float] = None) -> float:
    """Calculates the strength of a password as a float comprosed between 0 and 1.

    The strength is a function of the password's diversity and it's entropy
    compared to PASSWORD_ENTROPY_HIGH.
    The entropy of a password rises with its length and the range of character types
    found in the password.

    The current algo would evaluate:
    -   `"A1,azer"` as a weak password
    -   `"A1-azertyuiq"` as a medium strength password
    -   `"A1,azertyuiqsdfgh"` as a strong password
    -   `"A1,azertyuiqsdfghjklm"` as very strong password
    """
    stats = stats or password_stats(password)
    entropy = password_entropy(password, stats)
    # allow for some character repetition:
    diversity_factor = min(1.0, stats["diversity"] / .6)
    return min(1.0, (entropy * diversity_factor) / PASSWORD_ENTROPY_HIGH)


def password_entropy(password: str, stats: dict[str, float] = None) -> int:
    """Calculates the password entropy,
    ie an estimate of the worst-case cost to crack the password by brute-force.

    Entropy formula: E = log²(R^L), with:
    - E: the entropy mesured in bits
    - R: the character range used in this password
    - L: the password length

    see https://nordvpn.com/blog/what-is-password-entropy/#:~:text=You%20can%20calculate%20password%20entropy,password%20entropy%2C%20measured%20in%20bits.
    """
    stats = stats or password_stats(password)
    r = password_char_range(password, stats)
    return round(math.log2(math.pow(r, len(password))))


def password_char_range(password: str, stats: dict[str, float] = None) -> int:
    """Returns an estimate of the possible character range of a password,
    basing on the character types.

    - password: the password to analyze
    - stats: the result of password_stats(), if already available

    ex:
    - "ABC" => range = 26
    - "abc" => range = 26
    - "aB" => range = 2*26 = 52
    - "ab1" => range = 2*26 + 10 = 62

    For practical reasons, the range of alphabetic characters reduced to the latin character set,
    meaning the returned value may underestimate the actual range when characters of a wider set
    are available."""
    stats = stats or password_stats(password)
    r = 0
    if stats["upper"] > 0:
        r += 26
    if stats["lower"] > 0:
        r += 26
    if stats["digit"] > 0:
        r += 10
    if stats["special"] > 0:
        r += len(SPECIAL_CHARS)
    return r


def password_stats(password: str) -> dict[str, float]:
    """Parse a password and return some stats on character types
    and diversity of employed characters."""
    diversity = 0
    upper = 0
    lower = 0
    digit = 0
    alpha = 0
    special = 0
    chars_map = {}
    for c in password:
        chars_map[c] = chars_map.get(c, 0) + 1
        if str.isalpha(c):
            alpha += 1
            if str.isupper(c):
                upper += 1
            else:
                lower += 1
        elif str.isnumeric(c):
            digit += 1
        elif c in SPECIAL_CHARS:
            special += 1
    diversity = len(chars_map) / len(password)
    return {
        "diversity": diversity,
        "alpha": alpha,
        "lower": lower,
        "upper": upper,
        "digit": digit,
        "special": special,
    }


def password_example(required_strength: float) -> str:
    """Generates a random password example meeting a strength requirement.
    """
    low_chars = [chr(x) for x in range(ord('a'), ord('z') + 1)]
    upper_chars = [chr(x) for x in range(ord('A'), ord('Z') + 1)]
    digits = [chr(x) for x in range(ord('0'), ord('9') + 1)]
    from itertools import chain
    import random
    table = list(chain(low_chars, upper_chars, digits, SPECIAL_CHARS))
    random.shuffle(table)
    i = 1
    while password_strength("".join(table[:i])) < required_strength:
        i += 1
    return "".join(table[:i])


class StrengthPasswordValidator:
    """Validate a password strength.
    Strength is calculated on a password's 'entropy',
    which increases with the password size and availalble character range.

    Validator settings:
        - min_strength: float between 0 and 1, defaults to PASSWORD_STRENGTH_MEDIUM.
            also accepts a strign representing one of the PASSWORD_STRENGTH_*
            You can use on of the PASSWORD_STRENGTH_* constants defined in this module.
            min_strength is a qualitative measurement of the password strength,
            compared to an "optimal" password. See the password_strength() function
            defined in this module for calculation details.
        - min_length: (optional) int, defaults to 0, set 0 to ignore.
            Defines the minimal length of a valid password.
        - min_lower: (optional) int, defaults to 0, set 0 to ignore.
            Defines the minimal lowercase characters required in a valid password.
        - min_upper: (optional) int, defaults to 0, set 0 to ignore.
            Defines the minimal uppercase characters required in a valid password.
        - min_digit: (optional) int, defaults to 0, set 0 to ignore.
            Defines the minimal numeric characters required in a valid password.
        - min_special: (optional) int, defaults to 0, set 0 to ignore.
            Defines the minimal non-alphanumeric characters required in a valid password.
    """

    def __init__(
        self,
        min_strength: float | str = PASSWORD_STRENGTH_MEDIUM,
        min_length: int = 0,
        min_lower: int = 0,
        min_upper: int = 0,
        min_digit: int = 0,
        min_special: int = 0,
    ):
        if str(min_strength).isnumeric():
            self.min_strength: float = float(min_strength)
        else:
            self.min_strength: float = float(password_strength_from_symbol(min_strength))
        self.min_length: int = min_length
        self.min_lower: int = min_lower
        self.min_upper: int = min_upper
        self.min_digit: int = min_digit
        self.min_special: int = min_special

    def validate(self, password: str, user=None):
        """Validates a password based on this validator's settings.
        Raises a ValidationError when the password doesn't meet the requirements set for this validator.
        """
        try:
            password_strength_validation(
                password=password,
                min_length=self.min_length,
                min_strength=self.min_strength,
                min_lower=self.min_lower,
                min_upper=self.min_upper,
                min_digit=self.min_digit,
                min_special=self.min_special,
            )
        except ValidationError as e:
            msg = e.message + "\n" + self.get_help_text()
            raise ValidationError(msg, code=e.code)

    def get_help_text(self) -> str:
        """Validator help text."""
        help_msg = _("Choose a password strong enough")
        if length_suggestion := self.length_hint():
            help_msg += " (" + _("at least %d characters") % length_suggestion + ")"
        charlist = []
        if self.min_digit > 0:
            charlist.append(_("numeric_chars"))
        if self.min_lower > 0:
            charlist.append(_("lowercase_letters"))
        if self.min_upper > 0:
            charlist.append(_("uppercase_letters"))
        if self.min_special > 0:
            charlist.append(_("special_chars"))

        if len(charlist):
            help_msg += " " + _("containing") + " " + ", ".join(charlist)
        return help_msg

    def length_hint(self) -> int:
        """Returns an estimate of minimal password length to meet strength or length requirement.
        """
        if self.min_strength:
            return len(password_example(self.min_strength))
        else:
            return self.min_length
