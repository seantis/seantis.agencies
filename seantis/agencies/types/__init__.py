import logging
log = logging.getLogger('seantis.agencies')

from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from plone import api
from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.app.z3cform.wysiwyg import WysiwygFieldWidget
from plone.dexterity.content import Container
from plone.directives import form
from plone.namedfile.field import NamedImage

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

    display_alphabetically = schema.Bool(
        title=_(u'Display memberships alphabetically'),
        description=_(
            u'Tick this box to sort memberships alphabetically by name rather '
            u'than by their position in the folder.'
        ),
        default=False
    )

    export_fields = schema.List(
        title=_(u"Fields to export"),
        description=_(u"Fields to include in the PDF export"),
        required=False,
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary(terms=[
                SimpleTerm(value=u'role', title=_('Role')),
                SimpleTerm(value=u'title', title=_('Last Name First Name')),
                SimpleTerm(value=u'start', title=_('Start of membership')),
                SimpleTerm(value=u'postfix', title=_('Postfix')),
                SimpleTerm(value=u'lastname', title=_('Last Name')),
                SimpleTerm(value=u'firstname', title=_('First Name')),
                SimpleTerm(value=u'year', title=_('Year')),
                SimpleTerm(value=u'academic_title', title=_('Academic Title')),
                SimpleTerm(value=u'occupation', title=_('Occupation')),
                SimpleTerm(value=u'address', title=_('Address')),
                SimpleTerm(value=u'political_party',
                           title=_('Political Party')),
                SimpleTerm(value=u'phone', title=_('Phone')),
                SimpleTerm(value=u'direct_number', title=_('Direct number')),
            ])
        ),
        default=['role', 'title']
    )

    organigram = NamedImage(
        title=_(u'Organigram'),
        required=False
    )


class Organization(Container):

    pdfexportable = True

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

    postfix = schema.TextLine(
        title=_(u"Postfix"),
        required=False
    )


class Membership(PeopleMembership):
    pass
