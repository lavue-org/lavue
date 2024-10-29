LaVue - Live Image Viewer
=========================

|github workflow|
|docs|
|Pypi Version|
|Python Versions|

.. |github workflow| image:: https://github.com/lavue-org/lavue/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/lavue-org/lavue/actions
   :alt:

.. |docs| image:: https://img.shields.io/badge/Documentation-webpages-ADD8E6.svg
   :target: https://lavue-org.github.io/lavue/index.html
   :alt:

.. |Pypi Version| image:: https://img.shields.io/pypi/v/lavue.svg
                  :target: https://pypi.python.org/pypi/lavue
                  :alt:

.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/lavue.svg
                     :target: https://pypi.python.org/pypi/lavue/
                     :alt:

Authors: Christoph Rosemann <christoph.rosemann at desy.de>, Jan Kotański <jan.kotanski at desy.de>, André Rothkirch <andre.rothkirch at desy.de>

Introduction
------------

This is a simple implementation of a live viewer front end.
It is supposed to show a live image view from xray-detectors at PETRA3 @ desy.de,
e.g. ``Pilatus``, ``Lambda``, ``Eiger``, ``PerkinElmer``, ``PCO``, ``LimaCCD``, and others.

.. image:: https://github.com/lavue-org/lavue/blob/develop/doc/_images/lavue.png?raw=true


Installation
------------

LaVue requires the following python packages: ``qt5/qt4  pyqtgraph  numpy  zmq  scipy``

It is also recommended to install: ``pytango  hidra  pil  fabio  requests  h5py  pni  nxstools``


From sources
""""""""""""

Download the latest LaVue version from https://github.com/lavue-org/lavue

Extract sources and run

.. code-block:: console

   $ python setup.py install

The ``setup.py`` script may need: ``setuptools  sphinx  numpy  pytest`` python packages as well as ``qtbase5-dev-tools`` or ``libqt4-dev-bin``.

Debian packages
"""""""""""""""

Debian `bookworm`, `bullseye`, `buster` or Ubuntu  `noble`, `jammy`, `oracular` packages can be found in the HDRI repository.

To install the debian packages, add the PGP repository key

.. code-block:: console

   $ sudo su
   $ curl -s http://repos.pni-hdri.de/debian_repo.pub.gpg  | gpg --no-default-keyring --keyring gnupg-ring:/etc/apt/trusted.gpg.d/debian-hdri-repo.gpg --import
   $ chmod 644 /etc/apt/trusted.gpg.d/debian-hdri-repo.gpg

and then download the corresponding source list, e.g.

.. code-block:: console

   $ cd /etc/apt/sources.list.d

and

.. code-block:: console

   $ wget http://repos.pni-hdri.de/bookworm-pni-hdri.list

or

.. code-block:: console

   $ wget http://repos.pni-hdri.de/bullseye-pni-hdri.list

or

.. code-block:: console

   $ wget http://repos.pni-hdri.de/noble-pni-hdri.list

or

.. code-block:: console

   $ wget http://repos.pni-hdri.de/jammy-pni-hdri.list

respectively.

Finally,

.. code-block:: console

   $ apt-get update
   $ apt-get install python3-lavue
   $ apt-get install lavue-controller

or

.. code-block:: console

   $ apt-get install lavue-controller3
   
for python 3 version (for older debian/ubuntu releases).

From pip
""""""""

To install it from pip you need to install pyqt5 in advance, e.g.

.. code-block:: console

   $ python3 -m venv myvenv
   $ . myvenv/bin/activate

   $ pip install PyQtWebKit

or

.. code-block:: console

   $ pip install pyqt5

or

.. code-block:: console

   $ pip install PyQt5==5.14

and then

.. code-block:: console


   $ pip install lavue

Moreover it is also good to install the following python packages:

.. code-block:: console

   $ pip install fabio
   $ pip install pillow
   $ pip install pyFAI
   $ pip install lavuefilters
   $ pip install pytango

Start the Viewer
----------------

To start LaVue

.. code-block:: console

   $ lavue

or

.. code-block:: console

   $ lavue3

for python 3 version (for older debian/ubuntu releases).

Start the Viewer in the expert mode
"""""""""""""""""""""""""""""""""""

Changing LaVue settings is available in the expert mode, i.e.

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

More information can be found at: `LaVue <https://lavue-org.github.io/lavue>`_

| ``Conflunce`` page: https://confluence.desy.de/display/FSEC/LaVue+-+Live+Image+Viewer
| ``LavueController`` Tango Server API: https://lavue-org.github.io/lavue/stable/doc_html
