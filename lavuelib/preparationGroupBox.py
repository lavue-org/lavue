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

""" preparationbox widget """

from pyqtgraph import QtGui

from . import transformationsWidget
from . import maskWidget
from . import highValueMaskWidget
from . import bkgSubtractionWidget


class QHLine(QtGui.QFrame):
    """ horizontal line
    """

    def __init__(self):
        """ constructor
        """
        QtGui.QFrame.__init__(self)

        self.setFrameShape(QtGui.QFrame.HLine)
        self.setFrameShadow(QtGui.QFrame.Sunken)


class PreparationGroupBox(QtGui.QGroupBox):
    """ colection of image preperation widgets
    """

    def __init__(self, parent=None, settings=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param settings: lavue configuration settings
        :type settings: :class:`lavuelib.settings.Settings`
        """
        QtGui.QGroupBox.__init__(self, parent)
        self.setTitle("Image preparation")

        #: (:obj:`bool`) show mask widget
        self.__mask = True
        #: (:obj:`bool`) show highvaluemask widget
        self.__highvaluemask = True
        #: (:obj:`bool`) show background subtraction widget
        self.__bkgsub = True
        #: (:obj:`bool`) show transformations widget
        self.__trans = True
        #: (:obj:`bool`) show scalar factors
        self._subsf = False

        #: (:class:`lavuelib.maskWidget.Maskwidget`) mask widget
        self.maskWidget = maskWidget.MaskWidget(
            parent=self, settings=settings)
        #: (:class:`lavuelib.maskWidget.Maskwidget`) mask widget
        self.highValueMaskWidget = highValueMaskWidget.HighValueMaskWidget(
            parent=self, settings=settings)
        #: (:class:`lavuelib.bkgSubtractionWidget.BkgSubtractionWidget`)
        #  background subtrantion widget
        self.bkgSubWidget = bkgSubtractionWidget.BkgSubtractionWidget(
            parent=self, settings=settings)
        self.__hline = QHLine()
        #: (:class:`lavuelib.transformationsWidget.TransformationsWidget`)
        #  transformations widget
        self.trafoWidget = transformationsWidget.TransformationsWidget(
            parent=self)

        vlayout = QtGui.QVBoxLayout()
        vlayout.addWidget(self.bkgSubWidget)
        vlayout.addWidget(self.maskWidget)
        vlayout.addWidget(self.highValueMaskWidget)
        vlayout.addWidget(self.__hline)
        vlayout.addWidget(self.trafoWidget)

        self.setLayout(vlayout)

    def changeView(self, showmask=None, showsub=None, showtrans=None,
                   showhighvaluemask=None, showsubsf=None):
        """ show or hide widgets in the preparation colection

        :param showmask: mask widget shown
        :type showmask: :obj:`bool`
        :param showsub: subtraction widget shown
        :type showsub: :obj:`bool`
        :param showtrans: transformation widget shown
        :type showtrans: :obj:`bool`
        :param showhighvaluemask: mask widget shown
        :type showhighvaluemask: :obj:`bool`
        :param showsub: subtraction scaling widget shown
        :type showsub: :obj:`bool`
        """

        if showmask is True:
            self.__mask = True
            self.maskWidget.show()
        elif showmask is False:
            self.__mask = False
            self.maskWidget.hide()

        if showsub is True:
            self.__bkgsub = True
            self.bkgSubWidget.show()
        elif showsub is False:
            self.__bkgsub = False
            self.bkgSubWidget.hide()

        if showsubsf is True and showsub is True:
            self.__subsf = True
            self.bkgSubWidget.showScalingFactors(True)

        elif showsubsf is False:
            self.bkgSubWidget.showScalingFactors(False)

        if showtrans is True:
            self.__trans = True
            self.trafoWidget.show()
        elif showtrans is False:
            self.__trans = False
            self.trafoWidget.hide()

        if showhighvaluemask is True:
            self.__highvaluemask = True
            self.highValueMaskWidget.show()
        elif showhighvaluemask is False:
            self.__highvaluemask = False
            self.highValueMaskWidget.hide()

        masks = self.__bkgsub or self.__mask or self.__highvaluemask

        if self.__trans and masks:
            self.__hline.show()
        else:
            self.__hline.hide()

        if self.__trans or masks:
            self.show()
        else:
            self.hide()
