.. _range-window:

Range Window and Down-Sampling
==============================

.. figure:: ../_images/lavue-rangewindow.png

The **Range Window and Down-Sampling** widget allows to reduce the displayed image by selecting its **x** and **y slices** in python notation.

Moreover,  the user can reduce the image by applying down-sampling with a specific factor and a reduction function.

*    **Slices:** x,y numpy-like slices
*    **DS Factor:** down-sampling factor, i.e. 5 means: a 5x5 pixel block is reduced to 1 pixel.
*    **DS Reduction:** down-sampling reduction function, i.e. `max`, `min`, `mean` or `sum` .
