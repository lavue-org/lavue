.. _tango-file:

Tango File
==========

Images defined by file and directory tango attributes, e.g. `Pilatus` without Hidra

.. figure:: ../../_images/tangofilelavue.png


The **Tango File** image source frame contains the following fields:

*    **File Attr:** selects the tango attributes of the last image file,
     |br| e.g. `p09/pilatus/haso228k/LastImageTaken` or
     |br| e.g. `p09/pilatus/haso228k/LastImageTaken`
     |br| The possible file attributes can be preselected in the configuration dialog.
*    **Dir Attr:** selects the tango attributes of the last image file directory,
     |br| e.g. `p09/pilatus/haso228k/LastImagePath`
     |br| The possible file directory attributes can be preselected in the configuration dialog.
*    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
*    **Start/Stop** button to launch or interrupt image querying

The Tango File attribute and Tango Dir attribute contains a string with the file name and its directory in a raw format or `file:/` , `h5file:/`
or `http:/`, `https:/` scheme.


.. |br| raw:: html

     <br>
