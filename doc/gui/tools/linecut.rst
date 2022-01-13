.. _linecut:

LineCut Tool
============

**LineCut Tool** selects Line Cuts and shows their 1d intensity plots

.. figure:: ../../_images/linecutlavue.png


*    **X in 1d:** Points, X-Pixels, Y-Pixels
*    **All Cuts:** displays all cuts on the 1d-plot

The **width** of the line-cut can be set the handle in the middle of the line-cut selector.


The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration`` option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``x_coordinates`` (points, x-pixels  or y-pixels string), ``cuts_number`` (integer), ``all_cuts`` (boolean)

.. code-block:: console

   lavue -u linecut --tool-configuration \{\"cuts_number\":2,\"x_coordinates\":\"y-pixels\",\"all_cuts\":true}
.. |br| raw:: html

     <br>
