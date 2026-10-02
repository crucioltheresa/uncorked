"""
Wine images in one place: optimised URLs and responsive <img> tags.

On Cloudinary, images are served with automatic format and quality and
at the width they're shown at. With any other storage (local development,
tests) the plain file URL is used and no srcset is added.
"""
from django.utils.html import format_html, format_html_join

# Widths to offer for each kind of image, and how wide it's displayed
# (matches the wine grid: 1 column on phones, 2 or 3 on tablets, 4 from
# 1280px, and the wine page image at full width, then half width)
PRESETS = {
    "card": {
        "widths": (320, 480, 640, 800),
        "default": 480,
        "sizes": "(min-width: 1280px) 25vw, (min-width: 768px) 50vw, 100vw",
    },
    "detail": {
        "widths": (480, 720, 960, 1200, 1440),
        "default": 960,
        "sizes": "(min-width: 768px) 50vw, 100vw",
    },
}


def image_url(image, width=None):
    """Optimised URL for an ImageField file, or "" when there's none."""
    if not image:
        return ""
    storage = image.storage
    if hasattr(storage, "optimised_url"):
        return storage.optimised_url(image.name, width)
    return image.url


def responsive_image(image, preset, alt="", css_class="", eager=False,
                     priority=False):
    """
    An <img> for a wine image: src, srcset and sizes from the preset,
    lazy loading and async decoding unless it's above the fold (eager),
    and fetchpriority="high" for the page's main image (priority).
    """
    if not image:
        return ""
    settings = PRESETS[preset]
    attrs = [
        ("src", image_url(image, settings["default"])),
        ("alt", alt),
    ]
    if hasattr(image.storage, "optimised_url"):
        srcset = ", ".join(
            f"{image_url(image, width)} {width}w"
            for width in settings["widths"]
        )
        attrs += [("srcset", srcset), ("sizes", settings["sizes"])]
    if css_class:
        attrs.append(("class", css_class))
    if priority:
        attrs.append(("fetchpriority", "high"))
    if not eager and not priority:
        attrs.append(("loading", "lazy"))
    attrs.append(("decoding", "async"))
    return format_html(
        "<img{}>", format_html_join("", ' {}="{}"', attrs)
    )
