from Products.CMFCore.utils import getToolByName


def migrateTo10b1(context):
    properties_tool = getToolByName(context, 'portal_properties', None)
    if properties_tool is not None:
        site_props = getattr(properties_tool, 'site_properties', None)
        if not site_props.hasProperty('page_turner_auto_select_layout'):
            site_props.manage_addProperty('page_turner_auto_select_layout', True, 'boolean')
            site_props.manage_changeProperties(page_turner_auto_select_layout=True)