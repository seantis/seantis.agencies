# -*- coding: utf-8 -*-

from zope.component import getUtility

from plone import api
from plone.dexterity.interfaces import IDexterityFTI

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
