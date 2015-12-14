from five import grok

from zope.event import notify
from zope.interface import implements

from seantis.agencies.browser.base import BaseView
from seantis.agencies.interfaces import IActivityEvent
from seantis.agencies.types import IOrganization
from seantis.plonetools import tools


class ResourceViewedEvent(object):
    implements(IActivityEvent)


class OrganizationView(BaseView):

    grok.require('zope2.View')
    grok.context(IOrganization)
    grok.name('view')

    template = grok.PageTemplateFile('templates/organization.pt')
    event_fired = False

    def suborganizations(self):
        return [
            (brain["Title"] if "Title" in brain else "", brain.getURL())
            for brain in self.context.suborganizations()
        ]

    def memberships(self):
        memberships = []
        for brain in self.context.memberships():
            obj = brain.getObject()
            person = obj.person.to_object
            name = person.title if person else u''
            memberships.append((obj.role, name, obj.prefix, brain.getURL()))

        if self.context.display_alphabetically:
            sortkey = lambda m: tools.unicode_collate_sortkey()(m[1])
            memberships = sorted(memberships, key=sortkey)

        return memberships

    def update(self, **kwargs):
        super(OrganizationView, self).update(**kwargs)

        if not self.event_fired:
            notify(ResourceViewedEvent())
            self.event_fired = True
