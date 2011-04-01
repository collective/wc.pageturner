Introduction
============

This package is a Plone product that will add a `Page Turner` view to the PDF File content type. 
The result is that you'll be able to view PDFs much in the same way you can view them on
scribd.com. It uses the open source project, Flex Paper, to display the PDFs. You can find
information about it at `http://flexpaper.devaldi.com/`.


Requirements
------------

This product requires that you have pdf2swf installed. pdf2swf is included with SWFTools.
I suggest you stick with the package managers to install this as there are some dependencies
that need to be installed.

If you're using Ubuntu Lucid, the swftools package should now be in the package repositories now:

  # sudo apt-get install swftools

On Mac, if you have MacPorts installed you can,

  # sudo port install swftools


If all else fails, you can download SWF tools from `http://www.swftools.org/` and install it yourself.


Windows Users
~~~~~~~~~~~~~

Make sure pdf2swf.exe is in your path otherwise this product won't work.


How-To
------

* Add your PDF as a file to your Plone site.

* Edit the various setting of the Page turner by clicking the `Page Turner Settings` button that is now available

* To turn off auto-selecting of the page turner layout for PDF files, go to ZMI -> portal_properties -> site_properties and
  customize the page_turner_auto_select_layout property to off.


Tested With
-----------

* Plone 3 and 4

* Also works with Blob storage transparently so the converted PDFs aren't stored in the ZODB


Credits
-------

Credit goes to Wildcard corp and Talin Senner for sponsoring and designing the product and Nathan Van Gheem for coding it.


Asynchronous Conversion
-----------------------

With large PDFs the conversion to Flex Paper can take some time. If you have plone.app.async installed and configured, 
this conversion will now happen in asynchronously.


Convert All
-----------

If you'd like to convert all the existing documents on your site, visit the url, http://www.yoursite.com/@@convertall-to-flexpaper
