.. _scaling:

Scaling and Display Levels
==========================

In **Display levels and colors** user sets mapping between image pixel intensities and displayed colors on the 2D plot.

.. figure:: ../_images/autolevels_lavue.png

*    **scaling:** `sqrt`, `linear` or `log` – basic intensity scale for 2D images
     applied to `Image Statistics/1D plot` or not  – depending on *Configuration*
*    **Levels:** maximum and minimum intensity displayed. It can be automatic or set by user
*    **Auto levels %:** switch to automatic levels settings. You can provide the levels as a cut factor in % of the highest pick.
*    **Bin edges**: bin edges algorithm for finding histogram levels
*    **Step**: step parameter for the bin edges algorithm for finding histogram levels
*    **Histogram**: set intensity levels and color gradients on histogram plot
*    **Color gradients**: 12 various basic settings with possibility to adjust with ticks

By clicking the right-mouse-button on the color gradient bar you can **save** or **remove** your current **customize color gradient** into the local configuration (only in the expert mode).

For multi-channel images user can select a separate color channel, a sum or mean of all color channels or an RGB view.

With Map images to color channels in  *Configuration/General* checked on the user can adjust intensity display levels for each image sources separately on **RGB histogram**, e.g.

.. code-block:: console

   $ lavue -s test\;tangoattr -c \;sys/tg_test/1/double_image_ro -i linear --channel rgb -l green -x

lunches lavue with two image sources: test and sys/tg_test/1/double_image_ro tango attribute

.. figure:: ../_images/lavue_rgbhistogram.png

The test image source in the red channel has the intensity maximal value ~30 times larger than the tango image source image.  With the RGB histogram lavue adjusts the intensity levels separately for the each color channel so both images are visible in one time.

To display RGB image channels with the **gradient color maps** set **Configuration -> General -> Image Display -> Image channels with gradient colors** i.e.

.. figure:: ../_images/lavue_multigradientcolors.png

Other option to make both image visible is to use the **WeightedSum** filter from lavuelib.plugins.filters which performs the weighted sum of all channel images. 
