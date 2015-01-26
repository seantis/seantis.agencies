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

    def new_admin_browser(self):
        browser = self.new_browser()
        browser.login_admin()

        return browser

    def add_organization(self, title='organization', portrait='', path=''):
        browser = self.admin_browser

        url = self.orgs_url + path + '/++add++seantis.agencies.organization'
        browser.open(url)
        browser.getControl('Title').value = title
        browser.getControl('Portrait').value = portrait
        browser.getControl('Save').click()
