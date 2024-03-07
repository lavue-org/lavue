.. _maxima:

Maxima Tool
===========

**Maxima Tool** points pixels with the highest intensity

.. figure:: ../../_images/lavue_maxima.png

*    **Maxima:** a list of pixels with the highest intensity, i.e  nr: intensity_value at (x, y)
     |br| A number of maxima to find can be selected in a spin-box on the right
*    **Geometry:** detector geometry parameters.  They can be pass in both ways via LavueController tango server
*    **theta angles** or **q-space**  selects the radial transformation

The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``maxima_number``  (integer), ``current_maximum``  (integer), ``units`` (``angles``  or ``q-spaces`` string), ``geometry`` (string:float dictionary with the ``centerx``, ``centery``, ``energy``, ``pixelsizex``, ``pixelsizey``, ``detdistance`` keywords)

e.g.

.. code-block:: console

   lavue -u maxima -s test --tool-configuration \{\"maxima_number\":10,\"units\":\"angles\",\"geometry\":\{\"centerx\":123.4,\"centery\":93.4,\"pixelsizex\":70,\"pixelsizey\":70.2,\"energy\":5050,\"detdistance\":50.5\}\} --start

.. |br| raw:: html

     <br>
