.. _tine-prop:

Tine Property
=============

Images from a tine property, e.g. `Tine Camera`

.. figure:: ../../_images/lavuetineprop.png

The **Tine Property** image source frame contains the following fields:

*    **Addr/Prop:** selects the tine address and property of the detector last image,
     |br| e.g. `/HASYLAB/P00_LM00/Output/Frame`
     |br| The possible address/property can be preselected in the configuration dialog.
*    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
*    **Start/Stop** button to launch or interrupt image querying

By clicking on an **empty start** in the Addr/Prop combobox you can add a label to the current  item (only in the expert mode).

By clicking on an **full start** in the Addr/Prop combobox you can remove the label of the current  item (only in the expert mode).

.. |br| raw:: html

     <br>
