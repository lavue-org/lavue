# Copyright (C) 2017  DESY, Notkestr. 85, D-22607 Hamburg
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
#     Jan Kotanski <jan.kotanski@desy.de>
#     Christoph Rosemann <christoph.rosemann@desy.de>
#

""" Horizontal HistogramWidget """


import pyqtgraph as _pg
from pyqtgraph import QtCore, QtGui
import numpy as np
import logging

#: ( (:obj:`str`,:obj:`str`,:obj:`str`) )
#:         pg major version, pg minor verion, pg patch version
_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".")[:3] \
    if _pg.__version__ else ("0", "9", "0")

_pg.graphicsItems.GradientEditorItem.Gradients['reversegrey'] = {
    'ticks': [(0.0, (255, 255, 255, 255)),
              (1.0, (0, 0, 0, 255)), ], 'mode': 'rgb'}
_pg.graphicsItems.GradientEditorItem.Gradients['highcontrast'] = {
    'ticks': [(0.0, (0, 0, 0, 255)),
              (1.0, (255, 255, 0, 255)), ], 'mode': 'rgb'}
_pg.graphicsItems.GradientEditorItem.Gradients['spectrum'] = {
    'ticks': [(0.0, (255, 0, 255, 255)),
              (1.0, (255, 0, 0, 255))], 'mode': 'hsv'}
_pg.graphicsItems.GradientEditorItem.Gradients['spectrumclip'] = {
    'ticks': [(0.0, (255, 0, 255, 255)),
              (.99, (255, 0, 0, 255)),
              (1.0, (255, 255, 255, 255))], 'mode': 'hsv'}
# define two new gradients of choice
_pg.graphicsItems.GradientEditorItem.Gradients['inverted'] = {
    'ticks': [(0.0, (255, 255, 255, 255)),
              (1.0, (0, 0, 0, 255)), ], 'mode': 'rgb'}
_pg.graphicsItems.GradientEditorItem.Gradients['highcontrastclip'] = {
    'ticks': [(0.0, (255, 255, 255, 255)),
              (0.15, (0, 0, 0, 255)),
              (0.4, (255, 0, 0, 255)),
              (0.7, (255, 255, 0, 255)),
              (0.99, (255, 255, 255, 255)),
              (1.0, (0, 0, 255, 255)), ], 'mode': 'rgb'}


__all__ = ['HistogramHLUTWidget']


logger = logging.getLogger("lavue")


class HistogramHLUTWidget(_pg.widgets.GraphicsView.GraphicsView):

    """ Horizontal HistogramWidget """

    def __init__(self, parent=None, bins=None, step=None,
                 *args, **kargs):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        :param bins: bins edges algorithm for histogram, default: 'auto'
        :type bins: :obj:`str`
        :param step: data step for calculation of histogram levels,
                     default: 'auto'
        :type step: :obj:`str` or :obj:`int`
        :param args: HistogramHLUTItem parameters list
        :type args: :obj:`list` < :obj:`any`>
        :param kargs:  HistogramHLUTItem parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        background = kargs.pop('background', 'default')

        _pg.widgets.GraphicsView.GraphicsView.__init__(
            self, parent, useOpenGL=False, background=background)
        #: (:class:`HistogramHLUTItem`) histogram item
        self.item = HistogramHLUTItem(bins, step, *args, **kargs)
        self.setCentralItem(self.item)
        self.setSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        self.setMinimumWidth(95)

    def sizeHint(self):
        """ sets size hint
        """
        return QtCore.QSize(115, 200)

    def __getattr__(self, attr):
        """ gets attribute of HistogramHLUTItem
        :param attr: attribute name
        :type attr: :obj:`str`
        :returns: attribute value
        :rtype: :obj:`any`
        """
        return getattr(self.item, attr)

    def setAutoFactor(self, factor):
        """ sets auto level factor

        :param factor: auto level factor of maximal peak
        :type factor: :obj:`float`
        """
        self.item.autolevelfactor = factor

    def setBins(self, bins):
        """ sets bins edges algorithm for histogram

        :param channel: bins edges algorithm for histogram
        :type channel: :obj:`str`
        """
        self.item.setBins(bins)

    def setStep(self, step):
        """ sets image step data for algorithm of histogram

        :param channel: image step data for algorithm of histogram
        :type channel: :obj:`int`
        """
        self.item.setStep(step)


class GradientEditorItemWS(
        _pg.graphicsItems.GradientEditorItem.GradientEditorItem):

    """ gradient editor item with a signal on loadPreset """

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) minimum level changed signal
    sigNameChanged = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kargs):
        """ constructor

        :param args: GradientEditorItem parameters list
        :type args: :obj:`list` < :obj:`any`>
        :param kargs:  GradientEditorItem parameter dictionary
        :type kargs: :obj:`dict` < :obj:`str`, :obj:`any`>
        """
        self.__skipupdate = True
        _pg.graphicsItems.GradientEditorItem.GradientEditorItem.__init__(
            self, *args, **kargs)
        self.__skipupdate = False
        self.saveAction = QtGui.QAction('Save ...', self)
        self.removeAction = QtGui.QAction('Remove', self)

    def addMenuActions(self):
        """ add save/remove actions
        """

        self.menu.addAction(self.saveAction)
        self.menu.addAction(self.removeAction)

    def removeTick(self, tick, finish=True):
        """ removes ticks with hook

        :param tick: ticks to remove
        :type tick:  :obj:`list` < :obj:`any`>
        :param finish: finish remove flag
        :type finish: :obj:`bool`
        """
        if not self.__skipupdate:
            _pg.graphicsItems.GradientEditorItem.GradientEditorItem.\
                removeTick(
                    self, tick=tick, finish=finish)
        else:
            _pg.graphicsItems.GradientEditorItem.TickSliderItem.\
                removeTick(self, tick)
            if finish:
                # hook for a pyqtgraph bug
                # self.updateGradient()
                self.sigGradientChangeFinished.emit(self)

    def getCurrentGradient(self):
        """ provides dictionary with the current gradient

        :returns: gradient dictionary with:
           {"mode": <colorMode>,
            "ticks": [
                (<pos>, (<r>, <g>, <b>, <a>)),
                (<pos>, (<r>, <g>, <b>, <a>)),
                      ...
                (<pos>, (<r>, <g>, <b>, <a>)),
            ]
           }
        :rtype: :obj:`dict` < :obj:`str`:,  :obj:`str`: or :obj:`list`:>
        """
        tlist = self.listTicks()
        tdct = {}
        tdct['ticks'] = []
        tdct['mode'] = self.colorMode
        for tck, pos in tlist:
            clr = tck.color
            tdct['ticks'].append(
                (pos,
                 (clr.red(), clr.green(), clr.blue(), clr.alpha()))
                )
        return tdct

    def loadPreset(self, name):
        """ loads a predefined gradient and emits sigNameChanged

        :param name: gradient name
        :type name: :obj:`str`
        """
        _pg.graphicsItems.GradientEditorItem.GradientEditorItem.loadPreset(
            self, name)
        self.sigNameChanged.emit(name)


class HistogramHLUTItem(_pg.HistogramLUTItem):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) automatic levels changed signal
    autoLevelsChanged = QtCore.pyqtSignal(int)  # bool does not work...
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) minimum level changed signal
    sigNameChanged = QtCore.pyqtSignal(str)
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) save gradient requested
    saveGradientRequested = QtCore.pyqtSignal()
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) remove gradient requested
    removeGradientRequested = QtCore.pyqtSignal()

    """ Horizontal HistogramItem """

    def __init__(self, bins=None, step=None, image=None, fillHistogram=True,
                 expertmode=False):
        """ constructor

        :param bins: bins edges algorithm for histogram, default: 'auto'
        :type bins: :obj:`str`
        :param step: data step for calculation of histogram levels,
                     default: 'auto'
        :type step: :obj:`str` or :obj:`int`
        :param image: 2d image
        :type image: :class:`pyqtgraph.ImageItem`
        :param fillHistogram: histogram will be filled in
        :type fillHistogram: :obj:`bool`
        :param expertmode: expert mode flag
        :type expertmode: :obj:`bool`
        """
        _pg.graphicsItems.GraphicsWidget.GraphicsWidget.__init__(self)

        #: (:obj:`bool`) expert mode
        self.__expertmode = expertmode

        #: (:class:`numpy.ndarray`) look up table
        self.lut = None
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            #: (:class:`weakref.ref` or :class:`pyqtgraph.ImageItem`)
            #: weakref to image item or image item itself  (for < 0.9.8)
            self.imageItem = None
        else:
            self.imageItem = lambda: None

        #: (:obj: `bool`) rgb flag
        self.__rgb = False

        #: (:class:`PyQt5.QtGui.QGraphicsGridLayout`) grid layout
        self.layout = QtGui.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        #: (:class:`pyqtgraph.graphicsItems.ViewBox.ViewBox`) view box
        self.vb = _pg.graphicsItems.ViewBox.ViewBox()
        # self.vb.setMaximumHeight(152)
        self.vb.setMinimumHeight(45)
        self.vb.setMouseEnabled(x=True, y=False)
        # self.vb.setMouseEnabled(x=False, y=True)

        #: (:class:`GradientEditorItemWS`) gradient editor item with a signal
        self.gradient = GradientEditorItemWS()
        if self.__expertmode:
            self.gradient.addMenuActions()
        self.gradient.setOrientation('bottom')
        self.gradient.loadPreset('grey')
        #: (:obj:`list`) buffer for removed gradients
        self.__oldgradient = []
        #: (:class:`pyqtgraph.graphicsItems.LinearRegionItem.LinearRegionItem`)
        #:    linear region item
        self.region = _pg.graphicsItems.LinearRegionItem.LinearRegionItem(
            [0, 1],
            _pg.graphicsItems.LinearRegionItem.LinearRegionItem.Vertical)
        self.region.setZValue(1000)
        self.vb.addItem(self.region)

        #: (:class:`pyqtgraph.graphicsItems.AxisItem.AxisItem`) axis item
        self.axis = _pg.graphicsItems.AxisItem.AxisItem(
            'top', linkView=self.vb, maxTickLength=-10, showValues=False)

        self.layout.addItem(self.axis, 0, 0)
        self.layout.addItem(self.vb, 1, 0)
        self.layout.addItem(self.gradient, 2, 0)
        self.range = None

        self.autolevelfactor = None
        self.__step = step or 'auto'
        self.__bins = bins or 'auto'
        self.gradient.setFlag(self.gradient.ItemStacksBehindParent)
        self.vb.setFlag(self.gradient.ItemStacksBehindParent)

        self.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.gradient.sigNameChanged.connect(self._emitSigNameChanged)
        self.gradient.saveAction.triggered.connect(
            self._emitSaveGradientRequested)
        self.gradient.removeAction.triggered.connect(
            self._emitRemoveGradientRequested)
        self.region.sigRegionChanged.connect(self.regionChanging)
        self.region.sigRegionChangeFinished.connect(self.regionChanged)
        self.vb.sigRangeChanged.connect(self.viewRangeChanged)

        self.plot = _pg.graphicsItems.PlotDataItem.PlotDataItem()
        self.plots = [self.plot]
        # self.plot.dataBounds(1, 0.9)
        # self.plot.dataBounds(0, 0.9)
        self.levelMode = 'mono'
        self.fillHistogram(fillHistogram)

        self.vb.addItem(self.plot)
        self.autoHistogramRange()

        if image is not None:
            self.setImageItem(image)
        # self.background = None

    def setRGB(self, rgb):
        """ sets rgb flag

        :param rgb: rgb lag
        :type rgb: :obj:`bool`
        """
        self.__rgb = rgb

    def gradientChanged(self):
        """ gradient changed with rgb
        """
        if self.__rgb:
            self.lut = None
            self.sigLookupTableChanged.emit(self)
        else:
            _pg.HistogramLUTItem.gradientChanged(self)

    def resetGradient(self):
        """ resets gradient widget
        """
        self.gradient.sigGradientChanged.disconnect(self.gradientChanged)
        self.gradient.sigNameChanged.disconnect(self._emitSigNameChanged)
        self.gradient.saveAction.triggered.disconnect(
            self._emitSaveGradientRequested)
        self.gradient.removeAction.triggered.disconnect(
            self._emitRemoveGradientRequested)
        self.gradient.hide()
        if hasattr(self.gradient, "prepareGeometryChange"):
            self.gradient.prepareGeometryChange()
        self.layout.removeItem(self.gradient)
        self.gradient.close()
        self.__oldgradient.append(self.gradient)
        self.gradient = GradientEditorItemWS()
        if self.__expertmode:
            self.gradient.addMenuActions()
        self.gradient.setOrientation('bottom')
        self.gradient.loadPreset('grey')
        self.layout.addItem(self.gradient, 2, 0)

        self.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.gradient.sigNameChanged.connect(self._emitSigNameChanged)
        self.gradient.saveAction.triggered.connect(
            self._emitSaveGradientRequested)
        self.gradient.removeAction.triggered.connect(
            self._emitRemoveGradientRequested)

    @QtCore.pyqtSlot(str)
    def _emitSigNameChanged(self, name):
        """ emits SigNameChanged

        :param name: gradient name
        :type name: :obj:`str`
        """
        self.sigNameChanged.emit(name)

    @QtCore.pyqtSlot()
    def _emitSaveGradientRequested(self):
        """ emits saveGradientRequested
        """
        self.saveGradientRequested.emit()

    @QtCore.pyqtSlot()
    def _emitRemoveGradientRequested(self):
        """ emits removeGradientRequested
        """
        self.removeGradientRequested.emit()

    def setBins(self, bins):
        """ sets bins edges algorithm for histogram

        :param channel: bins edges algorithm for histogram
        :type channel: :obj:`str`
        """
        self.__bins = bins

    def setStep(self, step):
        """ sets image step data for algorithm of histogram

        :param channel: image step data for algorithm of histogram
        :type channel: :obj:`int`
        """
        try:
            if self.__step:
                self.__step = int(step)
            else:
                self.__step = "auto"
        except Exception:
            self.__step = "auto"

    def setGradientByName(self, name):
        """ sets gradient by name

        :param name: gradient name
        :type name: :obj:`str`
        """
        try:
            self.gradient.loadPreset(str(name))
        except Exception:
            self.gradient.loadPreset("highcontrast")

    def paint(self, p, *args):
        """ paints the histogram item

        :param p: QPainter painter
        :type p: :class:`PyQt5.QtGui.QPainter`
        :param args: paint argument
        :type args: :obj:`list` < :obj:`any`>
        """

        pen = self.region.lines[0].pen
        rgn = self.getLevels()
        p1 = self.vb.mapFromViewToItem(
            self, _pg.Point(rgn[0], self.vb.viewRect().center().y()))
        p2 = self.vb.mapFromViewToItem(
            self, _pg.Point(rgn[1], self.vb.viewRect().center().y()))
        gradRect = self.gradient.mapRectToParent(
            self.gradient.gradRect.rect())
        for pen in [_pg.functions.mkPen('k', width=3), pen]:
            p.setPen(pen)
            p.drawLine(p1, gradRect.topLeft())
            p.drawLine(p2, gradRect.topRight())
            p.drawLine(gradRect.topLeft(), gradRect.bottomLeft())
            p.drawLine(gradRect.topRight(), gradRect.bottomRight())

    def setHistogramRange(self, mn, mx, padding=0.1):
        """sets the Y range on the histogram plot. This disables auto-scaling.

        :param mn: minimum range level
        :type mn: :obj:`float`
        :param mx: maximum range level
        :type mx: :obj:`float`
        :param padding: histogram padding
        :type padding: :obj:`float`
        """
        self.vb.enableAutoRange(self.vb.XAxis, False)
        self.vb.setYRange(mn, mx, padding)

    def __imageItem(self):
        """ provides imageItem independent of the pyqtgraph version

        :returns: image item
        :rtype: :class:`pyqtgraph.ImageItem`

        """
        if _VMAJOR == '0' and int(_VMINOR) < 10 and int(_VPATCH) < 9:
            #: (:class:`weakref.ref` or :class:`pyqtgraph.ImageItem`)
            #: weakref to image item or image item itself  (for < 0.9.8)
            return self.imageItem
        else:
            return self.imageItem()

    def getFactorRegion(self):
        """ provides auto levels calculated from autofactor

        :returns: minlevel, maxlevel
        :rtype: (float, float)

        """

        hx = None
        hy = None
        if self.autolevelfactor is not None:
            try:
                hx, hy = self.__imageItem().getHistogram(
                    step=self.__step, bins=self.__bins)
            except Exception as e:
                logger.warning(str(e))
                # print(str(e))
            if hy is not None and hx is not None and hx.any() and hy.any():
                if abs(hx[0]) < 1.e-3 or abs(hx[0]+2.) < 1.e-3:
                    hx = hx[1:]
                    hy = hy[1:]
                if hx.any() and hy.any():
                    hmax = max(hy)
                    hmin = self.autolevelfactor*hmax/100.
                    mn, mx = self.__imageItem().levels[:2]
                    indexes = np.where(hy >= hmin)
                    ind1 = indexes[0][0]
                    ind2 = indexes[-1][-1]
                    return hx[ind1], hx[ind2]
        return None, None

    def imageChanged(self, autoLevel=False, autoRange=False):
        """ overload imageChange method

        :param autoLevel: auto level flag
        :type autoLevel: :obj:`bool`
        :param autoRange: auto range flag
        :type autoRange: :obj:`bool`
        """

        mn, mx = self.__imageItem().levels[:2]
        hx = None
        hy = None
        if self.autolevelfactor is not None:
            try:
                hx, hy = self.__imageItem().getHistogram(
                    step=self.__step, bins=self.__bins)
            except Exception as e:
                logger.warning(str(e))
                # print(str(e))
            if hy is not None and hx is not None and hx.any() and hy.any():
                if abs(hx[0]) < 1.e-3 or abs(hx[0]+2.) < 1.e-3:
                    hhx = hx[1:]
                    hhy = hy[1:]
                else:
                    hhx = hx
                    hhy = hy
                if hhx.any() and hhy.any():
                    hmax = max(hhy)
                    hmin = self.autolevelfactor * hmax / 100.
                    mn, mx = self.__imageItem().levels[:2]
                    indexes = np.where(hhy >= hmin)
                    ind1 = indexes[0][0]
                    ind2 = indexes[-1][-1]
                    self.region.setRegion([hhx[ind1], hhx[ind2]])
                    _pg.graphicsItems.HistogramLUTItem.HistogramLUTItem.\
                        imageChanged(
                            self, autoLevel=False, autoRange=autoRange)
                    return
        try:
            # _pg.graphicsItems.HistogramLUTItem.HistogramLUTItem.\
            #     imageChanged(
            #         self, autoLevel=autoLevel, autoRange=autoRange)
            h = self.imageItem().getHistogram(
                step=self.__step, bins=self.__bins)
            if h[0] is None:
                return
            self.plot.setData(*h)
            if autoLevel:
                mn = h[0][0]
                mx = h[0][-1]
                self.region.setRegion([mn, mx])
        except Exception as e:
            logger.warning(str(e))
            # print(str(e))
