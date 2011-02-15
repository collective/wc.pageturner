from Products.Five.browser import BrowserView
from plone.app.form import base as ploneformbase
from zope.interface import implements
from zope.formlib import form
from webdav.common import rfc1123_date
from Products.Archetypes.utils import contentDispositionHeader
from os import fstat
from Products.CMFCore.utils import getToolByName
from interfaces import IPageTurnerSettings, IUtils
from wc.pageturner import mf as _
from settings import Settings
from Products.ATContentTypes.interface.file import IFileContent
import zope.event, zope.lifecycleevent
from zope.component import getMultiAdapter
from convert import pdf2swf, converted_field

from logging import getLogger
logger = getLogger('wc.pageturner')

try:
    import plone.app.blob
    from plone.app.blob.download import handleRequestRange
    from plone.app.blob.iterators import BlobStreamIterator
    from plone.app.blob.utils import openBlob
    from ZODB.blob import Blob
    has_pab = True
except:
    has_pab = False
    
    
class PageTurnerView(BrowserView):

    installed = pdf2swf is not None
    pab_installed = has_pab
    enabled = pdf2swf is not None
        
    def __call__(self):
        self.settings = Settings(self.context)
        utils = getToolByName(self.context, 'plone_utils')
        msg = None
        
        if self.context.getContentType() in ('application/pdf', 'application/x-pdf', 'image/pdf'):
            if not self.installed:
                msg = "Since you do not have swftools installed on this system, we can not render the pages of this PDF."
            elif self.settings.converting is not None and self.settings.converting:
                msg = "The PDF is currently being converted to the FlexPaper view..."
                self.enabled = False
            elif not self.settings.successfully_converted:
                msg = "There was an error trying to convert the PDF. Maybe the PDF is encrypted, corrupt or malformed?"
                self.enabled = False
        else:
            self.enabled = False
            msg = "The file is not a PDF. No need for this view."
            
        if msg:
            mtool=getToolByName(self.context, 'portal_membership')
            if mtool.checkPermission('cmf.ModifyPortalContent', self.context):
                utils.addPortalMessage(msg)
            
        return self.index()

    def javascript(self):
        return """
jq(document).ready(function(){
  var swfVersionStr = "10.0.0";
  var xiSwfUrlStr = "%(context_url)s/++resource++pageturner.resources/expressinstall.swf";
    
  var flashvars = { 
    SwfFile : escape("%(context_url)s/converted.swf"),
    Scale : 0.6, 
    ZoomTransition : "easeOut",
    ZoomTime : 0.5,
    ZoomInterval : 0.1,
    FitPageOnLoad : false,
    FitWidthOnLoad : true,
    PrintEnabled : %(print_enabled)s,
    FullScreenAsMaxWindow : false,
    PrintToolsVisible : true,
    ViewModeToolsVisible : true,
    ZoomToolsVisible : true,
    FullScreenVisible : %(full_screen_visible)s,
    NavToolsVisible : true,
    CursorToolsVisible : %(cursor_tools_visible)s,
    SearchToolsVisible : %(search_tools_visible)s,
    ProgressiveLoading : %(progressive_loading)s,
    localeChain: "en_US"
  };
	  
  var params = {};
  params.quality = "high";
  params.bgcolor = "#ffffff";
  params.allowscriptaccess = "sameDomain";
  params.allowfullscreen = "true";
  params.wmode = "transparent";
  var attributes = {};
  attributes.id = "FlexPaperViewer";
  attributes.name = "FlexPaperViewer";
  swfobject.embedSWF(
    "%(context_url)s/++resource++pageturner.resources/FlexPaperViewer.swf", "pageturner", 
    "%(width)i", "%(height)i",
    swfVersionStr, xiSwfUrlStr, 
    flashvars, params, attributes);
    
  swfobject.createCSS("#flashContent", "display:block;text-align:left;");

});
""" % {
    'context_url' : self.context.absolute_url(),
    'width' : self.settings.width,
    'height' : self.settings.height,
    'progressive_loading' : str(self.settings.progressive_loading).lower(),
    'print_enabled' : str(self.settings.print_enabled).lower(),
    'full_screen_visible' : str(self.settings.full_screen_visible).lower(),
    'search_tools_visible' : str(self.settings.search_tools_visible).lower(),
    'cursor_tools_visible' : str(self.settings.cursor_tools_visible).lower()
}

class DownloadSWFView(PageTurnerView):
    
    def render_blob_version(self):
        # done much like it is done in plone.app.blob's index_html
        header_value = contentDispositionHeader(
            disposition='inline',
            filename=self.context.getFilename().replace('.pdf', '.swf'))
        
        blob = self.settings.data
        blobfi = openBlob(blob)
        length = fstat(blobfi.fileno()).st_size
        blobfi.close()
        
        self.request.response.setHeader('Last-Modified', rfc1123_date(self.context._p_mtime))
        self.request.response.setHeader('Accept-Ranges', 'bytes')
        self.request.response.setHeader('Content-Disposition', header_value)
        self.request.response.setHeader("Content-Length", length)
        self.request.response.setHeader('Content-Type', 'application/x-shockwave-flash')
        range = handleRequestRange(self.context, length, self.request, self.request.response)
        return BlobStreamIterator(blob, **range)
        
    def __call__(self):
        self.settings = Settings(self.context)
        
        if self.pab_installed and isinstance(self.settings.data, Blob):
            return self.render_blob_version()
        else:
            return converted_field.download(self.context)        

                
class SettingsForm(ploneformbase.EditForm):
    """
    The page that holds all the slider settings
    """
    form_fields = form.FormFields(IPageTurnerSettings)

    label = _(u'heading_pageturner_settings_form', default=u"Page Turner Settings")
    description = _(u'description_pageturner_settings_form', default=u"Configure the parameters for this Viewer.")

    @form.action(_(u"label_save", default="Save"),
                 condition=form.haveInputWidgets,
                 name=u'save')
    def handle_save_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data, self.adapters):
            zope.event.notify(zope.lifecycleevent.ObjectModifiedEvent(self.context))
            zope.event.notify(ploneformbase.EditSavedEvent(self.context))
            self.status = "Changes saved"
        else:
            zope.event.notify(ploneformbase.EditCancelledEvent(self.context))
            self.status = "No changes"
            
        url = getMultiAdapter((self.context, self.request), name='absolute_url')() + '/view'
        self.request.response.redirect(url)

from wc.pageturner.events import queue_job
from DateTime import DateTime
class Utils(BrowserView):
    implements(IUtils)
    
    def enabled(self):
        try:
            return IFileContent.providedBy(self.context) and self.context.getLayout() == 'page-turner'
        except:
            return False
            
    def convert(self):
        settings = Settings(self.context)
        settings.last_updated = DateTime().ISO8601()
        queue_job(self.context)
            
