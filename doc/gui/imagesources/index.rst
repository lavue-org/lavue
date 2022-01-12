Image Sources and stitching images
==================================

The user can select in the **IMAGE SOURCES** combo-box  the following source types:

*    **Hidra** - image from a Hidra server, e.g. Pilatus, Perkin Elmer
*    **HTTP response** - image from an http response, e.g. Eiger
*    **Tango Attribute** - image from a tango attribute, e.g. Lambda, PCO, AGIPD, Jungfrau or LimaCCDs detectors
*    **Tango Events** - image from a tango attribute passed via tango events, e.g. LimaCCDs detectors
*    **Tango File** - image defined by file and directory tango attributes, e.g. Pilatus w/o Hidra
*    **DOOCS Property** - image from a doocs property, e.g.  FLASH detectors
*    **ZMQ Stream** - image from a simple ZMQ server, e.g. lavuezmqstreamfromtango SERVER
*    **Nexus File** - image from a Nexus/Hdf5 file, e.g. written with SWMR
*    **Tine Property** - image from a tine property, e.g. bpm camera
*    **Epics PV** - image from a Epics Process Variables
*    **ASAPO** - images from a ASAPO server, e.g. data from detectors or postprocessed data
*    **Test** - random test image

By enlarging a number of image sources in  the *expert* mode: 

.. code-block:: console
   
        Configuration -> General -> Number of image sources

the user  can **combine images** from different sources, i.e. different detectors or detector modules.


.. figure:: ../../_images/lavue-multiplesources.png

*    **Offset**: `x,y[,TRANSFORMATION]`  where `x`, `y` are position of the first pixel for a particular image source while optional `TRANSFORMATION` can be  `flip-up-down`, `flipud`, `fud`, `flip-left-right`, `fliplr`, `flr`, `transpose`, `t`, `rot90`, `r90`, `rot180`, `r180`, `r270`, `rot270`, `rot180+transpose`, `rot180t` or `r180t`
*    **Checkbox** in the tag widget allows for switch on/off the corresponding image source

**Start**/ **Stop** button is only at the first source but it applies to all image sources.

List of Image Sources
=====================

.. toctree::
   :maxdepth: 2

   hidra
   http
   tangoattr
   tangoevents
   tangofile
   doocsprop
   zmqstream
   nexusfile
   tineprop
   epicspv
   asapo
   test
