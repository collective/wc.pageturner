from Products.Five.browser import BrowserView
from zope.annotation.interfaces import IAnnotations
from plone.app.form import base as ploneformbase
from persistent.dict import PersistentDict
from DateTime import DateTime
from zope.interface import implements
from zope.formlib import form
from StringIO import StringIO
import os, popen2
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
        swf2pdf_binary = self._findbinary(bin_name)
        self.swf2pdf_binary = swf2pdf_binary
        if swf2pdf_binary is None:
            raise IOError, "Unable to find swf2pdf binary"

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
        
        cmd = "%s %s -o %s -T 9 -f" % (self.swf2pdf_binary, path, newpath)
        child_stdout, child_stdin, child_stderr = popen2.popen3(cmd)
        
        output = child_stdout.read()
        if output.startswith('FATAL'):
            return Exception(output)
        
        newfi = open(newpath)
        
        return newfi.read()


try:
    pdf2swf = pdf2swf_subprocess()
except IOError:
    pdf2swf = None

try:
    import plone.app.blob
    from plone.app.blob.download import handleIfModifiedSince, handleRequestRange
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
                        self.settings.data = Blob(result)
                    else:
                        file = BaseUnit('_converted_file', result, 
                            mimetype='application/x-shockwave-flash',
                            filename=self.context.getFilename().replace('.pdf', '.swf'),
                            context=self.context)
                        converted_field.set(self.context, file, _initializing_=True)
                    self.settings.last_updated = DateTime().pCommonZ()
                    self.settings.successfully_converted = True
                except:
                    utils.addPortalMessage("There was an error trying to convert the PDF. Maybe the PDF is encrypted?")
                    self.settings.successfully_converted = False
                    self.enabled = False
        else:
            self.is_pdf = False
            utils.addPortalMessage("The file is not a PDF.")
            
        return self.index()

    def javascript(self):
        return """
jq(document).ready(function(){
<!-- For version detection, set to min. required Flash Player version, or 0 (or 0.0.0), for no version detection. --> 
var swfVersionStr = "9.0.124";
<!-- To use express install, set to playerProductInstall.swf, otherwise the empty string. -->
var xiSwfUrlStr = "${expressInstallSwf}";
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
    localeChain: "en_US"
};

var params = {

}
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
    flashvars, params, attributes
);

swfobject.createCSS("#pageturner", "display:block;text-align:left;");
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
        return IFileContent.providedBy(self.context) and \
            hasattr(self.context, 'layout') and self.context.layout == "page-turner"
            
            