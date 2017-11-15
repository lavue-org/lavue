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


from PyQt4 import QtGui


class StatisticsWidget(QtGui.QGroupBox):

    """
    Display some general image statistics.
    """

    def __init__(self, parent=None):
        super(StatisticsWidget, self).__init__(parent)

        self.setTitle("Image statistics")
        layout = QtGui.QGridLayout()

        self.scaling = "sqrt"

        scalingLabel = QtGui.QLabel("Scaling:")
        self.scaleLabel = QtGui.QLabel(self.scaling)

        maxlabel = QtGui.QLabel("maximum: ")
        meanlabel = QtGui.QLabel("mean: ")
        variancelabel = QtGui.QLabel("variance: ")
        self.roilabel = QtGui.QLabel("roi   sum: ")

        self.maxVal = QtGui.QLineEdit("Not set")
        self.meanVal = QtGui.QLineEdit("Not set")
        self.varVal = QtGui.QLineEdit("Not set")
        self.roiVal = QtGui.QLineEdit("Not set")
        layout.addWidget(scalingLabel, 0, 0)
        layout.addWidget(self.scaleLabel, 0, 1)

        layout.addWidget(maxlabel, 1, 0)
        layout.addWidget(self.maxVal, 1, 1)
        layout.addWidget(meanlabel, 2, 0)
        layout.addWidget(self.meanVal, 2, 1)
        layout.addWidget(variancelabel, 3, 0)
        layout.addWidget(self.varVal, 3, 1)
        layout.addWidget(self.roilabel, 4, 0)
        layout.addWidget(self.roiVal, 4, 1)

        self.setLayout(layout)

    def update_stats(self, meanVal, maxVal, varVal, scaling,
                     roiVal=None, lrid=""):
        if self.scaling is not scaling:
            self.scaling = scaling
        self.scaleLabel.setText(self.scaling)
        self.meanVal.setText(meanVal)
        self.maxVal.setText(maxVal)
        self.varVal.setText(varVal)
        lrid = lrid or "roi  sum: "
        self.roilabel.setText("%s" % lrid)
        if roiVal is not None:
            self.roiVal.setText(roiVal)
