from five import grok

from seantis.plonetools.browser import BaseView as SharedBaseView
from seantis.plonetools.browser import BaseForm as SharedBaseForm

from seantis.agencies.interfaces import ISeantisAgenciesSpecific


class BaseView(SharedBaseView):

    grok.baseclass()
    grok.layer(ISeantisAgenciesSpecific)

    domain = 'seantis.agencies'


class BaseForm(SharedBaseForm):

    grok.baseclass()
    grok.layer(ISeantisAgenciesSpecific)

    domain = 'seantis.agencies'
