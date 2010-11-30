from Products.CMFCore.utils import getToolByName
from convert import convert
from zope.component import getUtility
from settings import Settings

try:
    from plone.app.async.interfaces import IAsyncService
    async_installed = True
except:
    async_installed = False

def handle_file_creation(object, event):
    if object.getContentType() not in ('application/pdf', 'application/x-pdf', 'image/pdf'):
        return
    
    ptool = getToolByName(object, 'portal_properties')
    site_props = getattr(ptool, 'site_properties', None)
    auto_layout = site_props.getProperty('page_turner_auto_select_layout', False)
    
    if auto_layout:
        object.setLayout('page-turner')
        
    if async_installed:
        settings = Settings(object)
        async = getUtility(IAsyncService)
        job = async.queueJob(convert, object)
        settings.converting = True
    else:
        convert(object)