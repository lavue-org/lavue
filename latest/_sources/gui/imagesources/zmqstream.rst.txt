.. _zmq-stream:

ZMQ stream
==========

Images from a simple ZMQ server, e.g. lavuezmqstreamfromtango SERVER. It is used to send *post-processed images*

.. figure:: ../../_images/zmqstreamlavue.png


The **ZMQ Stream** image source frame contains the following fields:

*    **ZMQ Server:** selects the zmq server host and zmq  data port. Moreover the user can also select the required zmq topic and ZMQ HWM (how many images is in buffer), i.e. `host:port[/topic[/HWM]]` or `host:port[:topic[:HWM]]` (with the ZMQ configuration colon separator)
*    **DataSource:** name of zmq topic. Possible datasources can be predefined in the configuration or sent in ZMQ metadata.
*    **Status:** shows the connection status. It also displays a port of ZMQ security stream if it is enabled.
*    **Start/Stop** button to launch or interrupt image querying

The **ZMQ Stream** metadata part can also contain other informations like axes labels or axes start position and scale.

.. |br| raw:: html

     <br>
