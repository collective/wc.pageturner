from Products.Five.browser import BrowserView
from plone.app.form import base as ploneformbase
from DateTime import DateTime
from zope.interface import implements
from zope.formlib import form
import os, subprocess
from tempfile import mkstemp
from Acquisition import aq_inner
from webdav.common import rfc1123_date
from Products.Archetypes.utils import contentDispositionHeader
from os import fstat
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.Field import FileField
from Products.Archetypes.BaseUnit import BaseUnit
from interfaces import IPageTurnerSettings, IUtils
from wc.pageturner import mf as _
from settings import Settings
from Products.ATContentTypes.interface.file import IFileContent
import zope.event, zope.lifecycleevent
from zope.component import getMultiAdapter

from logging import getLogger
logger = getLogger('wc.pageturner')

converted_field = FileField('_converted_file')

class pdf2swf_subprocess:
    """
    idea of how to handle this shamelessly
    stolen from ploneformgen's gpg calls
    """
    paths = ['/bin', '/usr/bin', '/usr/local/bin']

    def __init__(self):
        if os.name == 'nt':
            bin_name = 'pdf2swf.exe'
        else:
            bin_name = 'pdf2swf'
        pdf2swf_binary = self._findbinary(bin_name)
        self.pdf2swf_binary = pdf2swf_binary
        if pdf2swf_binary is None:
            raise IOError, "Unable to find pdf2swf binary"

    def _findbinary(self,binname):
        import os
        if os.environ.has_key('PATH'):
            path = os.environ['PATH']
            path = path.split(os.pathsep)
        else:
            path = self.paths
        for dir in path:
            fullname = os.path.join(dir, binname)
            if os.path.exists( fullname ):
                return fullname
        return None

    def convert(self, filedata):
        _, path = mkstemp()
        fi = open(path, 'w')
        fi.write(filedata)
        fi.close()
        
        _, newpath = mkstemp()
        
        cmd = "%s %s -o %s -T 9 -f" % (self.pdf2swf_binary, path, newpath)
        output = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        if output.startswith('FATAL') or "Segmentation fault" in output:
            logger.exception('Error converting PDF: ' + output)
            raise Exception(output)
        
        newfi = open(newpath)
        newdata = newfi.read()
        
        if not newdata:
            logger.exception('Error converting PDF: ' + output)
            raise Exception(output)
        
        return newdata


try:
    pdf2swf = pdf2swf_subprocess()
except IOError:
    logger.exception("No SWFTools installed. Page Turner will not work.")
    pdf2swf = None

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
    enabled = pdf2swf is not None and has_pab
    is_pdf = True
        
    def __call__(self):
        self.settings = Settings(self.context)
        utils = getToolByName(self.context, 'plone_utils')
        
        if not self.installed:
            utils.addPortalMessage("Since you do not have swftools installed on this system, we can not render the pages of this PDF.")
        elif self.context.getContentType() in ('application/pdf', 'application/x-pdf', 'image/pdf'):
            
            if DateTime(self.settings.last_updated) < DateTime(self.context.ModificationDate()):
                context = aq_inner(self.context)
                field = context.getField('file') or context.getPrimaryField()
                
                try:
                    result = pdf2swf.convert(str(field.get(context).data))
                    if self.pab_installed:
                        blob = Blob()
                        blob.open('w').writelines(result)
                        self.settings.data = blob
                    else:
                        file = BaseUnit('_converted_file', result, 
                            mimetype='application/x-shockwave-flash',
                            filename=self.context.getFilename().replace('.pdf', '.swf'),
                            context=self.context)
                        converted_field.set(self.context, file, _initializing_=True)
                    self.settings.successfully_converted = True
                except:
                    logger.exception('Error converting PDF')
                    utils.addPortalMessage("There was an error trying to convert the PDF. Maybe the PDF is encrypted, corrupt or malformed?")
                    self.settings.successfully_converted = False
                    self.enabled = False
                    
                self.settings.last_updated = DateTime().pCommonZ()
        else:
            self.is_pdf = False
            utils.addPortalMessage("The file is not a PDF.")
            
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
    PrintEnabled : true,
    FullScreenAsMaxWindow : false,
    PrintToolsVisible : true,
    ViewModeToolsVisible : true,
    ZoomToolsVisible : true,
    FullScreenVisible : true,
    NavToolsVisible : true,
    CursorToolsVisible : true,
    SearchToolsVisible : true,
    localeChain: "en_US"
  };
	  
  var params = {};
  params.quality = "high";
  params.bgcolor = "#ffffff";
  params.allowscriptaccess = "sameDomain";
  params.allowfullscreen = "true";
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
    'height' : self.settings.height
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

class Utils(BrowserView):
    implements(IUtils)
    
    def enabled(self):
        try:
            return IFileContent.providedBy(self.context) and self.context.getLayout() == 'page-turner'
        except:
            return False
            
            
