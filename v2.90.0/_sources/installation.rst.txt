
Installation
------------

LaVue requires the following python packages: ``qt5/qt4``  ``pyqtgraph``  ``numpy``  ``zmq``  ``scipy``

It is also recommended to install: ``pytango``  ``hidra``  ``pil``  ``fabio``  ``requests``  ``h5py``  ``pninexus``  ``nxstools``


From sources
""""""""""""

Download the latest LaVue version from https://github.com/lavue-org/lavue

Extract sources and run

.. code-block:: console

   $ python setup.py install

The ``setup.py`` script may need: ``setuptools``  ``sphinx``  ``numpy``  ``pytest`` python packages as well as ``qtbase5-dev-tools`` or ``libqt4-dev-bin``.

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
