import mock

from seantis.agencies import tests


class TestPdfExport(tests.BrowserTestCase):

    @mock.patch('kantonzugpdf.ReportZug.get_logo')
    def test_export_pdf_empty(self, get_logo):
        get_logo.return_value = None
        browser = self.new_browser()
        browser.open('/pdfexport-agencies')

        self.assertNotEquals(browser.contents, '')
        self.assertEquals(browser.headers['Content-Type'], 'application/pdf')
        self.assertEquals(browser.headers['Content-disposition'],
                          'filename="Organizations.pdf"')
