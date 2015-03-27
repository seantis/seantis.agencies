from zope.interface import Interface


class ISeantisAgenciesSpecific(Interface):
    """ Browser Layer for seantis.agencies. """


class IActivityEvent(Interface):
    """ Event triggered when a seantis.agencies.organization resource
    is first viewed."""
