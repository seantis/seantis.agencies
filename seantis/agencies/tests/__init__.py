from plone import api

from zope.security.management import newInteraction, endInteraction

from seantis.plonetools.testing import TestCase
from seantis.agencies.testing import (
    INTEGRATION_TESTING,
    FUNCTIONAL_TESTING
)


# to use with integration where security interactions need to be done manually
class IntegrationTestCase(TestCase):
    layer = INTEGRATION_TESTING

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        newInteraction()

    def tearDown(self):
        endInteraction()
        super(IntegrationTestCase, self).tearDown()


# to use with the browser which does its own security interactions
class FunctionalTestCase(TestCase):
    layer = FUNCTIONAL_TESTING


class BrowserTestCase(FunctionalTestCase):

    def setUp(self):
        super(BrowserTestCase, self).setUp()
        self.baseurl = self.portal.absolute_url()
        self.admin_browser = browser = self.new_admin_browser()

        browser.open(self.baseurl + '/createObject?type_name=Folder')
        browser.getControl('Title').value = 'testfolder'
        browser.getControl('Save').click()

        self.folder_url = self.baseurl + '/testfolder'
        self.infolder = lambda url: self.folder_url + url

    def tearDown(self):
        self.admin_browser.open(self.infolder('/delete_confirmation'))
        self.admin_browser.getControl('Delete').click()

        super(BrowserTestCase, self).tearDown()

    def new_admin_browser(self):
        browser = self.new_browser()
        browser.login_admin()

        return browser
