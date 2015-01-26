import mock

from seantis.agencies import tests


class TestPdfExport(tests.BrowserTestCase):

    def setUp(self):
        super(TestPdfExport, self).setUp()

        browser = self.admin_browser

        browser.open(self.baseurl + '/++add++seantis.agencies.organization')
        browser.getControl('Title').value = 'organizations'
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
    def test_export_pdf_empty(self, get_logo):
        get_logo.return_value = None
        browser = self.new_browser()
        browser.open('/pdfexport-agencies')

        self.assertNotEquals(browser.contents, '')
        self.assertEquals(browser.headers['Content-Type'], 'application/pdf')
        self.assertEquals(browser.headers['Content-disposition'],
                          'filename="Organizations.pdf"')

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
        browser.open('/pdfexport-agencies')

        self.assertNotEquals(browser.contents, '')
        self.assertEquals(browser.headers['Content-Type'], 'application/pdf')
        self.assertEquals(browser.headers['Content-disposition'],
                          'filename="Organizations.pdf"')
