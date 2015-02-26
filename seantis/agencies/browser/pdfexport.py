import logging
log = logging.getLogger('seantis.agencies')

import os
import codecs
import re
import tempfile

from datetime import datetime, date
from io import BytesIO
from pdfdocument.document import MarkupParagraph
from reportlab.lib.units import cm

from five import grok
from plone import api
from Products.CMFPlone.interfaces import IPloneSiteRoot
from zExceptions import NotFound
from zope.interface import Interface

from kantonzugpdf import ReportZug
from kantonzugpdf.report import PDF

from seantis.agencies import _
from seantis.agencies.types import IOrganization
from seantis.plonetools import tools


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
                text = ''
                name = ''
                person = membership.person.to_object
                if person:
                    name = person.title
                    fields = ['title', 'year', 'academic_title', 'occupation',
                              'address', 'political_party']
                    text = ', '.join([
                        getattr(person, field) for field in fields
                        if getattr(person, field)
                    ])

                memberships.append((
                    membership.role, membership.prefix, text, name
                ))

            if organization.display_alphabetically:
                memberships = sorted(memberships, key=lambda m: m[3])

            table_data = []
            for membership in memberships:
                table_data.append([
                    MarkupParagraph(membership[0], self.pdf.style.normal),
                    MarkupParagraph(membership[1], self.pdf.style.normal),
                    MarkupParagraph(membership[2], self.pdf.style.normal),
                ])

            table_columns = [4.3*cm, 0.5*cm, 11*cm]
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

        for idx, child in enumerate(children):
            self.populate_organization(child, level+1, idx == len(children)-1)


class PdfExportViewFull(grok.View):

    grok.name('pdfexport-agencies')
    grok.context(IPloneSiteRoot)
    grok.require('zope2.View')

    template = None

    def render(self):
        filehandle = OrganizationsReport().build(self.context, self.request)

        filename = _(u'Organizations')
        filename = codecs.utf_8_encode('filename="%s.pdf"' % filename)[0]
        self.request.RESPONSE.setHeader('Content-disposition', filename)
        self.request.RESPONSE.setHeader('Content-Type', 'application/pdf')

        response = filehandle.getvalue()
        filehandle.seek(0, os.SEEK_END)

        filesize = filehandle.tell()
        filehandle.close()

        self.request.RESPONSE.setHeader('Content-Length', filesize)

        return response


class PdfExportView(grok.View):

    grok.name('pdfexport')
    grok.context(IOrganization)
    grok.require('zope2.View')

    template = None

    def render(self):
        report = OrganizationsReport(root=self.context)
        filehandle = report.build(self.context, self.request)

        filename = self.context.title
        filename = codecs.utf_8_encode('filename="%s.pdf"' % filename)[0]
        self.request.RESPONSE.setHeader('Content-disposition', filename)
        self.request.RESPONSE.setHeader('Content-Type', 'application/pdf')

        response = filehandle.getvalue()
        filehandle.seek(0, os.SEEK_END)

        filesize = filehandle.tell()
        filehandle.close()

        self.request.RESPONSE.setHeader('Content-Length', filesize)

        return response
