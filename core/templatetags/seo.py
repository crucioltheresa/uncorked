from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_url(context, url):
    """
    Full URL for canonical and Open Graph tags. Relative paths get this
    site's scheme and host; absolute URLs (e.g. Cloudinary) are kept as is.
    """
    request = context.get("request")
    if not url or request is None:
        return url or ""
    return request.build_absolute_uri(url)
