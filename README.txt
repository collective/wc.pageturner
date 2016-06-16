Introduction
============

This package is a Plone product that will add a `Page Turner` view to the PDF File content type. 
The result is that you'll be able to view PDFs much in the same way you can view them on
scribd.com. It uses the open source project, Flex Paper, to display the PDFs. You can find
information about it at `http://flexpaper.devaldi.com/`.

This package has been superceded by collective.documentviewer, which provides more functionality and is actively maintained.


Requirements
------------

This product requires that you have pdf2swf installed. pdf2swf is included in older versions of SWFTools, 
up to 0.9.0 (the most recent version of SWFTools is 0.9.2 dating from 2012).


Installing pdf2swf with package managers
----------------------------------------

Where possible, we recommend you use package managers to install SWFTools as there are some dependencies
that need to be installed. 

If you're using Ubuntu Lucid (10.04) (and possibly later versions, but not Trusty Tahr, 14.04):

  # sudo apt-get install swftools

On Mac, if you have MacPorts installed you can,

  # sudo port install swftools

On Debian, you'll need to install from source as the swftools package does not include pdf2swf: `http://wiki.swftools.org/wiki/Installation`

Checking that you have installed pdf2swf
----------------------------------------

Once you have installed the package, check if pdf2swf is in your path. On Linux:

  # which pdf2swf
  
On Windows: make sure pdf2swf.exe is in your path:

  C:\> pdf2swf

If it isn't in your path (ie. you get an error message above), you'll have to install manually; see below.

Installing pdf2swf manually
---------------------------

If your package manager installs a version of SWFTools that does not include pdf2swf, you can install an older version of the package that does.

These instructions for installing on Ubuntu are based on http://serverfault.com/questions/623604/install-pdf2swf-on-ubuntu-trusty-tahr14-04.

For AMD64:

  # wget -P /tmp/ http://archive.canonical.com/ubuntu/pool/partner/s/swftools/swftools_0.9.0-0ubuntu2_amd64.deb
  # chmod a+x /tmp/swftools_0.9.0-0ubuntu2_amd64.deb
  # sudo dpkg -i /tmp/swftools_0.9.0-0ubuntu2_amd64.deb

For i386:

  # wget -P /tmp/ http://archive.canonical.com/ubuntu/pool/partner/s/swftools/swftools_0.9.0-0ubuntu2_i386.deb
  # chmod a+x /tmp/swftools_0.9.0-0ubuntu2_i386.deb
  # sudo dpkg -i /tmp/swftools_0.9.0-0ubuntu2_i386.deb
  
Other architectures are available at http://archive.canonical.com/ubuntu/pool/partner/s/swftools/

If all else fails, you can download SWFTools from `http://www.swftools.org/` and install it yourself.

How-To
------

* Add your PDF as a File to your Plone site (Add New -> File menu).

* Edit the various setting of the Page turner by clicking the `Page Turner Settings` button.

* To turn off auto-selecting of the page turner layout for PDF files, go to ZMI -> portal_properties -> site_properties and
  customize the page_turner_auto_select_layout property to off.
  
* PDFs that were on your site before you activated this add-on will need to be converted (you will see an
  error message on each File until you convert it). To convert an individual PDF, click the Flexpaper Convert 
  button. Large PDFs will take some time to be converted.  To convert all PDFs on your site, go to your site's 
  URL and append /@@convertall-to-flexpaper, e.g. http://www.yoursite.com/@@convertall-to-flexpaper


Tested With
-----------

* Plone 3 and 4

* Also works with Blob storage transparently so the converted PDFs aren't stored in the ZODB


Credits
-------

Credit goes to Wildcard Corp and Talin Senner for sponsoring and designing the product, and Nathan Van Gheem for coding it.


Asynchronous Conversion
-----------------------

With large PDFs the conversion to Flex Paper can take some time. If you have plone.app.async installed and configured, 
this conversion will happen asynchronously.


Convert All
-----------

If you'd like to convert all the existing documents on your site, visit the URL http://www.yoursite.com/@@convertall-to-flexpaper


TODO
----

- Add support for Dexterity content types. Maybe via a behavior.


Versions
--------

Flexpaper: 1.5.1


Upgrade Path
------------

For a more fully featured add-on, see https://pypi.python.org/pypi/collective.documentviewer 
