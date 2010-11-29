from Products.CMFCore.utils import getToolByName

def handle_file_creation(object, event):
    ptool = getToolByName(object, 'portal_properties')
    site_props = getattr(ptool, 'site_properties', None)
    
    if not site_props:
        return
        
    auto_layout = site_props.getProperty('page_turner_auto_select_layout', False)
    
    if auto_layout and object.getContentType() in ('application/pdf', 'application/x-pdf', 'image/pdf'):
        object.setLayout('page-turner')