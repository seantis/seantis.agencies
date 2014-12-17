from five import grok

from plone.folder.interfaces import IExplicitOrdering
from plone.uuid.interfaces import IUUID
from zope.component import queryUtility

from seantis.agencies.types import IMembership
from seantis.agencies.browser.base import BaseView


class OrganizationView(BaseView):

    grok.require('zope2.View')
    grok.context(IMembership)
    grok.name('view')

    template = grok.PageTemplateFile('templates/membership.pt')

    def person(self):
        person = self.context.person.to_object
        return [person.title, person.absolute_url()]
