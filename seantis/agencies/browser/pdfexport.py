# coding=utf-8

import logging
log = logging.getLogger('seantis.agencies')

import time
import transaction

from datetime import datetime, date, timedelta
from five import grok
from io import BytesIO
from kantonzugpdf import ReportZug
from kantonzugpdf.report import PDF
from pdfdocument.document import MarkupParagraph
from plone import api
from plone.protect import createToken
from plone.synchronize import synchronized
from Products.CMFPlone.interfaces import IPloneSiteRoot
from reportlab.lib.units import cm
from seantis.agencies import _
from seantis.agencies.types import IOrganization
from seantis.plonetools import tools, unrestricted
from threading import Lock


PDF_EXPORT_FILENAME = u'exported_pdf.pdf'


def fetch_organisation(organization, level=0):
    """ Returns the export data of an organisation with all its
    sub-organizations.

    """
    data = {
        'title': organization.title if level else '',
        'portrait': '',
        'memberships': [],
        'children': [],
        'context': organization
    }

    if organization.portrait:
        data['portrait'] = organization.portal_transforms.convertTo(
            'text/x-html-safe',
            organization.portrait,
            context=organization,
            encoding='utf8'
        ).getData()

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
            text_fields = []
            for field in fields:
                if getattr(person, field, None):
                    text_fields.append(getattr(person, field, ''))
                if getattr(membership, field, None):
                    if field == 'role' or field == 'title':
                        continue
                    text_fields.append(getattr(membership, field, ''))
            text = ', '.join(text_fields)

        memberships.append((role, membership.prefix, text, name))

    if organization.display_alphabetically:
        sortkey = lambda m: tools.unicode_collate_sortkey()(m[3])
        memberships = sorted(memberships, key=sortkey)

    for membership in memberships:
        data['memberships'].append(membership[:3])

    children = [o.getObject() for o in organization.suborganizations()]

    for idx, child in enumerate(children):
        data['children'].append(
            fetch_organisation(child, level + 1)
        )

    return data


def fetch_organisations(context):
    """ Returns the export data of all organisations with all its
    sub-organizations within the context.

    """

    catalog = api.portal.get_tool('portal_catalog')
    folder_path = '/'.join(context.getPhysicalPath())
    organizations = catalog(
        path={'query': folder_path, 'depth': 1},
        portal_type='seantis.agencies.organization',
        sort_on='getObjPositionInParent',
    )

    data = []
    for organization in [o.getObject() for o in organizations]:
        data.append(fetch_organisation(organization))

    return data


class OrganizationsPdf(PDF):
    """ Extends kantonzugpdf.report.PDF with additional headings. """

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

    def __init__(self, data, title, translator, toc=True):
        self.data = data
        self.title = title
        self.translator = translator
        self.toc = toc
        self.file = BytesIO()
        self.pdf = OrganizationsPdf(self.file)
        self.pdf.init_report(
            page_fn=self.first_page, page_fn_later=self.later_page
        )
        if not toc:
            self.pdf.toc_numbering = None

    def translate(self, text):
        return self.translator(text)

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
        self.adjust_style()

        # First page contains the title and table of contents
        self.pdf.h(self.title)
        if self.toc:
            self.pdf.table_of_contents()
            self.pdf.pagebreak()

        # Iterate recursive over organizations
        for organization in self.data:
            self.populate_organization(organization)

    def populate_organization(self, organization, level=0,
                              block_had_content=False):

        break_page = (level > 0 and level < 4)
        if break_page:
            if not block_had_content:
                break_page = False

        if break_page:
            self.pdf.pagebreak()
        else:
            self.pdf.spacer()

        has_content = False
        if level:
            # Title
            if level == 1:
                self.pdf.h1(organization['title'])
            elif level == 2:
                self.pdf.h2(organization['title'])
            elif level == 3:
                self.pdf.h3(organization['title'])
            elif level == 4:
                self.pdf.h4(organization['title'])
            elif level == 5:
                self.pdf.h5(organization['title'])
            elif level == 6:
                self.pdf.h6(organization['title'])
            else:
                self.pdf.p_markup(organization['title'],
                                  self.pdf.style.heading6)

        # Portrait
        if organization['portrait']:
            has_content = True
            self.pdf.spacer()
            try:
                self.pdf.styled_paragraph(organization['portrait'])
            except ValueError:
                # the portrait might have some unprocessable html code
                self.pdf.p(organization['portrait'])
                log.warn('%s contains invalid markup' % organization['title'])

        image = organization['context'].organigram
        if image:
            self.pdf.spacer()
            self.pdf.image(
                '{}/@@images/organigram'.format(
                    organization['context'].absolute_url(),
                ),
                1.0 * image._width / image._height
            )
            self.pdf.spacer()

        table_data = []
        for membership in organization['memberships']:
            table_data.append([
                MarkupParagraph(membership[0], self.pdf.style.normal),
                MarkupParagraph(membership[1], self.pdf.style.normal),
                MarkupParagraph(membership[2], self.pdf.style.normal),
            ])

        table_columns = [5.5 * cm, 0.5 * cm, 9.7 * cm]
        if table_data:
            has_content = True
            self.pdf.spacer()
            self.pdf.table(table_data, table_columns)

        time.sleep(0)

        for idx, child in enumerate(organization['children']):
            child_has_content = self.populate_organization(
                child, level + 1, has_content
            )
            has_content = has_content or child_has_content

        return has_content


def create_and_save_pdf(data, filename, context, request, toc):
    """ Create a PDF of the current/all organization(s) and sub-organizations
    with portrait, memberships, and possibly table of contents and save it in
    the organization.

    """
    translator = tools.translator(request, 'seantis.agencies')
    report = OrganizationsReport(data, context.title, translator, toc=toc)
    filehandle = report.build(context, request)

    with unrestricted.run_as('Manager'):
        request.set('_authenticator', createToken())
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

            data = fetch_organisation(self.context)
            create_and_save_pdf(
                [data], filename, self.context, self.request, False
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

            data = fetch_organisations(self.context)
            create_and_save_pdf(
                data, filename, self.context, self.request, True
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
                log.info(u'fetching export data')
                data = fetch_organisations(context)
                for organization in data:
                    self.export_single_pdf(
                        organization, organization['context'], request
                    )
                self.export_full_pdf(data, context, request)
                result = True
            finally:
                self.running = False
                log.info(u'export data finished')

        return result

    def export_full_pdf(self, data, context, request):
        filename = PDF_EXPORT_FILENAME

        log.info('begin exporting full pdf')
        create_and_save_pdf(data, filename, context, request, True)
        log.info('full pdf exported')

    def export_single_pdf(self, data, context, request):
        filename = PDF_EXPORT_FILENAME

        log.info(u'creating pdf export of %s' % (context.title))
        create_and_save_pdf([data], filename, context, request, False)

        transaction.savepoint(optimistic=True)

        time.sleep(1)

        for child in data['children']:
            self.export_single_pdf(child, child['context'], request)


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
        result = export_scheduler.run(self.context, self.request, force)

        if result:
            return u'PDFs exported'
        else:
            return u'PDFs not exported'
