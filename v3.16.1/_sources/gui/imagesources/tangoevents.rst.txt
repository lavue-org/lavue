.. _tango-events:

Tango Events
============

Images from a tango attribute passed via ``Tango::CHANGE_EVENT`` or ``Tango::DATA_READY_EVENT``, e.g. `LimaCCDs` detectors.

.. figure:: ../../_images/lavue_tangoevents.png

The **Tango Events** image source frame contains the following fields:

*    **Attribute:** selects the tango attributes of the detector last image,
     |br| e.g. `haso000:10000/petra3/limaccds/01/video_last_image`.
     The possible attributes can be preselected in the configuration dialog.
*    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
*    **Start/Stop** button to launch or interrupt image querying

LaVue can read also Tango **DevEncoded** attributes. Thus, in order to read **LimaCCDs** images:

#.    set **TangoEvent** property of **LimaCCDs** to true
#.    set its **video_active** attribute (or **video_live** attribute) to true
#.    select the **video_last_image** attribute of **LimaCCDs** as a Tango Attribute source

or during your scan

#.    set TangoEvent property of **LimaCCDs** to true
#.    select the **last_image** attribute of **LimaCCDs** as a Tango Attribute source.

By clicking on an **empty start** in the Attribute combobox you can add a label to the current  item (only in the expert mode).

By clicking on an **full start** in the Attribute combobox you can remove the label of the current  item (only in the expert mode).

.. |br| raw:: html

     <br>
