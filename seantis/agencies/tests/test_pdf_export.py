from seantis.agencies import tests


class TestPdfExport(tests.BrowserTestCase):

    def test_export_pdf_empty(self):
        browser = self.new_browser()
        browser.open('/pdfexport-agencies')

        self.assertNotEquals(browser.contents, '')
        self.assertEquals(browser.headers['Content-Type'], 'application/pdf')
        self.assertEquals(browser.headers['Content-disposition'],
                          'filename="Organizations.pdf"')
