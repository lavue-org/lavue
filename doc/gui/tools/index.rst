Specialized Tools
=================


In the bottom-right corner `ComboBox` the user selects one of the **Specialized Image Tools**:

*    **Intensity** - shows intensity of the selected pixels
*    **ROI** - selects Regions Of Interest and culculates a sum of their pixel intensities
*    **LineCut** - selects Line Cuts and shows their 1d intensity plots
*    **Angle/Q** - shows pixel coordinates in q-space or theta-angles
*    **MoveMotor** - moves the selected motors to the position pointed by mouse
*    **MeshScan** - performs sardana mesh scan on the selected ROI region
*    **1d-Plot** - plots 1d-plots of the selected image rows
*    **Projections** - plots horizontal and vertical projections of the current image
*    **Q+ROI+Proj** - combines **Angle/Q, ROI** and Projections
*    **Maxima** - points pixels with the highest intensity
*    **Parameters** - reads and writes tango attributes to change detector settings
*    **Diffractogram** - shows a result of azimuth integration on 1d plot

.. toctree::
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
