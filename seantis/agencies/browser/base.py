from five import grok
from seantis.agencies.interfaces import ISeantisAgenciesSpecific
from seantis.plonetools.browser import BaseForm as SharedBaseForm
from seantis.plonetools.browser import BaseView as SharedBaseView


class BaseView(SharedBaseView):

    grok.baseclass()
    grok.layer(ISeantisAgenciesSpecific)

    domain = 'seantis.agencies'


class BaseForm(SharedBaseForm):

    grok.baseclass()
    grok.layer(ISeantisAgenciesSpecific)

    domain = 'seantis.agencies'
