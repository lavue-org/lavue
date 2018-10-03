LaVue - Live Image Viewer
=========================

Authors: Christoph Rosemann <christoph.rosemann at desy.de>, Jan Kotański <jan.kotanski at desy.de>, André Rothkirch <andre.rothkirch at desy.de>

Introduction
------------

This is a simple implementation of a live viewer front end.
It is supposed to show a live image view from xray-detectors at PETRA3 @ desy.de,
e.g. ``Pilatus``, ``Lambda``, ``Eiger``, ``PerkinElmer``, ``PCO``, ``LimaCCD``, and others.

.. image:: https://github.com/jkotan/lavue/blob/develop/doc/_images/lavue.png?raw=true


Installation
------------

LaVue requires the following python packages: ``qt4  pyqtgraph  numpy  zmq  scipy``

It is also recommended to install: ``pytango  hidra  pil  fabio  requests  h5py  pni  nxstools``


From sources
""""""""""""

Download the latest LaVue version from https://github.com/jkotan/lavue

Extract sources and run

.. code-block:: console

   $ python setup.py install

The ``setup.py`` script may need: ``setuptools  sphinx  numpy  pytest`` python packages as well as ``libqt4-dev-bin``.

Debian packages
"""""""""""""""

Debian Stretch (and Jessie) packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code-block:: console

   $ sudo su
   $ wget -q -O - http://repos.pni-hdri.de/debian_repo.pub.gpg | apt-key add -

and then download the corresponding source list, e.g.

.. code-block:: console

   $ cd /etc/apt/sources.list.d

and

.. code-block:: console

   $ wget http://repos.pni-hdri.de/stretch-pni-hdri.list

or

.. code-block:: console

   $ wget http://repos.pni-hdri.de/jessie-pni-hdri.list

respectively.

Finally,

.. code-block:: console

   $ apt-get update
   $ apt-get install python-lavue

for python 2.7 version

.. code-block:: console

   $ apt-get update
   $ apt-get install python3-lavue

for python 3 version. Please notice that `HiDRA
<https://confluence.desy.de/display/hidra>`_ is not available for python 3 yet.

Start the Viewer
----------------

To start LaVue

.. code-block:: console

   $ lavue

for python 2.7 or

.. code-block:: console

   $ lavue3

for python 3.

Start the Viewer in the expert mode
"""""""""""""""""""""""""""""""""""

Changing LaVue  settings is available in the expert mode, i.e.

.. code-block:: console

   $ lavue -m expert

under an additional button: Configuration.

Launching options
"""""""""""""""""

To get all possible command-line parameters

.. code-block:: console

   $ lavue -h

Further reading
---------------

More information can be found at: `LaVue
<https://confluence.desy.de/display/FSEC/LaVue+-+Live+Image+Viewer>`_
