from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interface.file import IFileContent

def uninstall(context):
    
    if not context.readDataFile('wc.pageturner-uninstall.txt'):
        return
        
    portal = context.getSite()
    portal_actions = getToolByName(portal, 'portal_actions')
    object_buttons = portal_actions.object

    actions_to_remove = ('pageturner_settings')
    for action in actions_to_remove:
        if action in object_buttons.objectIds():
            object_buttons.manage_delObjects([action])
    
    
    catalog = getToolByName(portal, 'portal_catalog')
    objs = catalog(object_provides=IFileContent.__identifier__)
    
    for obj in objs:
        obj = obj.getObject()
        obj.layout = ''
        
    types = getToolByName(portal, 'portal_types')
    filetype = types['File']
    methods = list(filetype.view_methods)
    methods = methods.remove('page-turner')
    filetype.view_methods = tuple(methods)