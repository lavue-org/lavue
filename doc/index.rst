.. lavuelib documentation master file, created by
   sphinx-quickstart on Thu Jan 25 15:05:39 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

  .. default-domain:: py

Live Image Viewer
=================

LaVue is a simple implementation of a live viewer front end.
It is supposed to show a live image view from xray-detectors at PETRA3 @ desy.de,
e.g. ``Pilatus``, ``Lambda``, ``Eiger``, ``PerkinElmer``, ``PCO``, ``LimaCCD``, and others.

.. figure:: _images/lavue.png

Authors: Christoph Rosemann <christoph.rosemann at desy.de>, Jan Kotański <jan.kotanski at desy.de>, André Rothkirch <andre.rothkirch at desy.de>


Contents
========

.. toctree::
   :maxdepth: 3

   installation
   start
   gui/index
   lavuecontroller
   lavuemonitor
   zmqserver
   filterplugins
   develop/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



Further reading
===============

More information can be found at: `LaVue
<https://confluence.desy.de/display/FSEC/LaVue+-+Live+Image+Viewer>`_

| ``lavuelib`` module API: https://lavue-org.github.io/lavue
| ``LavueController`` Tango Server API: https://lavue-org.github.io/lavue/doc_html
