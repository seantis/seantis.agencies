from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import applyProfile
from plone.app.testing import quickInstallProduct

from plone.testing import z2
from Testing import ZopeTestCase
from zope.configuration import xmlconfig


class TestLayer(PloneSandboxLayer):

    default_bases = (PLONE_FIXTURE,)

    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def setUpZope(self, app, configurationContext):

        # Set up sessioning objects
        app.REQUEST['SESSION'] = self.Session()
        ZopeTestCase.utils.setupCoreSessions(app)

        import seantis.plonetools
        self.loadZCML(package=seantis.plonetools)

        import seantis.agencies
        self.loadZCML(package=seantis.agencies)

        xmlconfig.file(
            'configure.zcml',
            seantis.agencies,
            context=configurationContext
        )

    def setUpPloneSite(self, portal):
        quickInstallProduct(portal, 'seantis.agencies')
        applyProfile(portal, 'seantis.agencies:default')

    def tearDownZope(self, app):
        z2.uninstallProduct(app, 'seantis.agencies')


Layer = TestLayer()


INTEGRATION_TESTING = IntegrationTesting(
    bases=(Layer, ),
    name="Testfixture:Integration"
)

FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(Layer, ),
    name="Testfixture:Functional"
)
