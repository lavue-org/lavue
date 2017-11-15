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

import pyqtgraph as pg
import math
from pyqtgraph.graphicsItems.ROI import ROI


from PyQt4 import QtCore

from . import GradientItem as GI


class ImageDisplayWidget(pg.GraphicsLayoutWidget):

    currentMousePosition = QtCore.pyqtSignal(QtCore.QString)

    def __init__(self, parent=None):
        super(ImageDisplayWidget, self).__init__(parent)
        self.layout = self.ci
        self.crosshair_locked = False
        self.roienable = False
        self.roicoords = [[0, 0, 0, 0]]
        self.currentroi = 0
        self.data = None
        self.autoDisplayLevels = True
        self.displayLevels = [None, None]

        self.viewbox = self.layout.addViewBox(row=0, col=1)

        self.image = pg.ImageItem()
        self.viewbox.addItem(self.image)

        leftAxis = pg.AxisItem('left')
        leftAxis.linkToView(self.viewbox)
        self.layout.addItem(leftAxis, row=0, col=0)

        bottomAxis = pg.AxisItem('bottom')
        bottomAxis.linkToView(self.viewbox)
        self.layout.addItem(bottomAxis, row=1, col=1)

        self.graditem = GI.GradientItem()
        self.graditem.setImageItem(self.image)

        self.layout.addItem(self.graditem, row=0, col=2)

        self.layout.scene().sigMouseMoved.connect(self.mouse_position)
        self.layout.scene().sigMouseClicked.connect(self.mouse_click)

        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=(255, 0, 0))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=(255, 0, 0))
        self.viewbox.addItem(self.vLine, ignoreBounds=True)
        self.viewbox.addItem(self.hLine, ignoreBounds=True)

        self.roi = []
        self.roi.append(ROI(0, pg.Point(50, 50)))
        self.roi[0].addScaleHandle([1, 1], [0, 0])
        self.roi[0].addScaleHandle([0, 0], [1, 1])

        self.viewbox.addItem(self.roi[0])
        self.roi[0].hide()

    def addItem(self, item):
        self.image.additem(item)

    def addROI(self, coords=None):
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * len(self.roi)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt + sz]
            spnt = pg.Point(sz, sz)
        else:
            pnt = pg.Point(coords[0], coords[1])
            spnt = pg.Point(coords[2] - coords[0], coords[3] - coords[1])
        self.roi.append(ROI(pnt, spnt))
        self.roi[-1].addScaleHandle([1, 1], [0, 0])
        self.roi[-1].addScaleHandle([0, 0], [1, 1])
        self.viewbox.addItem(self.roi[-1])

        self.roicoords.append(coords)

    def removeROI(self):
        roi = self.roi.pop()
        roi.hide()
        self.viewbox.removeItem(roi)
        self.roicoords.pop()

    def updateImage(self, img=None):
        if(self.autoDisplayLevels):
            self.image.setImage(img, autoLevels=True)
        else:
            self.image.setImage(
                img, autoLevels=False, levels=self.displayLevels)
        self.data = img

    def updateGradient(self, name):
        self.graditem.setGradientByName(name)

    def mouse_position(self, event):
        try:
            mousePoint = self.image.mapFromScene(event)
            xdata = math.floor(mousePoint.x())
            ydata = math.floor(mousePoint.y())
            if not self.crosshair_locked:
                self.vLine.setPos(xdata + .5)
                self.hLine.setPos(ydata + .5)

            if self.data is not None:
                try:
                    intensity = self.data[math.floor(xdata), math.floor(ydata)]
                except Exception as e:
                    intensity = 0.
            else:
                intensity = 0.

            if not self.roienable:
                self.currentMousePosition.emit(
                    "x=%i, y=%i, intensity=%.2f" % (xdata, ydata, intensity))
            elif self.currentroi > -1:
                self.currentMousePosition.emit(
                    "%s" % self.roicoords[self.currentroi])
            else:
                self.currentMousePosition.emit("")

        except Exception as e:
            print "Warning: ", str(e)
            pass

    def mouse_click(self, event):

        mousePoint = self.image.mapFromScene(event.scenePos())

        xdata = mousePoint.x()
        ydata = mousePoint.y()

        # if double click: fix mouse crosshair
        # another double click releases the crosshair again
        if event.double():
            if not self.roienable:
                self.crosshair_locked = not self.crosshair_locked
                if not self.crosshair_locked:
                    self.vLine.setPos(xdata + .5)
                    self.hLine.setPos(ydata + .5)

    def setAutoLevels(self, autoLvls):
        if(autoLvls):
            self.autoDisplayLevels = True
        else:
            self.autoDisplayLevels = False

    def setDisplayMinLevel(self, level=None):
        if (level is not None):
            self.displayLevels[0] = level

    def setDisplayMaxLevel(self, level=None):
        if (level is not None):
            self.displayLevels[1] = level
