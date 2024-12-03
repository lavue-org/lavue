.. _diffractogram:

Diffractogram Tool
==================

**Diffractogram Tool** shows a result of azimuth integration on 1d plot

.. figure:: ../../_images/lavuediffractogram.png

*    **Calibration** loads pyFAI calibration files, e.g. in PONI format
*    **Range** defines the integration ranges
*    combobox with **Units** sets x-axis units of the 1d diffractogram plot
*    **Show/Stop** - switches on/off continuous mode of diffractogram update with each  image
*    **Next** - (re-)computes a diffractogram for the current image
*    combobox with a **Number** of diffractograms corresponding to different ranges

Ranges and 1d plots **colors** can be changed in the lavue Configuration by setting **Ranges and ROIs Colors**.

Also in the Configuration the user can change

*    **Diffractogram size:** number of points in the diffractogram
*    **Correct Solid Angle:** correct solid angle flag for diffractogram

A contour plot of diffractograms (collected in time) can be created with use of the **Buffering** widget

*    **Buffer size:** maximal number of diffractograms in the heat-map plot
*    **Reset:** reset the diffractogram buffer
*    **Collect/Stop:** start or stop collect diffractograms in the buffer
*    **Main plot:** select 2D-plot i.e. Image shows the original image,  **Buffer <?>**   shows a buffer for the ``<?>`` diffractogram range


The **configuration** of the tool can be set with a JSON dictionary passed in the  ``--tool-configuration``  option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``calibration`` (string), ``diff_number`` (integer), ``diff_ranges`` ( [azimuth_start, azimuth_end, radial_start, radial_end] for each diffractogram i.e.   lists of  four floats), ``diff_units`` ( ``"q [1/nm]"``, ``"q [1/A]"``, ``"2th [deg]"``, ``"2th [rad]"``, ``"r [mm]"``, ``"r [pixel]"`` string), ``buffer_size`` (integer), ``buffering`` (boolean), ``collect`` (boolean), ``show_diff`` (boolean), ``main_plot`` (image, buffer 1, buffer 2, buffer 3 or buffer 4 string)

e.g.

.. code-block:: console

   lavue -u diffractogram -s test --tool-configuration \{\"calibration\":\"test/images/eiger4n_al203_13.45kev.poni\",\"diff_number\":2,\"diff_ranges\":[[10,20,0,10],[-5,5,5,15]],\"diff_units\":\"r\ [mm]\",\"buffering\":true,\"buffer_size\":512\} --start

A JSON dictionary with the **tool results** is passed to the **LavueController** or/and to **user functions plugins**. It contains the following keys:

``tool`` : "diffractogram", ``imagename`` (string), ``timestamp`` (float), ``nrdiffs`` (int), ``calibration`` (str) [i.e a pyfai file name],  ``unit`` (str) [i.e. "q_nm^-1", "q_A^-1", "2th_deg", "2th_rad", "r_mm" or "r_pixel"], ``diff_%i`` ([[float, float], ..., [float, float]]) [i.e. "%i" goes from 1 to ``nrdiffs``], ``radial_range_%i`` ([float, float]) [i.e. "%i" goes from 1 to ``nrdiffs``], ``azimuth_range_%i`` ([float, float]) [i.e. "%i" goes from 1 to ``nrdiffs``], ``peaks_%i`` ([[float, ..., float], [float, ..., float]]) [i.e. "%i" goes from 1 to ``nrdiffs`` and it contains peak positions and  peak values lists]

.. |br| raw:: html

     <br>
