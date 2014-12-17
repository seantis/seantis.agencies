import logging
log = logging.getLogger('seantis.agencies')

from datetime import date
from five import grok

from zope import schema
from zope.interface import Interface, Invalid

from plone import api
from plone.app.z3cform.wysiwyg import WysiwygFieldWidget
from plone.dexterity.content import Container
from plone.directives import form
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation

from collective.dexteritytextindexer import searchable

from seantis.people.types.base import PersonBase
from seantis.people.interfaces import IMembership as IPeopleMembership
from seantis.people.content import Membership as PeopleMembership
from seantis.agencies import _


class IMember(form.Schema):
    form.model("member.xml")


class Member(PersonBase):
    pass


@form.default_value(field=IExcludeFromNavigation['exclude_from_nav'])
def excludeFromNavDefaultValue(data):
    return True


class IOrganization(form.Schema):

    searchable('title')
    title = schema.TextLine(
        title=_(u'Title')
    )

    searchable('description')
    description = schema.Text(
        title=_(u'Description'),
        required=False
    )

    searchable('portrait')
    form.widget(portrait=WysiwygFieldWidget)
    portrait = schema.Text(
        title=_(u'Portrait'),
        required=False
    )


class Organization(Container):

    def memberships(self):
        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(self.getPhysicalPath())

        memberships = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.agencies.membership',
            sort_on='getObjPositionInParent',
        )

        return memberships

    def suborganizations(self):
        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(self.getPhysicalPath())

        suborganizations = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.agencies.organization',
            sort_on='getObjPositionInParent',
        )

        return suborganizations


class IMembership(IPeopleMembership):

    start = schema.TextLine(
        title=_(u"Start of membership"),
        required=False
    )

    prefix = schema.TextLine(
        title=_(u"Prefix"),
        required=False
    )


class Membership(PeopleMembership):
    pass
