from django import template

from core import images

register = template.Library()


@register.filter
def image_url(image, width=None):
    """{{ wine.image|image_url:128 }}: optimised image URL at that width."""
    return images.image_url(image, width)


@register.simple_tag
def wine_image(image, preset="card", alt="", css_class="", eager=False,
               priority=False):
    """
    {% wine_image wine.image "card" alt=wine.name %}: a responsive <img>
    (see core.images.PRESETS). Add eager=True for images above the fold
    and priority=True for the page's main image.
    """
    return images.responsive_image(
        image, preset, alt=alt, css_class=css_class, eager=eager,
        priority=priority,
    )
