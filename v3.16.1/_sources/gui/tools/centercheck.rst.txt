.. _centercheck:

CenterCheck Tool
================

**CenterCheck Tool** selects redial symetric Line Cuts and shows their 1d intensity plots to check the center of the image

.. figure:: ../../_images/centerchecklavue.png


*    **All Cuts:** displays all cuts on the 1d-plot
*    **Length** default length of the line-cuts
*    **Reset** reset to symetric structure

The **width** of the line-cut can be set the handle in the middle of the line-cut selector.


The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration`` option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``cuts_number`` (integer), ``cuts_length`` (integer),  ``connect_nan`` (boolean),  ``geometry`` (string:float dictionary with the ``centerx``, ``centery`` keywords)

.. code-block:: console

   lavue -u centercheck --tool-configuration \{\"cuts_number\":2,\"cuts_length\":600,\"connect_nan\":true}

A JSON dictionary with the **tool results** is passed to the **LavueController** or/and to **user functions plugins**. It contains the following keys:

``tool`` : "centercheck", ``imagename`` (string), ``timestamp`` (float), ``linecutlength`` (float),  ``nrlinecuts`` (int), ``linecut_%i`` ([[float, float], ..., [float, float]]) [i.e. "%i" goes from 1 to ``nrlinecuts``]

.. |br| raw:: html

     <br>
