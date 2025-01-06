LaVue Monitor
-------------

An example of **monitor script** which fetches metadata from the ZMQ security stream is deployed with lavue GUI.


It can be **launched** via

.. code-block:: console

  $ lavuemonitor

To get all **possible** command-line **parameters**

.. code-block:: console

   $ lavuemonitor -h

   usage: lavuemonitor [-h] [-i MAXVAL] [-g TIMEGAP] [-c COMMAND] [-r] [-p PORT]
		       [-z HOST] [-t TOPIC] [--debug]

   ZMQ Client for laVue status

   optional arguments:
     -h, --help            show this help message and exit
     -i MAXVAL, --max-intensity MAXVAL
			   maximal pixel value (default: 1000.)
     -g TIMEGAP, --time-gap TIMEGAP
			   maximal time gap in seconds (default: 1.)
     -c COMMAND, --stop-command COMMAND
			   stop command
     -r, --raw             check raw image
     -p PORT, --port PORT  zmq port (default: automatic)

     -z HOST, --host HOST  zmq host (default: localhost)
     -t TOPIC, --topic TOPIC
			   zmq topic (default: 10001)
     --debug               debug mode

On debian systems it is installed at */usr/bin/lavuemonitor*.  **Based on** it the user can write its own scripts.
