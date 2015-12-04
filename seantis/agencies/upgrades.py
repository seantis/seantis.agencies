# -*- coding: utf-8 -*-

from zope.component import getUtility

from plone import api
from plone.dexterity.interfaces import IDexterityFTI

from seantis.people import catalog_id
from seantis.people.supermodel.indexing import update_related_indexes


def run_import_step_from_profile(step, module, profile):
    setup = api.portal.get_tool('portal_setup')
    profile = 'profile-{}:{}'.format(module, profile)
    setup.runImportStepFromProfile(profile, step)


def upgrade_portal_type(portal_type, module, profile):
    run_import_step_from_profile('typeinfo', module, profile)
    update_related_indexes(getUtility(IDexterityFTI, portal_type))


def upgrade_1000_to_1001(context):
    upgrade_portal_type(
        'seantis.agencies.membership', 'seantis.agencies', 'default'
    )

    catalog = api.portal.get_tool('portal_catalog')
    memberships = catalog.unrestrictedSearchResults(
        portal_type='seantis.agencies.membership'
    )

    for membership in [m.getObject() for m in memberships]:
        if not hasattr(membership, 'prefix'):
            membership.prefix = None
        if membership.note == u'*':
            membership.prefix = membership.note
            membership.note = None


def upgrade_1001_to_1002(context):
    upgrade_portal_type(
        'seantis.agencies.membership', 'seantis.agencies', 'default'
    )


def upgrade_1002_to_1003(context):
    upgrade_portal_type(
        'seantis.agencies.organization', 'seantis.agencies', 'default'
    )


def upgrade_1003_to_1004(context):
    upgrade_portal_type(
        'seantis.agencies.organization', 'seantis.agencies', 'default'
    )


def upgrade_1004_to_1005(context):
    catalog = api.portal.get_tool(catalog_id)
    catalog.refreshCatalog(clear=1)


def upgrade_1005_to_1006(context):
    # Replace ['lastname', 'firstname'] with ['title'] in export fields
    catalog = api.portal.get_tool('portal_catalog')
    brains = catalog.unrestrictedSearchResults(
        portal_type='seantis.agencies.organization'
    )

    for brain in brains:
        organization = brain.getObject()
        if hasattr(organization, 'export_fields'):
            fields = organization.export_fields
            if u'lastname' in fields and u'firstname' in fields:
                index = fields.index(u'lastname')
                if fields.index(u'firstname') == index + 1:
                    print 'changed'
                    fields.insert(index, u'title')
                    fields.remove(u'lastname')
                    fields.remove(u'firstname')
                    organization.export_fields = fields


def upgrade_1006_to_1007(context):
    upgrade_portal_type(
        'seantis.agencies.organization', 'seantis.agencies', 'default'
    )
    run_import_step_from_profile('actions', 'seantis.agencies', 'default')
