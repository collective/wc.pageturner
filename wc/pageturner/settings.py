from zope.interface import implements
from persistent.dict import PersistentDict
from zope.annotation.interfaces import IAnnotations
from interfaces import IPageTurnerSettings
from DateTime import DateTime

class Settings(object):
    implements(IPageTurnerSettings)
    
    def __init__(self, context):
        self.context = context
        annotations = IAnnotations(self.context)

        self._metadata = annotations.get('wc.pageturner', None)
        if self._metadata is None:
            self._metadata = PersistentDict()
            self._metadata['last_updated'] = DateTime('1901/01/01').pCommonZ()
            annotations['wc.pageturner'] = self._metadata
                    
    def __setattr__(self, name, value):
        if name[0] == '_' or name == 'context':
            self.__dict__[name] = value
        else:
            self._metadata[name] = value

    def __getattr__(self, name):
        default = None
        if name in IPageTurnerSettings.names():
            default = IPageTurnerSettings[name].default

        return self._metadata.get(name, default)
