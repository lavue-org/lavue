.. _1d-plot:

1d-Plot Tool
============

**1d-Plot Tool** plots 1d-plots of the selected image rows

.. figure:: ../../_images/1dplotlavue.png

*    **Rows to plot:** e.g. ``1,2,9:10`` or ``100:120:2``, ``ALL`` for all rows
*    **Labels:** rename labels of the 1d-plot curves
*    **X in the first row:** tread the first row as 1d X-axis
*    **Buffer size:** size of the buffer to collect one curve data in time
*    **Reset:** reset the curve buffer
*    **Collect/Stop:** start and stop collecting curve data

It works for **MCAs**.

The ***configuration** of the tool can be set with a JSON dictionary passed in the ``--tool-configuration`` option in command line or a toolconfig variable of ``LavueController.LavueState`` with the following keys:

``rows_to_plot`` (string), ``labels`` (list of strings), ``buffer_size`` (integer), ``collect`` (boolean), ``reset`` (boolean), ``1d_stretch`` (integer)

e.g.

.. code-block:: console

   lavue -u 1d-plot -s tangoattr\;tangoattr -c aspectro\;fspecto --tool-configuration \{\"rows_to_plot\":\"0,1\",\"1d_stretch\":1000,\"labels\":\[\"sample\ 1\"\,\"water\"]\} --start

.. |br| raw:: html

     <br>
