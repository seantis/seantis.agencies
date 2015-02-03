import logging
log = logging.getLogger('seantis.agencies')

import re
import transaction
import xlrd

from five import grok
from plone.dexterity.utils import createContentInContainer
from plone.directives import form
from plone.namedfile.field import NamedFile
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from StringIO import StringIO
from z3c.form import field
from z3c.form.button import buttonAndHandler
from z3c.form.error import InvalidErrorViewSnippet
from z3c.relationfield.relation import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope.component import getUtility
from zope.interface import Invalid

from seantis.agencies import _
from seantis.agencies.browser.xlsexport import (
    TITLES_REGISTER, FIELDS_REGISTER,
    TITLES_ORGANIZATION, FIELDS_ORGANIZATION
)
from seantis.plonetools import unrestricted


KNOWN_PUBLISH_ACTIONS = (
    'publish', 'onegov-simple-workflow--TRANSITION--publish--draft_published'
)


class IImportSchema(form.Schema):
    xls_file = NamedFile(title=_(u"XLS file"))


class ImportView(form.Form):
    fields = field.Fields(IImportSchema)

    grok.context(IPloneSiteRoot)
    grok.require('cmf.ManagePortal')
    grok.name('import-agencies')

    ignoreContext = True

    def abort_action(self, action, messages):
        """ Aborts the given action and adds the list of messages as
        error-widgets to the form."""
        form = action.form
        formcontent = form.getContent()
        request = action.request

        for msg in messages:
            args = (Invalid(msg), request, None, None, form, formcontent)
            err = InvalidErrorViewSnippet(*args)
            err.update()
            form.widgets.errors += (err, )

        form.status = form.formErrorsMessage

        transaction.abort()

    @buttonAndHandler(_(u'Import'), name='import')
    def import_xls(self, action):
        """ Create and handle form button."""

        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        try:
            io = StringIO(data["xls_file"].data)
            workbook = xlrd.open_workbook(file_contents=io.read())
        except (KeyError, TypeError, xlrd.XLRDError):
            self.abort_action(action, (_(u'Invalid XLS file'),))
            return

        errors = self._import_xls(workbook)

        if errors:
            self.abort_action(action, errors)
        else:
            self.status = _(u'Items imported. Please reindex.')

    def parse_organization_sheet(self, sheet, errors):
        organizations = {}
        for row in range(1, sheet.nrows):
            try:
                values = [cell.value.strip() for cell in sheet.row(row)]
                assert len(values) == len(TITLES_ORGANIZATION)
                assert values[0] not in organizations

                organization = {}
                for index, field in enumerate(FIELDS_ORGANIZATION):
                    organization[field] = values[2+index]

                children = [id.strip() for id in values[1].split(',') if id]
                organization['_children'] = children

                organizations[values[0]] = organization
            except:
                errors.append(_(u'Invalid row ${row} in sheet ${sheet}',
                                mapping={u'row': row, u'sheet': sheet.name}))

        found = 0
        start = None
        for key, value in organizations.iteritems():
            if sheet.name == value['title']:
                start = key
                found += 1
        if found != 1:
            errors.append(_(u'Top level organizations not found'))
        else:
            organizations['first'] = start

        return organizations

    def parse_register_sheet(self, sheet, errors):
        members = []

        for row in range(1, sheet.nrows):
            try:
                values = [cell.value.strip() for cell in sheet.row(row)]
                assert len(values) == len(TITLES_REGISTER)

                member = {}
                for index, field in enumerate(FIELDS_REGISTER):
                    member[field] = values[index]

                pattern = re.compile(
                    r'\((.*)\)\((.*)\)\((.*)\)\((.*)\)\((.*)\)'
                )
                strings = [
                    membership.strip() for membership
                    in values[len(FIELDS_REGISTER)].split('//') if membership
                ]
                memberships = [pattern.match(str).groups() for str in strings]
                member['_memberships'] = memberships

                members.append(member)
            except Exception as e:
                errors.append(_(u'Invalid row ${row} in sheet ${sheet}',
                                mapping={u'row': row, u'sheet': sheet.name}))

        return members

    def publish_content(self, content):
        wftool = getToolByName(self.context, 'portal_workflow')
        with unrestricted.run_as('Manager'):
            for action in KNOWN_PUBLISH_ACTIONS:
                try:
                    wftool.doActionFor(content, action)
                    break
                except WorkflowException:
                    pass

    def create_organisation(self, context, id, organizations, memberships,
                            count=0):
        organization = organizations[id]

        kwargs = dict(
            (key, unicode(value)) for (key, value) in organization.iteritems()
            if not key.startswith('_')
        )
        content = createContentInContainer(
            context, "seantis.agencies.organization", **kwargs
        )
        self.publish_content(content)
        count += 1
        log.info(
            'added organization %s (%i/%i)' % (
                organization['title'], count, len(organizations)-1
            )
        )

        if id in memberships:
            for membership in sorted(memberships[id], key=lambda i: i[3]):
                person = RelationValue(membership[4])
                m_content = createContentInContainer(
                    content, "seantis.agencies.membership",
                    role=unicode(membership[0]),
                    start=unicode(membership[1]),
                    prefix=unicode(membership[2]),
                    person=person
                )
                self.publish_content(m_content)
                log.info('added %s to %s' % (person.to_object.title,
                                             organization['title']))

        for child in organization['_children']:
            count = self.create_organisation(
                content, child, organizations, memberships, count
            )

        return count

    def _import_xls(self, workbook):
        errors = []
        organizations = {}
        registers = {}

        for sheet in workbook.sheets():
            titles = []
            if sheet.nrows > 1:
                titles = [cell.value for cell in sheet.row(0)]

            if titles == TITLES_ORGANIZATION:
                organizations[sheet.name] = self.parse_organization_sheet(
                    sheet, errors
                )
            elif titles == TITLES_REGISTER:
                registers[sheet.name] = self.parse_register_sheet(
                    sheet, errors
                )
            else:
                log.warn('ignored sheet %s' % sheet.name)

        if errors:
            return errors

        intids = getUtility(IIntIds)
        memberships = {}
        for name, members in registers.iteritems():
            directory = createContentInContainer(
                self.context, "seantis.people.list", title=name
            )
            self.publish_content(directory)
            log.info('added directory %s' % name)

            for index, member in enumerate(members):
                kwargs = dict(
                    (key, unicode(value)) for (key, value)
                    in member.iteritems() if not key.startswith('_')
                )
                content = createContentInContainer(
                    directory, "seantis.agencies.member",
                    exclude_from_nav=True, **kwargs
                )
                self.publish_content(content)
                uid = intids.getId(content)
                log.info(
                    'added person %s %s (%i/%i)' % (
                        member['firstname'], member['lastname'], index+1,
                        len(members)
                    )
                )

                for membership in member['_memberships']:
                    if membership[0] not in memberships:
                        memberships[membership[0]] = []
                    memberships[membership[0]].append((
                        membership[1], membership[2], membership[3],
                        membership[4], uid
                    ))

        for name, organization in organizations.iteritems():
            self.create_organisation(
                self.context, organization['first'], organization, memberships
            )

        log.info('import finished')
