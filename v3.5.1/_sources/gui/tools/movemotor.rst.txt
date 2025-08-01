.. _move-motor:

MoveMotor Tool
==============

**MoveMotor Tool** moves the selected motors to the position pointed by mouse

.. figure:: ../../_images/motorslavue.png


*    **X, Y:** final  x,y positions
*    **Motors:** selects x,y motors
*    **Move/Stop** motors action
*    **Track/Untrack:** show/hide the current motors positions
*    **Pixel intensity** pointed by mouse and its position
*    **Axes Labels and Scales:** also changeable from ZMQ Source

The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration`` option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``motors`` ([string, string]), ``x_position`` (float), ``y_position`` (float), ``xunits`` (string), ``yunits`` (string), ``xtext`` (string), ``ytext`` (string), ``position`` ([float, float]), ``scale`` ([float, float]), ``move`` (boolean), ``stop`` (boolean),

e.g.

.. code-block:: console

   lavue -u movemotors -s test --tool-configuration \{\"motors\":[\"mot02\",\"mot03\"],\"x_position\":202.1,\"y_position\":123,\"position\":[112,145.5],\"scale\":[2,3],\"move\":true\} --start

.. |br| raw:: html

     <br>
