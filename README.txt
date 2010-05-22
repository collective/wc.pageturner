Introduction
============

This package is a Plone product that will add a `Page Turner` view to the File content type. 
The result is that you'll be able to view PDFs much in the same way you can view them on
scribd.com. It uses the open source project, Flex Paper, to display the PDFs. You can find
information about it at `http://flexpaper.devaldi.com/`.


Requirements
------------

This product requires that you have pdf2swf installed. pdf2swf is included with SWFTools.
I suggest you stick with the package managers to install this as there are some dependencies
that need to be installed.

If you're using Ubuntu Lucid, you can find a swftools download at `http://packages.ubuntu.com/karmic/swftools`
that seem to work.

If all else fails, you can download SWF tools from `http://www.swftools.org/`. 


How-To
------

* Add your PDF as a file to your Plone site.

* Select the `Page Turner` view from the display drop down.

* Edit the height and width of the Page turner by clicking the `Page Turner Settings` button that is now available


Tested With
-----------

* Plone 3 and 4

* Also works with Blob storage transparently so the converted PDFs aren't stored in the ZODB



Credits
-------

Credit goes to Wildcard corp and Talin Senner for sponsoring and designing the product and Nathan Van Gheem for coding it.