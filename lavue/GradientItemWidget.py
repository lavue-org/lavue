# Copyright (C) 2017  DESY, Christoph Rosemann, Notkestr. 85, D-22607 Hamburg
#
# lavue is an image viewing program for photon science imaging detectors.
# Its usual application is as a live viewer using hidra as data source.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation in  version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.
#
# Authors:
#     Christoph Rosemann <christoph.rosemann@desy.de>
#     Jan Kotanski <jan.kotanski@desy.de>
#

from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import GraphicsView
from pyqtgraph import GraphicsWidget
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.GradientEditorItem import GradientEditorItem
from pyqtgraph.graphicsItems.AxisItem import AxisItem
# from pyqtgraph.graphicsItems.GridItem import *

import numpy as np


class GradientItem(GraphicsWidget):

    """
    This is a blatant copy/rewrite of the HistogramLUTItem.
    Instead of a histogram and stuff it only provides a
      Gradient editor to define color lookup table for single-channel images
    """

    sigLookupTableChanged = QtCore.Signal(object)
    sigLevelsChanged = QtCore.Signal(object)
    sigLevelChangeFinished = QtCore.Signal(object)

    def __init__(self, image=None, fillHistogram=True):
        """
        If *image* (ImageItem) is provided, then the control will be
        automatically linked to the image and changes to the control
        will be immediately reflected in the image's appearance.
        By default, the histogram is rendered with a fill. For performance,
        set *fillHistogram* = False.
        """
        GraphicsWidget.__init__(self)
        self.lut = None
        self.imageItem = None

        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        self.vb = ViewBox()
        self.vb.setMaximumWidth(152)
        self.vb.setMinimumWidth(45)
        self.vb.setMouseEnabled(x=False, y=False)

        self.gradient = GradientEditorItem()
        # CR: this is  sooooo bad, but there is no function !?
        self.gradient.tickSize = 0
        self.gradient.setOrientation('right')
        self.gradient.loadPreset('highContrast')

        self.layout.addItem(self.gradient, 0, 0)
        self.axis = AxisItem(
            'right', linkView=self.vb, maxTickLength=12, showValues=True)
        self.layout.addItem(self.axis, 0, 1)

        self.range = None
        self.gradient.setFlag(self.gradient.ItemStacksBehindParent)

        self.vb.setFlag(self.gradient.ItemStacksBehindParent)

        self.gradient.sigGradientChanged.connect(self.gradientChanged)

        if image is not None:
            self.setImageItem(image)

    def paint(self, p, *args):
        pass

    def setImageItem(self, img):
        self.imageItem = img
        # send function pointer, not the result
        img.setLookupTable(self.getLookupTable)

    def gradientChanged(self):
        if self.imageItem is not None:
            if self.gradient.isLookupTrivial():
                self.imageItem.setLookupTable(None)
            else:
                # send function pointer, not the result
                self.imageItem.setLookupTable(
                    self.getLookupTable)

        self.lut = None
        self.sigLookupTableChanged.emit(self)

    def getLookupTable(self, img=None, n=None, alpha=None):
        if n is None:
            if img.dtype == np.uint8:
                n = 256
            else:
                n = 512
        if self.lut is None:
            self.lut = self.gradient.getLookupTable(n, alpha=alpha)
        return self.lut


class GradientItemWidget(GraphicsView):

    def __init__(self, parent=None,  *args, **kargs):
        background = kargs.get('background', 'default')
        GraphicsView.__init__(
            self, parent, useOpenGL=False, background=background)
        self.item = GradientItem(*args, **kargs)
        self.setCentralItem(self.item)
        self.setSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.setMinimumWidth(95)

    def sizeHint(self):
        return QtCore.QSize(115, 200)

    def __getattr__(self, attr):
        return getattr(self.item, attr)
