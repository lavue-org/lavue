.. _mesh-scan:

MeshScan Tool
=============

**MeshScan Tool** performs sardana mesh scan on the selected ROI region

.. figure:: ../../_images/meshlavue.png

*    **Intervals:** select x,y intervals and integration time
*    **Motors:** select x,y motors
*    **Scan/Stop:** sardana mesh macro with the active MG
*    **Pixel intensity** pointed by mouse and its position
*    **Axes Labels and Scales**: also changeable from ZMQ Source

The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``motors`` ([string, string]), ``x_intervals`` (integer), ``y_intervals`` (integer), ``interval_time`` (float), ``xunits`` (string), ``yunits`` (string), ``xtext`` (string), ``ytext`` (string), ``position`` ([float, float]), ``scale`` ([float, float]), ``scan``  (boolean), ``stop``  (boolean),

e.g.

.. code-block:: console

   lavue -u meshscan -s test --tool-configuration \{\"motors\":[\"mot02\",\"mot03\"],\"x_intervals\":20,\"y_intervals\":123,\"interval_time\":0.1,\"position\":[112,145.5],\"scale\":[2,3],\"scan\":true\} --start

.. |br| raw:: html

     <br>
