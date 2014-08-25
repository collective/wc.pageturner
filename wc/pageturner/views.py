from Products.Five.browser import BrowserView
from plone.app.form import base as ploneformbase
from zope.interface import implements
from zope.formlib import form
from webdav.common import rfc1123_date
from Products.Archetypes.utils import contentDispositionHeader
from os import fstat
from Products.CMFCore.utils import getToolByName
from interfaces import IPageTurnerSettings, IUtils, IGlobalPageTurnerSettings
from wc.pageturner import mf as _
from settings import Settings, GlobalSettings
from plone.app.contenttypes.interfaces import IFile
import zope.event
import zope.lifecycleevent
from zope.component import getMultiAdapter
from convert import pdf2swf
from zope.component.hooks import getSite
from plone.memoize.view import memoize
from wc.pageturner.events import queue_job
from DateTime import DateTime

from logging import getLogger
logger = getLogger('wc.pageturner')

from plone.app.blob.download import handleRequestRange
from plone.app.blob.iterators import BlobStreamIterator
from plone.app.blob.utils import openBlob


def either(one, two):
    if one is None:
        return two
    return one


class PageTurnerView(BrowserView):

    installed = pdf2swf is not None
    enabled = pdf2swf is not None

    @property
    @memoize
    def portal_url(self):
        return getMultiAdapter((self.context, self.request),
                               name="plone_portal_state").portal_url()

    def initialize(self):
        site = getSite()
        self.settings = Settings(self.context)
        self.global_settings = GlobalSettings(site)

        utils = getToolByName(self.context, 'plone_utils')
        msg = None

        if self.context.file.contentType in ('application/pdf',
                                             'application/x-pdf', 'image/pdf'):
            if not self.installed:
                msg = "Since you do not have swftools installed on this " + \
                      "system, we can not render the pages of this PDF."
            elif self.settings.converting is not None and \
                    self.settings.converting:
                msg = "The PDF is currently being converted to the " + \
                      "FlexPaper view..."
                self.enabled = False
            elif not self.settings.successfully_converted:
                msg = "There was an error trying to convert the PDF. Maybe " +\
                      "the PDF is encrypted, corrupt or malformed?"
                self.enabled = False
        else:
            self.enabled = False
            msg = "The file is not a PDF. No need for this view."

        if msg:
            mtool = getToolByName(self.context, 'portal_membership')
            if mtool.checkPermission('cmf.ModifyPortalContent', self.context):
                utils.addPortalMessage(msg)

    def __call__(self):
        self.initialize()
        return super(PageTurnerView, self).__call__()

    def javascript(self):
        return """
jQuery(document).ready(function(){
    window.flexPaper = new FlexPaperViewer(
        '%(portal_url)s/%(resources)s/FlexPaperViewer',
        'pageturner', { config : {
        SwfFile : escape('%(context_url)s/converted.swf'),
        Scale : 0.6,
        ZoomTransition : 'easeOut',
        ZoomTime : 0.5,
        ZoomInterval : 0.2,
        FitPageOnLoad : true,
        FitWidthOnLoad : %(fit_width_on_load)s,
        FullScreenAsMaxWindow : false,
        ProgressiveLoading : false,
        MinZoomSize : 0.2,
        MaxZoomSize : 5,
        SearchMatchAll : false,
        InitViewMode : 'Portrait',
        PrintPaperAsBitmap : false,

        ViewModeToolsVisible : true,
        PrintEnabled : %(print_enabled)s,
        CursorToolsVisible : %(cursor_tools_visible)s,
        SearchToolsVisible : %(search_tools_visible)s,
        ProgressiveLoading : %(progressive_loading)s,

        localeChain: 'en_US',
        swfinstall: '%(portal_url)s/%(resources)s/playerProductInstall.swf'
        }});
    jQuery('#pageturner').show().width(%(width)s).height(%(height)s);
});
""" % {
            'resources': '++resource++pageturner.resources',
            'context_url': self.context.absolute_url(),
            'portal_url': self.portal_url,
            'width': either(self.settings.width, self.global_settings.width),
            'height': either(self.settings.height, self.global_settings.height),  # noqa
            'fit_width_on_load': str(either(self.settings.fit_width_on_load,
                self.global_settings.fit_width_on_load)).lower(),
            'progressive_loading': str(either(self.settings.progressive_loading,  # noqa
                self.global_settings.progressive_loading)).lower(),
            'print_enabled': str(either(self.settings.print_enabled,
                self.global_settings.print_enabled)).lower(),
            'full_screen_visible': str(either(self.settings.full_screen_visible,  # noqa
                self.global_settings.full_screen_visible)).lower(),
            'search_tools_visible': str(either(self.settings.search_tools_visible,  # noqa
                self.global_settings.search_tools_visible)).lower(),
            'cursor_tools_visible': str(either(self.settings.cursor_tools_visible,  # noqa
                self.global_settings.cursor_tools_visible)).lower(),
}


class DownloadSWFView(PageTurnerView):

    def __call__(self):
        self.initialize()
        # done much like it is done in plone.app.blob's index_html
        header_value = contentDispositionHeader(
            disposition='inline',
            filename=self.context.file.filename.replace('.pdf', '.swf'))

        blob = self.settings.data
        blobfi = openBlob(blob)
        length = fstat(blobfi.fileno()).st_size
        blobfi.close()

        self.request.response.setHeader(
            'Last-Modified', rfc1123_date(self.context._p_mtime))
        self.request.response.setHeader('Accept-Ranges', 'bytes')
        self.request.response.setHeader('Content-Disposition', header_value)
        self.request.response.setHeader("Content-Length", length)
        self.request.response.setHeader(
            'Content-Type', 'application/x-shockwave-flash')
        range = handleRequestRange(
            self.context, length, self.request,
            self.request.response)
        return BlobStreamIterator(blob, **range)


class SettingsForm(ploneformbase.EditForm):
    """
    The page that holds all the slider settings
    """
    form_fields = form.FormFields(IPageTurnerSettings)

    label = _(u'heading_pageturner_settings_form',
              default=u"Page Turner Settings")
    description = _(u'description_pageturner_settings_form',
                    default=u"these settings override the global settings.")

    @form.action(_(u"label_save", default="Save"),
                 condition=form.haveInputWidgets,
                 name=u'save')
    def handle_save_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data,
                             self.adapters):
            zope.event.notify(
                zope.lifecycleevent.ObjectModifiedEvent(self.context))
            zope.event.notify(ploneformbase.EditSavedEvent(self.context))
            self.status = "Changes saved"
        else:
            zope.event.notify(ploneformbase.EditCancelledEvent(self.context))
            self.status = "No changes"

        # convert right now if password provided
        if data.get('encryption_password', None):
            settings = Settings(self.context)
            settings.last_updated = DateTime('1999/01/01').ISO8601()
            queue_job(self.context)

        url = getMultiAdapter((self.context, self.request),
                              name='absolute_url')() + '/view'
        self.request.response.redirect(url)


class GlobalSettingsForm(ploneformbase.EditForm):
    form_fields = form.FormFields(IGlobalPageTurnerSettings)

    label = _(u'heading_pageturner_global_settings_form',
              default=u"Global Page Turner Settings")
    description = _(u'description_pageturner_global_settings_form',
                    default=u"Configure the parameters for this Viewer.")

    @form.action(_(u"label_save", default="Save"),
                 condition=form.haveInputWidgets,
                 name=u'save')
    def _handle_save_action(self, action, data):
        if form.applyChanges(self.context, self.form_fields, data,
                             self.adapters):
            zope.event.notify(ploneformbase.EditSavedEvent(self.context))
            self.status = "Changes saved"
        else:
            zope.event.notify(ploneformbase.EditCancelledEvent(self.context))
            self.status = "No changes"
        self.request.response.redirect(
            self.context.absolute_url() + '/@@global-page-turner-settings')


class Utils(BrowserView):
    implements(IUtils)

    def enabled(self):
        try:
            return IFile.providedBy(self.context) and \
                self.context.getLayout() == 'page-turner'
        except:
            return False

    def convert(self):
        if self.enabled():
            settings = Settings(self.context)
            settings.last_updated = DateTime('1999/01/01').ISO8601()
            queue_job(self.context)

        self.request.response.redirect(self.context.absolute_url() + '/view')

    def convert_all(self):
        confirm = self.request.get('confirm', 'no')
        if confirm != 'yes':
            return 'You must append "?confirm=yes"'
        else:
            ptool = getToolByName(object, 'portal_properties')
            site_props = getattr(ptool, 'site_properties', None)
            auto_layout = site_props.getProperty(
                'page_turner_auto_select_layout', False)

            catalog = getToolByName(self.context, 'portal_catalog')
            files = catalog(object_provides=IFile.__identifier__)
            for brain in files:
                file = brain.getObject()
                if file.file.contentType not in ('application/pdf',
                                                 'application/x-pdf',
                                                 'image/pdf'):
                    continue

                if auto_layout and file.getLayout() != 'page-turner':
                    file.setLayout('page-turner')

                self.request.response.write(
                    'Converting %s to flex paper...\n' % file.absolute_url())
                settings = Settings(file)
                settings.last_updated = DateTime('1999/01/01').ISO8601()
                queue_job(file)
