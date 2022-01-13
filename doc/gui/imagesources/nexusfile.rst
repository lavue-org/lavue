.. _nexus-file:

NeXus File
==========

Images from a NeXus/HDF5 file, e.g. written in the SWMR mode (Single-Writer-Multiple-Reader) or after the scan.

.. figure:: ../../_images/nexuslavue.png

The **NeXus File** image source frame contains the following fields:

*    **File:** nexus file name with its full path e.g. `/gpfs/current/H2O_test.nxs`
*    **Field:** nexus field with its path inside nexus file e.g. `/entry12345/data/lambda`
*    **Stacking:** stacking dimension of images inside a 3D field. Usually, for Nexus format is 0, i.e. the first dimension.
*    **Frame:** nexus field frame to display. The default value is  -1, i.e. the last frame.
*    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
*    **Start/Stop** button to launch or interrupt image querying

.. |br| raw:: html

     <br>
