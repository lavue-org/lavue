.. _epics-pv:

Epics PV
========

Images from a Epics Process Variables

.. figure:: ../../_images/lavueepicspv.png

The **Epics PV** image source frame contains the following fields:

    **PV Name:** selects the Process Variable name with  the detector last image data,
    The possible attributes can be preselected in the configuration dialog.
    **Shape:** selects the Process Variable name shape, e.g. `640,480`
    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
    **Start/Stop** button to launch or interrupt image querying

By clicking on an **empty start** in the PV name and Shape combobox you can add a label to the current  item (only in the expert mode).

By clicking on an **full start** in the PV name and Shape combobox you can remove the label of the current  item (only in the expert mode).

.. |br| raw:: html

     <br>
