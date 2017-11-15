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


import math

from PyQt4 import QtCore, QtGui

from . import imageDisplayWidget


class ImageWidget(QtGui.QWidget):

    """
    The part of the GUI that incorporates the image view.
    """

    roiCoordsChanged = QtCore.pyqtSignal()
    roiNrChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)

        self.nparray = None
        self.imageItem = None

        self.img_widget = imageDisplayWidget.ImageDisplayWidget(parent=self)
        self.currentroimapper = QtCore.QSignalMapper(self)
        self.roiregionmapper = QtCore.QSignalMapper(self)

        verticallayout = QtGui.QVBoxLayout()

        filenamelayout = QtGui.QHBoxLayout()

        filelabel = QtGui.QLabel("Image/File name: ")
        filenamelayout.addWidget(filelabel)
        self.filenamedisplay = QtGui.QLineEdit()
        filenamelayout.addWidget(self.filenamedisplay)
        self.cnfButton = QtGui.QPushButton("Configuration")
        filenamelayout.addWidget(self.cnfButton)

        verticallayout.addLayout(filenamelayout)
        verticallayout.addWidget(self.img_widget)

        self.pixelComboBox = QtGui.QComboBox()
        self.pixelComboBox.addItem("Intensity")
        self.pixelComboBox.addItem("ROI")

        pixelvaluelayout = QtGui.QHBoxLayout()
        self.pixellabel = QtGui.QLabel("Pixel position and intensity: ")

        self.infodisplay = QtGui.QLineEdit()
        self.infodisplay.setReadOnly(True)

        self.roiLabel = QtGui.QLabel("ROI alias(es): ")
        self.labelROILineEdit = QtGui.QLineEdit("")
        self.roiSpinBox = QtGui.QSpinBox()
        self.roiSpinBox.setMinimum(0)
        self.roiSpinBox.setValue(1)
        self.fetchROIButton = QtGui.QPushButton("Fetch")
        self.applyROIButton = QtGui.QPushButton("Apply")

        pixelvaluelayout.addWidget(self.pixellabel)
        pixelvaluelayout.addWidget(self.infodisplay)
        pixelvaluelayout.addWidget(self.roiLabel)
        pixelvaluelayout.addWidget(self.labelROILineEdit)
        pixelvaluelayout.addWidget(self.roiSpinBox)
        pixelvaluelayout.addWidget(self.applyROIButton)
        pixelvaluelayout.addWidget(self.fetchROIButton)
        pixelvaluelayout.addWidget(self.pixelComboBox)
        verticallayout.addLayout(pixelvaluelayout)

        self.setLayout(verticallayout)
        self.img_widget.currentMousePosition.connect(self.infodisplay.setText)

        self.roiregionmapper.mapped.connect(self.roiRegionChanged)
        self.currentroimapper.mapped.connect(self.currentROIChanged)
        self.img_widget.roi[0].sigHoverEvent.connect(self.currentroimapper.map)
        self.img_widget.roi[0].sigRegionChanged.connect(
            self.roiregionmapper.map)
        self.currentroimapper.setMapping(self.img_widget.roi[0], 0)
        self.roiregionmapper.setMapping(self.img_widget.roi[0], 0)

        self.roiSpinBox.valueChanged.connect(self.roiNrChanged)
        self.labelROILineEdit.textEdited.connect(self.updateROIButton)
        self.updateROIButton()

    def roiRegionChanged(self, rid):
        self.roiChanged()

    def currentROIChanged(self, rid):
        oldrid = self.img_widget.currentroi
        if rid != oldrid:
            self.img_widget.currentroi = rid
            self.roiCoordsChanged.emit()

    def updateROIButton(self):
        if not str(self.labelROILineEdit.text()).strip():
            self.applyROIButton.setEnabled(False)
        else:
            self.applyROIButton.setEnabled(True)

    def roiNrChanged(self, rid, coords=None):
        if coords:
            for i, crd in enumerate(self.img_widget.roi):
                if i < len(coords):
                    self.img_widget.roicoords[i] = coords[i]
                    self.img_widget.roi[i].setPos([coords[i][0], coords[i][1]])
                    self.img_widget.roi[i].setSize(
                        [coords[i][2] - coords[i][0],
                         coords[i][3] - coords[i][1]])
        while rid > len(self.img_widget.roi):
            # print("LEN %s" % len(self.img_widget.roi))
            if coords and len(coords) >= len(self.img_widget.roi):
                self.img_widget.addROI(coords[len(self.img_widget.roi)])
            else:
                self.img_widget.addROI()
            self.img_widget.roi[-1].sigHoverEvent.connect(
                self.currentroimapper.map)
            self.img_widget.roi[-1].sigRegionChanged.connect(
                self.roiregionmapper.map)
            self.currentroimapper.setMapping(
                self.img_widget.roi[-1],
                len(self.img_widget.roi) - 1)
            self.roiregionmapper.setMapping(
                self.img_widget.roi[-1],
                len(self.img_widget.roi) - 1)
        if rid == 0:
            self.img_widget.currentroi = -1
        elif self.img_widget.currentroi >= rid:
            self.img_widget.currentroi = 0
        while rid < len(self.img_widget.roi):
            self.currentroimapper.removeMappings(self.img_widget.roi[-1])
            self.roiregionmapper.removeMappings(self.img_widget.roi[-1])
            self.img_widget.removeROI()
        self.roiCoordsChanged.emit()
        self.roiSpinBox.setValue(rid)

    def roiChanged(self):
        try:
            rid = self.img_widget.currentroi
            state = self.img_widget.roi[rid].state
            ptx = int(math.floor(state['pos'].x()))
            pty = int(math.floor(state['pos'].y()))
            szx = int(math.floor(state['size'].x()))
            szy = int(math.floor(state['size'].y()))
            self.img_widget.roicoords[rid] = [ptx, pty, ptx + szx, pty + szy]
            self.roiCoordsChanged.emit()
        except Exception as e:
            print "Warning: ", str(e)

    def plot(self, array, name=None):
        if array is None:
            return
        if name is not None:
            self.filenamedisplay.setText(name)

        self.img_widget.updateImage(array)

    def setAutoLevels(self, autoLvls):
        self.img_widget.setAutoLevels(autoLvls)

    def setMinLevel(self, level=None):
        self.img_widget.setDisplayMinLevel(level)

    def setMaxLevel(self, level=None):
        self.img_widget.setDisplayMaxLevel(level)

    def changeGradient(self, name):
        self.img_widget.updateGradient(name)
