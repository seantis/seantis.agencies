from five import grok

from plone.folder.interfaces import IExplicitOrdering
from plone.uuid.interfaces import IUUID
from zope.component import queryUtility

from seantis.agencies.types import IOrganization
from seantis.agencies.browser.base import BaseView


class OrganizationView(BaseView):

    grok.require('zope2.View')
    grok.context(IOrganization)
    grok.name('view')

    template = grok.PageTemplateFile('templates/organization.pt')

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
            memberships = sorted(memberships, key=lambda m: m[1])

        return memberships
