from Products.CMFCore.utils import getToolByName
from convert import convert
from zope.component import getUtility
from settings import Settings
from logging import getLogger

logger = getLogger('wc.pageturner')

try:
    from plone.app.async.interfaces import IAsyncService
    async_installed = True
except:
    async_installed = False


def queue_job(object):
    if async_installed:
        try:
            settings = Settings(object)
            async = getUtility(IAsyncService)
            async.queueJob(convert, object)
            settings.converting = True
        except:
            logger.exception("Error using plone.app.async with wc.pageturner. "
                             "Converting pdf without plone.app.async...")
            convert(object)
    else:
        convert(object)


def handle_file_creation(object, event):
    qi = getToolByName(object, 'portal_quickinstaller')
    if not qi.isProductInstalled('wc.pageturner'):
        return

    if object.getContentType() not in ('application/pdf', 'application/x-pdf',
                                       'image/pdf'):
        return
    ptool = getToolByName(object, 'portal_properties')
    site_props = getattr(ptool, 'site_properties', None)
    auto_layout = site_props.getProperty('page_turner_auto_select_layout',
                                         False)
    if auto_layout and object.getLayout() != 'page-turner':
        object.setLayout('page-turner')

    # for circular depend
    try:
        from wildcard.pdfpal.ocr import copyPdfMetadata
        new_pdfpal_installed = True
    except:
        new_pdfpal_installed = False
    if not new_pdfpal_installed or not \
            qi.isProductInstalled('wildcard.pdfpal'):
        # if the new version of wildcard.pdfpal is installed, allow it to queue
        # this job up after it creates the searchable pdf.
        # otherwise, just queue it up here.
        queue_job(object)
