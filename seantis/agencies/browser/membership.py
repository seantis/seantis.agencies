from five import grok
from seantis.agencies.browser.base import BaseView
from seantis.agencies.types import IMembership


class OrganizationView(BaseView):

    grok.require('zope2.View')
    grok.context(IMembership)
    grok.name('view')

    template = grok.PageTemplateFile('templates/membership.pt')

    def person(self):
        person = self.context.person.to_object
        if person:
            return [person.title, person.absolute_url()]
        return [u'', u'']
