from .base import BaseView, BaseForm
from .renderer import UUIDListRenderer
from seantis.people.browser.renderer import renderers
from seantis.people.utils import UUIDList


# Patch the renderer to include the parent organization
renderers[UUIDList] = UUIDListRenderer()
