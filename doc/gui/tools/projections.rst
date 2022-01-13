.. _projections:

Projections Tool
================

**Projections Tool** plots horizontal and vertical projections of the current image

.. figure:: ../../_images/projectionslavue.png

*    **Row/Column slice** e.g. 9:10 or 100:120:2, <empty> for all
*    **Mapping:** mean or sum
*    **Pixel intensity** pointed by mouse and its position

The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``mapping`` (``sum``  or ``mean`` string), ``rows`` (string with a python slice), ``columns`` (string with a python slice)

e.g.

.. code-block:: console

   lavue -u projections -s test --tool-configuration \{\"mapping\":\"sum\",\"rows\":\"10:200:5\",\"columns\":\"50:150\"\} --start


.. |br| raw:: html

     <br>
