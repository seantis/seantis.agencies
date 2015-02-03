import xlrd

from copy import deepcopy
from datetime import date, timedelta
from plone import api
from StringIO import StringIO
from xlwt import Workbook
from zExceptions import Unauthorized

from seantis.agencies import tests
from seantis.agencies.browser.xlsexport import TITLES_ORGANIZATION
from seantis.agencies.browser.xlsexport import TITLES_REGISTER
from seantis.plonetools import tools


class TestImportExport(tests.BrowserTestCase):

    def setUp(self):
        super(TestImportExport, self).setUp()
        self.organizations = [
            [u'0', u'1,2', u'Organizations', u'des_0', u'port_0'],
            [u'1', u'', u'org_1', u'des_1', u'port_1'],
            [u'2', u'3', u'org_2', u'des_2', u'port_2'],
            [u'3', u'', u'org_3', u'des_3', u'port_3']
        ]
        self.people = [
            [str(prefix) + '_' + field for field in TITLES_REGISTER]
            for prefix in range(3)
        ]
        self.people[0][-1] = u'(0)(role)(2006)(*)(3)//'
        self.people[1][-1] = u'(1)()()()(7)// (0)()()()(2)//(3)()()()(7)'
        self.people[2][-1] = u'(2)(role)()(2000)(2)//(3)()(*)()(8)'

    def create_test_workbook(self, filehandle, organizations=None,
                             people=None):
        if organizations is None:
            organizations = self.organizations
        if people is None:
            people = self.people

        book = Workbook(encoding='utf-8')
        sheet = book.add_sheet(u'Organizations')
        for index, cell in enumerate(TITLES_ORGANIZATION):
            sheet.row(0).write(index, cell)
        for row, organization in enumerate(organizations):
            for index, cell in enumerate(organization):
                sheet.row(row+1).write(index, cell)
        sheet = book.add_sheet(u'People')
        for index, cell in enumerate(TITLES_REGISTER):
            sheet.row(0).write(index, cell)
        for row, organization in enumerate(people):
            for index, cell in enumerate(organization):
                sheet.row(row+1).write(index, cell)
        book.save(filehandle)

    def test_access(self):
        browser = self.new_browser()
        self.assertRaises(Unauthorized, browser.open, '/export-agencies')
        self.assertRaises(Unauthorized, browser.open, '/import-agencies')

    def test_export_empty(self):
        browser = self.new_admin_browser()
        browser.open('/export-agencies')
        self.assertEquals(browser.contents, '')
        self.assertEquals(browser.headers['Content-disposition'], 'export.xls')
        self.assertEquals(browser.headers['Content-Type'], 'application/xls')
        self.assertEquals(browser.headers['Content-Length'], '0')

    def test_import_export(self):
        filehandle = StringIO()
        self.create_test_workbook(filehandle)
        xls_file = filehandle.getvalue()
        filehandle.close()

        # import
        browser = self.new_admin_browser()
        browser.open('/import-agencies')
        widget = browser.getControl(name='form.widgets.xls_file')
        widget.add_file(xls_file, 'application/xls', 'import.xls')
        browser.getControl('Import').click()

        # export
        browser.open('/export-agencies')
        self.assertEquals(browser.headers['Content-disposition'], 'export.xls')
        self.assertEquals(browser.headers['Content-Type'], 'application/xls')
        self.assertTrue(int(browser.headers['Content-Length']) > 0)

        # compare
        workbook = xlrd.open_workbook(file_contents=browser.contents)
        sheets = workbook.sheets()
        self.assertEquals(len(sheets), 2)
        self.assertEquals(sheets[0].name, u'Organizations')
        self.assertEquals(sheets[0].ncols, len(TITLES_ORGANIZATION))
        self.assertEquals(sheets[0].nrows, 5)
        for row, content in enumerate(self.organizations):
            self.assertEquals([cell.value for cell in sheets[0].row(row+1)],
                              content)

        self.assertEquals(sheets[1].name, u'People')
        self.assertEquals(sheets[1].ncols, len(TITLES_REGISTER))
        self.assertEquals(sheets[1].nrows, 4)
        for row, content in enumerate(self.people):
            self.assertEquals(
                [cell.value for cell in sheets[1].row(row+1)[:-1]],
                content[:-1]
            )

        # roles are slightly different: position starts at zero, order is
        # random
        self.assertEquals(u'(0)(role)(2006)(*)(1)',
                          sheets[1].cell(1, -1).value)
        self.assertTrue(u'(1)()()()(0)', sheets[1].cell(2, -1).value)
        self.assertTrue(u'(3)()()()(0)', sheets[1].cell(2, -1).value)
        self.assertTrue(u'(0)()()()(0)', sheets[1].cell(2, -1).value)
        self.assertTrue(u'(2)(role)()()(0)', sheets[1].cell(3, -1).value)
        self.assertTrue(u'(3)()()(*)(1)', sheets[1].cell(3, -1).value)

        # browse imported items
        browser.open('/organizations')
        self.assertIn('des_0', browser.contents)
        self.assertIn('port_0', browser.contents)
        self.assertIn('org_1', browser.contents)
        self.assertIn('org_2', browser.contents)
        self.assertNotIn('org_3', browser.contents)

        browser.open('/organizations/org_1')
        self.assertIn('des_1', browser.contents)
        self.assertIn('port_1', browser.contents)
        self.assertNotIn('org_2', browser.contents)
        self.assertNotIn('org_3', browser.contents)

        browser.open('/organizations/org_2')
        self.assertIn('des_2', browser.contents)
        self.assertIn('port_2', browser.contents)
        self.assertNotIn('org_1', browser.contents)
        self.assertIn('org_3', browser.contents)

        browser.open('/organizations/org_2/org_3')
        self.assertIn('des_3', browser.contents)
        self.assertIn('port_3', browser.contents)

    def test_import_errors(self):
        browser = self.new_admin_browser()

        # missing file
        browser.open('/import-agencies')
        browser.getControl('Import').click()
        self.assertIn('Required input is missing', browser.contents)

        # invalid file
        browser.open('/import-agencies')
        widget = browser.getControl(name='form.widgets.xls_file')
        widget.add_file('stuff', 'application/xls', 'import.xls')
        browser.getControl('Import').click()
        self.assertIn('Invalid XLS file', browser.contents)

        # error in register sheet
        people = deepcopy(self.people)
        people[1][-1] = u'(1))()()(7)// (0aa()()(2)//(3)()()()(7)//'
        filehandle = StringIO()
        self.create_test_workbook(filehandle, people=people)
        xls_file = filehandle.getvalue()
        filehandle.close()

        browser.open('/import-agencies')
        widget = browser.getControl(name='form.widgets.xls_file')
        widget.add_file(xls_file, 'application/xls', 'import.xls')
        browser.getControl('Import').click()

        self.assertIn('Invalid row 2 in sheet People', browser.contents)

        # error in organization sheet
        organizations = deepcopy(self.organizations)
        organizations[0][2] = u'Urganizations'
        organizations[2][0] = u'1'
        filehandle = StringIO()
        self.create_test_workbook(filehandle, organizations=organizations)
        xls_file = filehandle.getvalue()
        filehandle.close()

        browser.open('/import-agencies')
        widget = browser.getControl(name='form.widgets.xls_file')
        widget.add_file(xls_file, 'application/xls', 'import.xls')
        browser.getControl('Import').click()
        self.assertIn('Top level organizations not found', browser.contents)
        self.assertIn('Invalid row 3 in sheet Organizations', browser.contents)
