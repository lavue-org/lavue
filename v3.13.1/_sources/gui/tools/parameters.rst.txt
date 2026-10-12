.. _parameters:

Parameters Tool
===============

**Parameters Tool** allows to read and write tango attributes to change detector settings

.. figure:: ../../_images/lavueparameters.png

*    **Setup:** add and remove tango device attributes and their labels to the list of parameters
*    **Apply:** write parameter values from the white edit widget to the corresponding tango device attribute

**Read values** of parameters are displayed in the corresponding green widgets.

The configuration of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``tango_det_attrs`` (string:string dictonary)

e.g.

.. code-block:: console

   lavue -u parameters -s test --tool-configuration \{\"tango_det_attrs\":\{\"lmbd2\":\"p00/lambda/dellek/LiveLastImageData\",\"tangotest\":\"sys/tg_test/1/long_image_ro\",\"mca01\":\"p00/mca/exp.01/Data\"\}\} --start

.. |br| raw:: html

     <br>
