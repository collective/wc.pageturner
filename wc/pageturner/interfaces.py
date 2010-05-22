from zope.interface import Interface
from wc.pageturner import mf as _
from zope import schema

class Layer(Interface):
    """
    layer class
    """
    
class IPageTurnerSettings(Interface):
    
    
    width = schema.Int(
        title=_(u'label_width_title_pageturner', default=u"Width"),
        description=_(u"label_width_description_pageturn", 
            default=u"The fixed width of the Page Viewer."),
        default=600,
        required=True
    )
    
    height = schema.Int(
        title=_(u'label_height_title_pageturner', default=u"Height"),
        description=_(u"label_height_description_pageturner", 
            default=u"The fixed height of the Page Viewer."),
        default=500,
        required=True
    )
    
class IUtils(Interface):
    
    def enabled():
        pass