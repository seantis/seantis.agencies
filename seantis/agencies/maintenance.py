from five import grok
from zope.app.component.hooks import getSite

from seantis.plonetools import async
from seantis.agencies.interfaces import IActivityEvent


@grok.subscribe(IActivityEvent)
def on_resource_viewed(event):
    async.register('/%s/pdfexport-agencies?run=1' % getSite().id, 60 * 60)
