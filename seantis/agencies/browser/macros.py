from Acquisition import aq_inner, aq_parent
from collections import namedtuple
from five import grok
from plone import api
from seantis.agencies.types import IMember
from seantis.people.browser.macros import View as BaseView
from seantis.plonetools import tools


class View(BaseView):

    """ Overrides seantis.people.browser.macros to include the parent
    organisation in the membership listing on the person details view.

    """

    grok.context(IMember)
    grok.require('zope2.View')
    grok.name('seantis-people-macros')

    def organizations(self, person, method):
        Organization = namedtuple('Organization', ['title', 'url', 'role'])
        catalog = api.portal.get_tool('portal_catalog')

        organizations = []

        for uuid, memberships in getattr(person, method).items():

            brain = catalog(UID=uuid)[0]
            obj = brain.getObject()
            parent = aq_parent(aq_inner(obj))

            title = u'%s' % obj.title
            if parent:
                title = u'%s (%s)' % (title, parent.title)

            for membership in memberships:
                organizations.append(
                    Organization(title, brain.getURL(), membership.role)
                )

        sortkey = lambda org: tools.unicode_collate_sortkey()(org.title)
        return sorted(organizations, key=sortkey)
