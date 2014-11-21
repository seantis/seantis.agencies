from zope.schema import getFields

from seantis.agencies import tests


class TestSchema(tests.IntegrationTestCase):

    def test_schema_load(self):
        from seantis.agencies.types import IMember, IMembership, IOrganization
        getFields(IMember)
        getFields(IMembership)
        getFields(IOrganization)
