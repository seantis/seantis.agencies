import logging
log = logging.getLogger('seantis.agencies')

import os
import codecs
import re
import tempfile
import time
import transaction

from datetime import datetime, date, timedelta
from io import BytesIO
from pdfdocument.document import MarkupParagraph
from reportlab.lib.units import cm
from threading import Lock

from five import grok
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.synchronize import synchronized
from zExceptions import NotFound
from zope.interface import Interface

from kantonzugpdf import ReportZug
from kantonzugpdf.report import PDF

from seantis.agencies import _
from seantis.agencies.types import IOrganization
from seantis.plonetools import tools, unrestricted


PDF_EXPORT_FILENAME = u'exported_pdf.pdf'


class OrganizationsPdf(PDF):

    def h4(self, text, toc_level=3):
        self.add_toc_heading(text, self.style.heading4, None, None)

    def h5(self, text, toc_level=4):
        self.add_toc_heading(text, self.style.heading5, None, None)

    def h6(self, text, toc_level=5):
        self.add_toc_heading(text, self.style.heading6, None, None)


class OrganizationsReport(ReportZug):
    """ Report to show the memberships of organizations found in the
    current context.

    """

    def __init__(self, root=None, toc=True):
        self.root = root
        self.toc = toc
        self.file = BytesIO()
        self.pdf = OrganizationsPdf(self.file)
        self.pdf.init_report(
            page_fn=self.first_page, page_fn_later=self.later_page
        )
        if not toc:
            self.pdf.toc_numbering = None

    def translate(self, text):
        return tools.translator(self.request, 'seantis.agencies')(text)

    def get_print_date_text(self):
        date_text = api.portal.get_localized_time(
            datetime=datetime.combine(
                date.today(), datetime.min.time()
            )
        )

        return self.translate(
            _(u'Print date: ${date}', mapping={'date': date_text})
        )

    def populate(self):
        """ Builds the structure of the report before it gets rendered. """
        self.title = self.context.title
        self.adjust_style()

        # First page contains the title and table of contents
        self.pdf.h(self.title)
        if self.toc:
            self.pdf.table_of_contents()
            self.pdf.pagebreak()

        # Iterate recursive over organizations
        root_organizations = self.get_root_organizations()

        for organization in root_organizations:
            self.populate_organization(organization, 0)

    def get_root_organizations(self):
        if self.root:
            return [self.root]

        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(self.context.getPhysicalPath())
        organizations = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.agencies.organization',
            sort_on='getObjPositionInParent',
        )
        return [organization.getObject() for organization in organizations]

    def populate_organization(self, organization, level, last_child=False):

        has_content = False
        if level:
            # Title
            if level == 1:
                self.pdf.h1(organization.title)
            elif level == 2:
                self.pdf.h2(organization.title)
            elif level == 3:
                self.pdf.h3(organization.title)
            elif level == 4:
                self.pdf.h4(organization.title)
            elif level == 5:
                self.pdf.h5(organization.title)
            elif level == 6:
                self.pdf.h6(organization.title)
            else:
                self.pdf.p_markup(organization.title, self.pdf.style.heading6)

        # Portrait
        if organization.portrait and organization.portrait.strip():
            has_content = True
            self.pdf.spacer()
            try:
                # remove target attribute from link tags
                self.pdf.p_markup(
                    re.sub(r"target=[\"'].*\w[\"']", "",
                           organization.portrait)
                )
            except ValueError:
                # the portrait might have some unprocessable html code
                self.pdf.p(organization.portrait)
                log.warn('%s contains invalid markup' % organization.title)

        # Table with memberships
        memberships = []
        for brain in organization.memberships():
            membership = brain.getObject()
            person = membership.person.to_object
            fields = organization.export_fields

            role = membership.role if 'role' in fields else ''
            text = ''
            name = ''

            if person:
                name = person.title
                text = ', '.join([
                    getattr(person, field, '') for field in fields
                    if getattr(person, field, '')
                ])

            memberships.append((role, membership.prefix, text, name))

        if organization.display_alphabetically:
            sortkey = lambda m: tools.unicode_collate_sortkey()(m[3])
            memberships = sorted(memberships, key=sortkey)

        table_data = []
        for membership in memberships:
            table_data.append([
                MarkupParagraph(membership[0], self.pdf.style.normal),
                MarkupParagraph(membership[1], self.pdf.style.normal),
                MarkupParagraph(membership[2], self.pdf.style.normal),
            ])

        table_columns = [4.3 * cm, 0.5 * cm, 11 * cm]
        if table_data:
            has_content = True
            self.pdf.spacer()
            self.pdf.table(table_data, table_columns)

        children = [o.getObject() for o in organization.suborganizations()]

        break_page = (
            (level < 3 and has_content) or
            (level == 3 and not len(children)) or
            (level == 4 and last_child)
        )
        if break_page:
            self.pdf.pagebreak()
        else:
            self.pdf.spacer()

        time.sleep(0)

        for idx, child in enumerate(children):
            self.populate_organization(child, level + 1,
                                       idx == len(children) - 1)


def create_and_save_pdf(filename, context, request, root, toc):
    """ Create a PDF of the current/all organization(s) and sub-organizations
    with portrait, memberships, and possibly table of contents and save it in
    the organization.

    """
    report = OrganizationsReport(root=root, toc=toc)
    filehandle = report.build(context, request)

    if filename in context:
        context.manage_delObjects([filename])

    context.invokeFactory(type_name='File', id=filename)
    file = context.get(filename)
    file.setContentType('application/pdf')
    file.setExcludeFromNav(True)
    file.setFilename(filename)
    file.setFile(filehandle.getvalue())
    file.reindexObject()


class PdfAtOrganizationView(grok.View):
    """ View to create and store a PDF of the current organization and
    sub-organizations with portrait and memberships. Redirects to the  file if
    it already exists.

    """

    grok.name('pdf')
    grok.context(IOrganization)
    grok.require('zope2.View')

    template = None

    def render(self):
        filename = PDF_EXPORT_FILENAME

        if filename not in self.context or self.request.get('force') == '1':
            log.info(u'creating pdf export of %s' % (self.context.title))

            with unrestricted.run_as('Manager'):
                create_and_save_pdf(
                    filename, self.context, self.request, self.context, False
                )

            log.info(u'pdf export of %s created' % (self.context.title))

        self.response.redirect(filename)


class PdfAtRootView(grok.View):
    """ View to create and store a PDF of all organizations and
    sub-organizations with table of contents, portrait and memberships.
    Redirects to the  file if it already exists.

    """

    grok.name('pdf')
    grok.context(IPloneSiteRoot)
    grok.require('zope2.View')

    template = None

    def render(self):
        filename = PDF_EXPORT_FILENAME

        if filename not in self.context or self.request.get('force') == '1':
            log.info(u'creating full pdf export')

            with unrestricted.run_as('Manager'):
                create_and_save_pdf(
                    filename, self.context, self.request, None, True
                )

            log.info(u'full pdf exported')

        self.response.redirect(filename)


class PdfExportScheduler(object):
    """ Schedules the creation of all PDFs nightly at 0:30.

    """

    _lock = Lock()

    def __init__(self):
        self.next_run = 0
        self.running = False

    def get_next_run(self, now=None):
        if now is None:
            now = datetime.now()

        # Schedule next run tomorrow at 0:30
        at_hours = 0
        at_minutes = 30
        days = 1
        if now.hour < (at_hours + 1) and now.minute < at_minutes:
            days = 0
        next_run = datetime(now.year, now.month, now.day)
        next_run = next_run + timedelta(
            days=days, hours=at_hours, minutes=at_minutes
        )

        return next_run

    @synchronized(_lock)
    def run(self, context, request, force, now=None):

        result = False

        if self.running:
            log.info(u'already exporting')
            return

        if now is None:
            now = datetime.now()

        if not self.next_run:
            self.next_run = self.get_next_run(now)

        if (now > self.next_run) or force:
            self.running = True
            try:
                self.next_run = self.get_next_run(now)
                self.export_single_pdfs(context, request)
                self.export_full_pdf(context, request)
                result = True
            finally:
                self.running = False

        return result

    def export_full_pdf(self, context, request):
        filename = PDF_EXPORT_FILENAME

        log.info('begin exporting full pdf')
        create_and_save_pdf(filename, context, request, None, True)
        log.info('full pdf exported')

    def export_single_pdf(self, context, request):
        filename = PDF_EXPORT_FILENAME

        log.info(u'creating pdf export of %s' % (context.title))
        create_and_save_pdf(filename, context, request, context, False)

        transaction.savepoint(optimistic=True)

        time.sleep(1)

        children = [o.getObject() for o in context.suborganizations()]
        for child in children:
            self.export_single_pdf(child, request)

    def export_single_pdfs(self, context, request):
        catalog = api.portal.get_tool('portal_catalog')
        folder_path = '/'.join(context.getPhysicalPath())
        organizations = catalog(
            path={'query': folder_path, 'depth': 1},
            portal_type='seantis.agencies.organization',
            sort_on='getObjPositionInParent'
        )

        for organization in [o.getObject() for o in organizations]:
            self.export_single_pdf(organization, request)


export_scheduler = PdfExportScheduler()


class PdfExportViewFull(grok.View):
    """ View to invoke the creation of all PDFs nightly
    """

    grok.name('pdfexport-agencies')
    grok.context(IPloneSiteRoot)
    grok.require('zope2.View')

    template = None

    def render(self):
        self.request.response.setHeader("Content-type", "text/plain")

        result = False

        force = self.request.get('force') == '1'
        with unrestricted.run_as('Manager'):
            result = export_scheduler.run(self.context, self.request, force)

        if result:
            return u'PDFs exported'
        else:
            return u'PDFs not exported'
