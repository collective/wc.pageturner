import subprocess
import os
from tempfile import mkstemp
from Products.Archetypes.Field import FileField
from settings import Settings
from Acquisition import aq_inner
from Products.Archetypes.BaseUnit import BaseUnit
from DateTime import DateTime
from logging import getLogger
from Products.Archetypes.atapi import AnnotationStorage

logger = getLogger('wc.pageturner')

converted_field = FileField('_converted_file', storage = AnnotationStorage(migrate=True))

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
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()[0]
        if output.startswith('FATAL') or "Segmentation fault" in output:
            logger.exception('Error converting PDF: ' + output)
            raise Exception(output)
        elif process.returncode != 0:
            logger.exception("pdf2swf process did not exit cleanly! Error Code: %d" % (process.returncode))
            raise Exception(output)
        
        newfi = open(newpath)
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
    if DateTime(settings.last_updated) < DateTime(context.ModificationDate()):
        context = aq_inner(context)
        field = context.getField('file') or context.getPrimaryField()
        
        try:
            result = pdf2swf.convert(str(field.get(context).data))
            if has_pab:
                blob = Blob()
                blob.open('w').writelines(result)
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
        
    