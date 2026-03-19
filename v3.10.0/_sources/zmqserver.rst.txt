ZMQ Stream server examples
--------------------------


An example of ZMQ Stream server (lavuezmqstreamfromtango) which sends images from TANGO attribribute to lavue via a PICKLE protocol is deployed with the GUI.


It can be launched by, e.g.

.. code-block:: console

   $ lavuezmqstreamfromtango  --port 5535


Another example of ZMQ Stream server (lavuezmqstreamtest) which sends random images to lavue via a JSON protocol (from v1.27.1) can be launched by, e.g.

.. code-block:: console

   $ lavuezmqstreamtest  --port 5535


To get all possible command-line parameters

.. code-block:: console

   $ lavuezmqstreamfromtango -h

   usage: lavuezmqstreamfromtango [-h] [-g TIMEGAP] [-p PORT] [-t TOPIC]
				  [-n PREFIX] [-a ATTRIBUTE] [--no-dict]
				  [--debug]


   ZMQ Pickle test server


   optional arguments:

     -h, --help            show this help message and exit
     -g TIMEGAP, --time-gap TIMEGAP
			   maximal time gap in seconds (default: 0.1)
     -p PORT, --port PORT  zmq port (default: automatic)
     -t TOPIC, --topic TOPIC
			   zmq topic (default: first one from datasources)
     -n PREFIX, --name-prefix PREFIX
			   image name prefix
     -a ATTRIBUTE, --attribute ATTRIBUTE
			   tango attribute (default: sys/tg_test/1/double_image_ro)
     --no-dict             create zmq stream without dictionary
     --debug               debug mode

or

.. code-block:: console

   $ lavuezmqstreamtest -h


   usage: lavuezmqstreamtest [-h] [-g TIMEGAP] [-p PORT] [-t TOPIC]
				  [-n PREFIX] [--no-dict][--debug]

   ZMQ JSON test server

   optional arguments:

     -h, --help            show this help message and exit
     -g TIMEGAP, --time-gap TIMEGAP
			   maximal time gap in seconds (default: 0.1)
     -p PORT, --port PORT  zmq port (default: automatic)
     -t TOPIC, --topic TOPIC
			   zmq topic (default: first one from datasources)
     -n PREFIX, --name-prefix PREFIX
			   image name prefix
     --no-dict             create zmq stream without dictionary
     --debug               debug mode


On debian systems the above scripts are installed at `/usr/bin/lavuezmqstreamfromtango` .  Based on it the user can write its own servers.
