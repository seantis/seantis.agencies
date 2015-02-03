import os

from five import grok
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from StringIO import StringIO
from xlwt import Workbook


TITLES_REGISTER = [
    u'Akademischer Titel', u'Beruf', u'Vorname', u'Nachname',
    u'Politische Partei', u'Jahrgang', u'E-Mail', u'Adresse', u'Telefon',
    u'Direktnummer', u'Anrede', u'Fax', u'Website', u'Stichworte',
    u'Bemerkungen', u'Organisationen'
]
FIELDS_REGISTER = [
    'academic_title', 'occupation', 'firstname', 'lastname',
    'political_party', 'year', 'email', 'address', 'phone', 'direct_number',
    'salutation', 'fax', 'website', 'keywords', 'remarks'
]

TITLES_ORGANIZATION = [
    u'ID', u'Unterorganisationen', u'Titel', u'Beschreibung', u'Portrait'
]
FIELDS_ORGANIZATION = [
    'title', 'description', 'portrait'
]


class ExportView(grok.View):

    grok.name('export-agencies')
    grok.context(IPloneSiteRoot)
    grok.require('cmf.ManagePortal')

    template = None

    def get_root_organizations(self):
        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(self.context.getPhysicalPath())
        organizations = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.agencies.organization',
            sort_on='getObjPositionInParent',
        )
        return [organization.getObject() for organization in organizations]

    def get_root_registers(self):
        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(self.context.getPhysicalPath())
        organizations = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.people.list',
            sort_on='getObjPositionInParent',
        )
        return [organization.getObject() for organization in organizations]

    def get_simple_uid(self, uid, uids):
        if uid not in uids:
            uids[uid] = uids['next']
            uids['next'] = uids['next'] + 1
        return uids[uid]

    def write_organization(self, sheet, organization, uids):
        uid = self.get_simple_uid(organization.UID(), uids)
        children = [o.getObject() for o in organization.suborganizations()]
        memberships = [m.getObject() for m in organization.memberships()]

        index = len(sheet.rows)
        sheet.row(index).write(0, str(uid))
        sheet.row(index).write(1, ','.join(
            [str(self.get_simple_uid(child.UID(), uids)) for child in children]
        ))
        for col, field in enumerate(FIELDS_ORGANIZATION):
            sheet.row(index).write(2+col, getattr(organization, field))

        for child in children:
            self.write_organization(sheet, child, uids)

    def write_register(self, sheet, register, uids):
        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(register.getPhysicalPath())

        people = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.agencies.member'
        )
        for index, brain in enumerate(people):
            person = brain.getObject()

            for col, field in enumerate(FIELDS_REGISTER):
                sheet.row(index+1).write(col, getattr(person, field))

            memberships = [
                u'(%s)(%s)(%s)(%s)(%s)' % (
                    str(uids.get(item.aq_parent.UID(), '')),
                    item.role, item.start or '', item.prefix or '',
                    str(item.aq_parent.getObjectPosition(item.getId()))
                )
                for sublist in person.memberships.values() for item in sublist
            ]

            sheet.row(index+1).write(
                len(FIELDS_REGISTER), u'//'.join(memberships)
            )

    def render(self):
        book = Workbook(encoding='utf-8')
        uids = {'next': 0}

        root_organizations = self.get_root_organizations()
        for organization in root_organizations:
            sheet = book.add_sheet(organization.title)
            for index, cell in enumerate(TITLES_ORGANIZATION):
                sheet.row(0).write(index, cell)
            self.write_organization(sheet, organization, uids)

        root_registers = self.get_root_registers()
        for register in root_registers:
            sheet = book.add_sheet(register.title)
            for index, cell in enumerate(TITLES_REGISTER):
                sheet.row(0).write(index, cell)

            self.write_register(sheet, register, uids)

        filehandle = StringIO()
        if root_organizations or root_registers:
            book.save(filehandle)
        response = filehandle.getvalue()

        filehandle.seek(0, os.SEEK_END)
        filesize = filehandle.tell()
        filehandle.close()

        self.request.RESPONSE.setHeader('Content-disposition', 'export.xls')
        self.request.RESPONSE.setHeader('Content-Type', 'application/xls')
        self.request.RESPONSE.setHeader('Content-Length', filesize)

        return response
