.. _tango-attr:

Tango Attribute
===============

Images from a tango attribute, e.g. `Lambda`, `PCO`, `AGIPD`, `Jungfrau` or `LimaCCDs` detectors

.. figure:: ../../_images/tangoattrlavue.png

The **Tango Attribute** image source frame contains the following fields:

*    **Attribute:** selects the tango attributes of the detector last image, |br|
     e.g. `sys/tg_test/1/double_image_ro`  or `haslambda02:10000/petra3/lambda/01/LiveLastImageData`. |br| The possible attributes can be preselected in the configuration dialog.
*    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
*    **Start/Stop** button to launch or interrupt image querying

LaVue can read also Tango **DevEncoded** attributes. Thus, in order to read **LimaCCDs** images:

#.    set its **video_active** attribute (or **video_live** attribute) to true
#.    select the **video_last_image** attribute of **LimaCCDs** as a Tango Attribute source

or during your scan

#.    select the **last_image** attribute of **LimaCCDs** as a Tango Attribute source

By clicking on an **empty start** in the Attribute combobox you can add a label to the current  item (only in the expert mode).

By clicking on an **full start** in the Attribute combobox you can remove the label of the current  item (only in the expert mode).

.. |br| raw:: html

     <br>
