from django.core.exceptions import ValidationError
import math

SPECIAL_CHARS = ",?;.:/!§%*$£@&#()[]{}+-"
# 10 characters including ASCII lower case, upper case, digits
PASSWORD_ENTROPY_LOW = 60
PASSWORD_ENTROPY_MEDIUM = 77
PASSWORD_ENTROPY_HIGH = 144
PASSWORD_STRENGTH_LOWEST = .3
PASSWORD_STRENGTH_LOW = .5
PASSWORD_STRENGTH_MEDIUM = .66
PASSWORD_STRENGTH_HIGH = .75


def password_strength_validator(
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
            "Password should contain at least %(value) characters",
            params={"value": min_length}
        )
    stats = password_stats(password)
    if stats.get("lower", 0) < min_lower \
            or stats.get("upper", 0) < min_upper \
            or stats.get("digit", 0) < min_digit \
            or stats.get("special", 0) < min_special:
        raise ValidationError("Password does not meet the minimal character requirements.")
    strength = password_strength(password, stats)
    if strength < min_strength:
        raise ValidationError("This password is too weak.")


def password_strength_grade(password: str, stats: dict[str, float] = None) -> str:
    """Returns a qualitative estimation of a password strength, as a grade:
    "LOWEST", "LOW", "MEDIUM", "HIGH", "HIGHEST"
    """
    strength_map = [
        (PASSWORD_STRENGTH_LOWEST, "LOWEST"),
        (PASSWORD_STRENGTH_LOW, "LOW"),
        (PASSWORD_STRENGTH_MEDIUM, "MEDIUM"),
        (PASSWORD_STRENGTH_HIGH, "HIGH"),
        (1.0, "HIGHEST")
    ]
    strength = password_strength(password, stats)
    grade = "LOWEST"
    for s, g in strength_map:
        if strength <= s:
            break
        else:
            grade = g
    return grade


def password_strength(password: str, stats: dict[str, float] = None) -> float:
    """Calculates the strength of a password as a float comprosed between 0 and 1.
    The strength is a function of the password's diversity and it's entropy
    compared to PASSWORD_ENTROPY_HIGH.
    """
    stats = stats or password_stats(password)
    entropy = password_entropy(password, stats)
    return min(1.0, (entropy * stats['diversity']) / PASSWORD_ENTROPY_HIGH)


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
