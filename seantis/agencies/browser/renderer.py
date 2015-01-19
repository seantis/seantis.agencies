from Acquisition import aq_inner, aq_parent

from plone.app.uuid.utils import uuidToCatalogBrain

from seantis.people.browser.renderer import (
    UUIDListRenderer as BaseUUIDListRenderer
)
from seantis.plonetools import tools


class UUIDListRenderer(BaseUUIDListRenderer):

    def brain_to_link(self, brain):
        obj = brain.getObject()
        parent = aq_parent(aq_inner(obj))

        title = u'%s' % obj.title
        if parent:
            # title = u'%s > %s' % (parent.title, title)
            title = u'%s (%s)' % (title, parent.title)

        return (brain.getURL(), title)

    def __call__(self, context, field, options):

        if not all([field == 'organization_uuids',
                    context.portal_type == 'seantis.agencies.member']):
            return super(UUIDListRenderer, self).__call__(context, field,
                                                          options)

        uuids = getattr(context, field, None)
        if not uuids:
            return u''

        brains = (b for b in (uuidToCatalogBrain(uid) for uid in uuids) if b)
        items = (self.brain_to_link(b) for b in brains)

        unicode_sortkey = tools.unicode_collate_sortkey()
        items = sorted(items, key=lambda i: unicode_sortkey(i[1]))

        return ', '.join(
            self.template.substitute(url=url, title=title)
            for url, title in items
        )
