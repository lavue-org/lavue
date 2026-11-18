.. _q-roi-proj:

Q+ROI+Proj Tool
===============

**Q+ROI+Proj Tool** combines Angle/Q, ROI and Projections

.. figure:: ../../_images/qroiprojlavue.png

Projections:

*    **Row/Column slice** e.g. ``9:10`` or ``100:120:2``, ``<empty>`` for all
*    **Mapping:** mean or sum

ROI:

The user can use rectangle and ellipse ROI shapes. The rectangle bounds are represented by a list of four integer numbers,  [x1, y1, x2, y2].  The elliptic bounds are represented by a list of five float numbers, i.e. [x, y, width, height, angle].

*    **ROI alias(es)** for roi tango devices
*    **Add** to or **Fetch** from sardana environment (see below). If lavue is working with ANALYSISDEVICE , i.e. lavue -n <device>,  **ROIs** bounds are sending also to tango SPECTRUM  **RoIs**  attribute of the device, e.g. LambdaOnlineAnalysis server.
*    **Sum of** the selected **ROI** or all **ROIs**. The used version can be selected in the configuration.

Geometry:

*    **Geometry: detector geometry parameters.  They can be pass in both ways via **LavueController** tango server
*    **theta angles** or **q-space** selects the radial transformation
*    **Pixel intensity** pointed by mouse and its position

The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``aliases`` (list of strings), ``rois_number`` (integer), ``mapping`` (``sum`` or ``mean`` string), ``rows`` (string with a python slice), ``columns`` (string with a python slice), ``units`` (``angles``  or ``q-spaces`` string), ``geometry`` (string:float dictionary with the  ``centerx``, ``centery``, ``energy``, ``pixelsizex``, ``pixelsizey``, ``detdistance`` keywords)

e.g.

.. code-block:: console

   lavue -u q+roi+proj -s test --tool-configuration \{\"rois_number\":2,\"aliases\":[\"pilatus_roi1\",\"polatus_roi2\"],\"mapping\":\"sum\",\"rows\":\"10:200:5\",\"columns\":\"50:150\",\"units\":\"angles\",\"geometry\":\{\"centerx\":123.4,\"centery\":93.4,\"pixelsizex\":70,\"pixelsizey\":70.2,\"energy\":5050,\"detdistance\":50.5\}\} --start

A JSON dictionary with the **tool results** is passed to the **LavueController** or/and to **user functions plugins**. It contains the following keys:

``tool`` : "q+roi+proj", ``imagename`` (string), ``timestamp`` (float), ``xx`` ([float, .., float]), ``sx`` ([float, .., float]), ``yy`` ([float, .., float]), ``sy`` ([float, .., float]), ``xscale`` (float), ``xslice`` ([float, float, float]), ``yscale`` (float), ``yslice`` ([float, float, float]), fun (str) [i.e. "mean" or "sum"]

.. |br| raw:: html

     <br>
