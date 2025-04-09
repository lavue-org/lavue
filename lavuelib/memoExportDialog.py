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

""" image display widget """

import pyqtgraph as _pg
from pyqtgraph import QtCore
import types
from pyqtgraph.GraphicsScene import exportDialog

try:
    from pyqtgraph import QtWidgets
except Exception:
    from pyqtgraph import QtGui as QtWidgets


class MemoPlotWidget(_pg.PlotWidget):

    """ Plot Widget with improved Export Dialog
    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) freeze clicked signal
    freezeClicked = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) clear clicked signal
    clearClicked = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) reset clicked signal
    resetClicked = QtCore.pyqtSignal()

    def __init__(self, parent=None, background='default', **kargs):
        _pg.PlotWidget.__init__(
            self, parent=parent, background=background, **kargs)
        sc = self.scene()
        sc.contextMenu[0].triggered.disconnect(sc.showExportDialog)
        sc.showExportDialog = types.MethodType(
            GraphicsScene_showExportDialog, sc)
        sc.contextMenu[0].triggered.connect(sc.showExportDialog)

        self.__menu = self.plotItem.vb.menu
        self.__separator = self.__menu.addSeparator()
        self.__freezeaction = QtWidgets.QAction(
            "Freeze", self.__menu)
        self.__menu.addAction(self.__freezeaction)
        self.__freezeaction.triggered.connect(self._freeze)
        self.__clearaction = QtWidgets.QAction(
            "Clear", self.__menu)
        self.__menu.addAction(self.__clearaction)
        self.__clearaction.triggered.connect(self._clear)
        self.__resetaction = QtWidgets.QAction(
            "Reset", self.__menu)
        self.__menu.addAction(self.__resetaction)
        self.__resetaction.triggered.connect(self._reset)
        self.showMenu()

    def _freeze(self):
        """ emits freezeClicked signal
        """
        self.freezeClicked.emit()

    def _clear(self):
        """ emits clearClicked signal
        """
        self.clearClicked.emit()

    def _reset(self):
        """ emits resetClicked signal
        """
        self.resetClicked.emit()

    def showMenu(self, freeze=False, clear=False, reset=False):
        """ shows freeze or/and clear action in the menu

        :param freeze: freeze show status
        :type freeze: :obj:`bool`
        :param clear: clear show status
        :type clear: :obj:`bool`
        :param reset: reset show status
        :type reset: :obj:`bool`
        """
        self.__freezeaction.setVisible(freeze)
        self.__clearaction.setVisible(clear)
        self.__resetaction.setVisible(reset)
        self.__separator.setVisible(freeze or clear or reset)


class MemoExportDialog(exportDialog.ExportDialog):

    """ ExportDialog with bookkeeping  parameters """

    def __init__(self, scene):
        exportDialog.ExportDialog.__init__(self, scene)
        self.dctparams = {}

    def exportFormatChanged(self, item, prev):
        if item is None:
            self.currentExporter = None
            self.ui.paramTree.clear()
            return
        if hasattr(item, "expClass"):
            expClass = item.expClass
        else:
            expClass = self.exporterClasses[str(item.text())]
        exp = expClass(item=self.ui.itemTree.currentItem().gitem)

        if prev:
            oldtext = str(prev.text())
            self.dctparams[oldtext] = self.currentExporter.parameters()
        newtext = str(item.text())
        if newtext in self.dctparams.keys():
            params = self.dctparams[newtext]
            exp.params = params
        else:
            params = exp.parameters()
            self.dctparams[newtext] = params

        if params is None:
            self.ui.paramTree.clear()
        else:
            self.ui.paramTree.setParameters(params)
        self.currentExporter = exp
        self.ui.copyBtn.setEnabled(exp.allowCopy)


def GraphicsScene_showExportDialog(self):
    """ dynamic replacement of GraphicsScene.showExportDialog
    """
    if self.exportDialog is None:
        self.exportDialog = MemoExportDialog(self)
    self.exportDialog.show(self.contextMenuItem)
