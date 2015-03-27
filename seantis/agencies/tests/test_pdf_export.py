import mock
import os

from datetime import datetime, timedelta
from zExceptions import NotFound

from seantis.agencies import tests


class TestPdfExport(tests.BrowserTestCase):

    def setUp(self):
        super(TestPdfExport, self).setUp()

        browser = self.admin_browser

        browser.open(self.baseurl + '/++add++seantis.agencies.organization')

        browser.getControl(name='form.widgets.title').value = 'organizations'
        browser.getControl('Save').click()
        self.orgs_url = self.baseurl + '/organizations'

        browser.open(self.baseurl + '/++add++seantis.people.list')
        browser.getControl('Name of the list of people').value = 'list'
        browser.getControl('Save').click()
        self.list_url = self.baseurl + '/list'

    def tearDown(self):
        self.admin_browser.open(self.orgs_url + '/delete_confirmation')
        self.admin_browser.getControl('Delete').click()

        self.admin_browser.open(self.list_url + '/delete_confirmation')
        self.admin_browser.getControl('Delete').click()

        super(TestPdfExport, self).tearDown()

    @mock.patch('kantonzugpdf.ReportZug.get_logo')
    def test_export_pdfs_unscheduled(self, get_logo):
        get_logo.return_value = None
        browser = self.new_browser()

        browser.open('/pdfexport-agencies')
        self.assertEquals(browser.contents, u'PDFs not exported')

    @mock.patch('kantonzugpdf.ReportZug.get_logo')
    def test_export_pdfs_empty(self, get_logo):
        get_logo.return_value = None
        browser = self.new_browser()

        browser.open('/pdfexport-agencies?force=1')
        self.assertEquals(browser.contents, u'PDFs exported')
        browser.open('/exported_pdf.pdf')
        self.assertEquals(browser.headers['Content-Type'], 'application/pdf')
        self.assertNotEquals(browser.contents, '')

    @mock.patch('kantonzugpdf.ReportZug.get_logo')
    def test_export_pdf(self, get_logo):
        get_logo.return_value = None

        self.add_organization(title='a', portrait='portrait')
        self.add_organization(title='b', path='/a')
        self.add_organization(title='c', path='/a/b')
        self.add_organization(title='d', path='/a/b/c')
        self.add_organization(title='e', path='/a/b/c/d')
        self.add_organization(title='f', path='/a/b/c/d/e')
        self.add_organization(title='g', path='/a/b/c/d/e/f')
        self.add_organization(title='h', path='/a/b/c/d/e/f/g')

        browser = self.new_browser()
        browser.open('/pdfexport-agencies?force=1')
        self.assertEquals(browser.contents, u'PDFs exported')
        browser.open('/exported_pdf.pdf')
        self.assertEquals(browser.headers['Content-Type'], 'application/pdf')
        self.assertNotEquals(browser.contents, '')

    def test_scheduler_next_run(self):
        from seantis.agencies.browser.pdfexport import export_scheduler

        real_now = datetime.today()
        today = datetime(real_now.year, real_now.month, real_now.day)
        tomorrow = today + timedelta(days=1)

        next_run = export_scheduler.get_next_run(today)
        self.assertEqual(next_run, today + timedelta(minutes=30))

        now = today + timedelta(minutes=10)
        next_run = export_scheduler.get_next_run(now)
        self.assertEqual(next_run, today + timedelta(minutes=30))

        now = today + timedelta(minutes=29)
        next_run = export_scheduler.get_next_run(now)
        self.assertEqual(next_run, today + timedelta(minutes=30))

        now = today + timedelta(minutes=30)
        next_run = export_scheduler.get_next_run(now)
        self.assertEqual(next_run, tomorrow + timedelta(minutes=30))

        now = today + timedelta(hours=1, minutes=30)
        next_run = export_scheduler.get_next_run(now)
        self.assertEqual(next_run, tomorrow + timedelta(minutes=30))

        now = today + timedelta(hours=4)
        next_run = export_scheduler.get_next_run(now)
        self.assertEqual(next_run, tomorrow + timedelta(minutes=30))

        now = today + timedelta(hours=12)
        next_run = export_scheduler.get_next_run(now)
        self.assertEqual(next_run, tomorrow + timedelta(minutes=30))

    @mock.patch('kantonzugpdf.ReportZug.get_logo')
    def test_view_single_pdfs(self, get_logo):
        get_logo.return_value = None

        self.add_organization(title='a', portrait='portrait')
        self.add_organization(title='b', path='/a')
        self.add_organization(title='c', path='/a/b')
        self.add_organization(title='d', path='/a/b/c')
        self.add_organization(title='e', path='/a/b/c/d')
        self.add_organization(title='f', path='/a/b/c/d/e')
        self.add_organization(title='g', path='/a/b/c/d/e/f')
        self.add_organization(title='h', path='/a/b/c/d/e/f/g')

        browser = self.new_browser()

        for org in ['a', 'a/b', 'a/b/c', 'a/b/c/d', 'a/b/c/d/e',
                    'a/b/c/d/e/f', 'a/b/c/d/e/f/g']:
            self.assertRaises(NotFound, browser.open,
                              '/organizations/%s/exported_pdf.pdf' % org)

        browser.open('/organizations/a/b/c/d/e/f/g/pdf')
        browser.open('/organizations/a/b/c/d/e/f/g/exported_pdf.pdf')

        for org in ['a', 'a/b', 'a/b/c', 'a/b/c/d', 'a/b/c/d/e',
                    'a/b/c/d/e/f']:
            self.assertRaises(NotFound, browser.open,
                              '/organizations/%s/exported_pdf.pdf' % org)

        for org in ['a', 'a/b', 'a/b/c', 'a/b/c/d', 'a/b/c/d/e',
                    'a/b/c/d/e/f']:
            browser.open('/organizations/%s/pdf' % org)
            browser.open('/organizations/%s/exported_pdf.pdf' % org)

    @mock.patch('kantonzugpdf.ReportZug.get_logo')
    def test_view_full_pdf(self, get_logo):
        get_logo.return_value = None

        self.add_organization(title='a', portrait='portrait')
        self.add_organization(title='b', path='/a')
        self.add_organization(title='c', path='/a/b')
        self.add_organization(title='d', path='/a/b/c')
        self.add_organization(title='e', path='/a/b/c/d')
        self.add_organization(title='f', path='/a/b/c/d/e')
        self.add_organization(title='g', path='/a/b/c/d/e/f')
        self.add_organization(title='h', path='/a/b/c/d/e/f/g')

        browser = self.new_browser()

        self.assertRaises(NotFound, browser.open, '/exported_pdf.pdf')

        browser.open('/pdf')
        browser.open('/exported_pdf.pdf')
