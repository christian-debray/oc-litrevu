from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from urllib import parse as parse_url


def redirect_next(request: HttpRequest, default: str) -> HttpResponse:
    return redirect(get_next_route(request, default))


def get_next_route(request: HttpRequest, default: str) -> str:
    """Tries to read the next url field in the request.
    Falls back to default value set by the second parameter.
    """
    return request.POST.get("next") or request.GET.get("next") or default


def add_next_url(url: str, request: HttpRequest, next_url: str = None) -> str:
    """Appends or updates the 'next" query parameter in a URL.
    Helps customizing redirects after processing a form, for instance.

    The next_url string can be either a view name as defined in the URLConf or a full URL.

    If the second parameter is not set, tries to find the next url in the current request.
    If no 'next' query parameter is found nor set, returns the url without changes.
    """
    next_url = next_url or get_next_route(request, next_url)
    if next_url:
        parts = parse_url.urlsplit(url)
        qs = parse_url.parse_qs(parts.query) or {}
        qs.update({"next": next_url})
        new_query = parse_url.urlencode(qs)
        return parse_url.urlunsplit(
            [parts.scheme, parts.netloc, parts.path, new_query, parts.fragment]
        )
    else:
        return url
