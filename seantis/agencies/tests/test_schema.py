from seantis.agencies import tests
from zope.schema import getFields


class TestSchema(tests.IntegrationTestCase):

    def test_schema_load(self):
        from seantis.agencies.types import IMember, IMembership, IOrganization
        getFields(IMember)
        getFields(IMembership)
        getFields(IOrganization)
