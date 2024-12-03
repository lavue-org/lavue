.. _intensity:

Intensity Tool
==============

**Intensity Tool** shows intensity of the selected pixels.

.. figure:: ../../_images/intensitylavue.png

*    **Pixel intensity** pointed by mouse and its position
*    **Axes Labels** and **Scales:** also changeable from ZMQ Source
*    **Crosshair locker:** show red horizontal and vertical lines denoting a selected point

The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a ``toolconfig`` variable of ``LavueController.LavueState`` with the following keys:

``crosshair_locker`` (boolean), ``xunits`` (string), ``yunits`` (string), ``xtext`` (string), ``ytext`` (string), ``position`` ([float, float]), ``scale`` ([float, float])

e.g.

.. code-block:: console

   lavue -u intensity -s test --tool-configuration \{\"cross_hair\":false,\"position\":[112,125.5],\"scale\":[2,3]\} --start

A JSON dictionary with the **tool results** is passed to the **LavueController** or/and to **user functions plugins**. It contains the following keys:

``tool`` : "intensity", ``imagename`` (string), ``timestamp`` (float), ``pixel`` ([float, float]), ``scaled_coordiantes`` ([float, float]), ``coordiantes_units`` ([str, str]), ``intensity_scaling`` (str) [i.e. "log", "linear" or "sqrt"]

.. |br| raw:: html

     <br>

