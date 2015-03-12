from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from plone import api

from seantis.agencies.types import IMembership


def on_organization_modified(context, event=None):
    """ Listens to IObjectModifiedEvent events of organization and triggers
    reindexing for containing memberships.

    """
    catalog = api.portal.get_tool('portal_catalog')
    memberships = catalog(
        object_provides=IMembership.__identifier__,
        path={'query': '/'.join(context.getPhysicalPath()), 'depth': 1}
    )
    for membership in memberships:
        notify(ObjectModifiedEvent(membership.getObject()))
