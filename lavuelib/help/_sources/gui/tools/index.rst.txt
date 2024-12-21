.. _special-tools:

Specialized Tools
=================


In the bottom-right corner `ComboBox` the user selects one of the **Specialized Image Tools**:

*    :ref:`Intensity <intensity>` - shows intensity of the selected pixels
*    :ref:`ROI <roi>` - selects Regions Of Interest and culculates a sum of their pixel intensities
*    :ref:`LineCut <linecut>` - selects Line Cuts and shows their 1d intensity plots
*    :ref:`Angle/Q <angleq>` - shows pixel coordinates in q-space or theta-angles
*    :ref:`MoveMotor <move-motor>` - moves the selected motors to the position pointed by mouse
*    :ref:`MeshScan <mesh-scan>` - performs sardana mesh scan on the selected ROI region
*    :ref:`1d-Plot <1d-plot>` - plots 1d-plots of the selected image rows
*    :ref:`Projections <projections>` - plots horizontal and vertical projections of the current image
*    :ref:`Q+ROI+Proj <q-roi-proj>` - combines :ref:`Angle/Q <angleq>`, :ref:`ROI <roi>` and :ref:`Projections <projections>`
*    :ref:`Maxima <maxima>` - points pixels with the highest intensity
*    :ref:`Parameters <parameters>` - reads and writes tango attributes to change detector settings
*    :ref:`Diffractogram <diffractogram>` - shows a result of azimuth integration on 1d plot
*    :ref:`TwoD-Fit <twodfit>` - fits two-dimensional  function tohe the current raw image

The **configuration** of tools can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or as a ``toolconfig`` variable in the ``LavueState`` attribute of :ref:`lavuecontroller`, e.g.

.. code-block:: python


         import tango
         import json

         lc = tango.DeviceProxy("p09/lavuecontroller/1")

	 lc.LavueState = json.dumps({"tool":"intensity", "toolconfig":'{"crosshair_locker":true}'})

.. toctree::
   :caption: Table of Contents
   :maxdepth: 2

   intensity
   roi
   linecut
   angleq
   movemotor
   meshscan
   onedplot
   projections
   qroiproj
   maxima
   parameters
   diffractogram
   twodfit
