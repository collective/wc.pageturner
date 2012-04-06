import subprocess
import os
from tempfile import mkstemp
from Products.Archetypes.Field import FileField
from settings import Settings, GlobalSettings
from Acquisition import aq_inner
from Products.Archetypes.BaseUnit import BaseUnit
from DateTime import DateTime
from logging import getLogger
from Products.Archetypes.atapi import AnnotationStorage
from zope.app.component.hooks import getSite

logger = getLogger('wc.pageturner')

converted_field = FileField('_converted_file',
    storage=AnnotationStorage(migrate=True))


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
            raise IOError("Unable to find pdf2swf binary")

    def _findbinary(self, binname):
        import os
        if 'PATH' in os.environ:
            path = os.environ['PATH']
            path = path.split(os.pathsep)
        else:
            path = self.paths
        for dir in path:
            fullname = os.path.join(dir, binname)
            if os.path.exists(fullname):
                return fullname
        return None

    def convert(self, filedata, s_opts=[], password=None):
        fd, path = mkstemp()
        os.close(fd)
        fi = open(path, 'wb')
        fi.write(filedata)
        fi.close()

        fd, newpath = mkstemp()
        os.close(fd)

        s_opts = ' '.join(['-s %s' % o for o in s_opts])
        if password:
            password = '--password=%s' % password
        else:
            password = ''
        cmd = "%s %s -o %s -T 9 -f -t -G %s %s" % (self.pdf2swf_binary, path,
            newpath, s_opts, password)
        logger.info("Running command %s" % cmd)
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        output = process.communicate()[0]
        logger.info("Finished Running Command %s" % cmd)
        if output.startswith('FATAL') or "Segmentation fault" in output or \
                process.returncode != 0:
            logger.exception('Error converting PDF: ' + output)
            # cleanup
            os.remove(newpath)
            os.remove(path)
            raise Exception(output)

        newfi = open(newpath, 'rb')
        newdata = newfi.read()
        newfi.close()

        # now remove both files
        os.remove(newpath)
        os.remove(path)

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
    from ZODB.blob import Blob
    has_pab = True
except:
    has_pab = False


def convert(context):
    """
    Convert PDF to Flex Paper
    """

    settings = Settings(context)
    site = getSite()
    global_settings = GlobalSettings(site)

    if DateTime(settings.last_updated) < DateTime(context.ModificationDate()):
        context = aq_inner(context)
        field = context.getField('file') or context.getPrimaryField()

        import transaction
        # commit anything done before the expensive operation
        transaction.commit()
        try:
            s_options = settings.command_line_options and \
                settings.command_line_options or \
                global_settings.command_line_options
            if s_options:
                opts = [o.strip().replace(' ', '').replace('\t', '')
                            for o in s_options.split(',')]
            else:
                opts = []
            result = pdf2swf.convert(str(field.get(context).data), opts,
                password=settings.encryption_password)
            transaction.begin()
            if has_pab:
                blob = Blob()
                bfile = blob.open('w')
                bfile.write(result)
                bfile.close()
                settings.data = blob
            else:
                file = BaseUnit('_converted_file', result,
                    mimetype='application/x-shockwave-flash',
                    filename=context.getFilename().replace('.pdf', '.swf'),
                    context=context)
                converted_field.set(context, file, _initializing_=True)
            settings.successfully_converted = True
        except:
            logger.exception('Error converting PDF')
            settings.successfully_converted = False
        settings.last_updated = DateTime().ISO8601()
        settings.converting = False
        transaction.commit()
