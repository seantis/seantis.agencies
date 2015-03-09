from five import grok
from zope.component.hooks import getSite

from seantis.plonetools import async
from seantis.agencies.interfaces import IActivityEvent


@grok.subscribe(IActivityEvent)
def on_resource_viewed(event):
    async.register('/%s/pdfexport-agencies' % getSite().id, 60 * 60)
