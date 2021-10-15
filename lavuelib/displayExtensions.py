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
import numpy as np
import math
import json
import time
import logging
# import warnings
from pyqtgraph.graphicsItems.ROI import ROI, LineROI, Handle
from pyqtgraph.graphicsItems.IsocurveItem import IsocurveItem

_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".")[:3] \
    if _pg.__version__ else ("0", "9", "0")

logger = logging.getLogger("lavue")


class HandleWithSignals(Handle):
    """ handle with signals

    """
    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) hover event emitted
    hovered = QtCore.pyqtSignal()

    def __init__(self, pos, center, parent):
        """ constructor

        :param pos: position of handle
        :type pos: [float, float]
        :param center: center of handle
        :type center: [float, float]
        :param parent: roi object
        :type parent: :class:`pyqtgraph.graphicsItems.ROI.ROI`
        """
        pos = _pg.Point(pos)
        center = _pg.Point(center)
        if pos[0] != center[0] and pos[1] != center[1]:
            raise Exception(
                "Scale/rotate handles must have either the same x or y "
                "coordinate as their center point.")
        Handle.__init__(self, parent.handleSize, typ='sr',
                        pen=parent.handlePen, parent=parent)
        self.setPos(pos * parent.state['size'])

    def hoverEvent(self, ev):
        """ hover event

        :param ev: close event
        :type ev: :class:`pyqtgraph.QtCore.QEvent`:
        """
        Handle.hoverEvent(self, ev)
        self.hovered.emit()


class SimpleLineROI(LineROI):
    """ simple line roi """

    def __init__(self, pos1, pos2, width=0.00001, **args):
        """ constructor

        :param pos1: start position
        :type pos1: [float, float]
        :param pos2: end position
        :type pos2: [float, float]
        :param args: dictionary with ROI parameters
        :type args: :obj:`dict`<:obj:`str`, :obj:`any`>
        """
        pos1 = _pg.Point(pos1)
        pos2 = _pg.Point(pos2)
        d = pos2 - pos1
        ln = d.length()
        ang = _pg.Point(1, 0).angle(d)

        ROI.__init__(self, pos1, size=_pg.Point(ln, width), angle=ang, **args)
        h1pos = [0, 0.0]
        h1center = [1, 0.0]
        h2pos = [1, 0.0]
        h2center = [0, 0.0]
        vpos = [0.5, 1]
        vcenter = [0.5, 0]
        self.handle1 = HandleWithSignals(h1pos, h1center, self)
        self.handle2 = HandleWithSignals(h2pos, h2center, self)
        self.vhandle = HandleWithSignals(vcenter, vpos, self)
        self.addHandle(
            {'name': 'handle1', 'type': 'sr', 'center': h1center,
             'pos': h1pos, 'item': self.handle1})
        self.addHandle(
            {'name': 'handle2', 'type': 'sr', 'center': h2center,
             'pos': h2pos, 'item': self.handle2})
        self.addHandle(
            {'name': 'vhandle', 'type': 'sr', 'center': vcenter,
             'pos': vpos, 'item': self.vhandle})
        # self.handle1 = self.addScaleRotateHandle([0, 0.5], [1, 0.5])
        # self.handle2 = self.addScaleRotateHandle([1, 0.5], [0, 0.5])

    def getCoordinates(self):
        """ provides the roi coordinates

        :param trans: transposed flag
        :type trans: :obj:`bool`
        :returns: x1, y1, x2, y2 positions of the roi
        :rtype: [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`]
        """
        ang = self.state['angle']
        pos1 = self.state['pos']
        size = self.state['size']
        ra = ang * np.pi / 180.
        pos2 = pos1 + _pg.Point(
            size.x() * math.cos(ra),
            size.x() * math.sin(ra))
        return [pos1.x(), pos1.y(), pos2.x(), pos2.y(), size.y()]


class RegionItem(IsocurveItem):

    def __init__(self, points=None, pen='w', **args):
        """ constructor

        :param points: list of points
        :type points:  :obj:`list` < (float, float) >
        :param pen: qt pen
        :type pen: :class:`pyqtgraph.QtGui.QPen`
        :param args: more params
        :type args: :obj:`dict` <:obj:`str`, `any`>
        """
        IsocurveItem.__init__(self, points, 0, pen, None, **args)
        # if points and points[0] and points[0][0]:
        #     self.setPos(*points[0][0])

    def generatePath(self):
        """ generate QPainterPath
        """
        if self.data is None:
            self.path = None
            return

        self.path = _pg.QtGui.QPainterPath()
        # nopos = True
        for line in self.data:
            if line and len(line) > 1:
                self.path.moveTo(*line[0])
                # if nopos:
                #     self.setPos(*line[0])
                #     nopos = False
                for p in line[1:]:
                    self.path.lineTo(*p)


class DisplayExtension(QtCore.QObject):
    """ display extension for ImageDisplayWidget
    """
    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        QtCore.QObject.__init__(self)
        #: (:obj:`str`) extension name
        self.name = "none"
        #: (:class:`pyqtgraph.QtCore.QObject`) mainwidget
        self._mainwidget = parent
        #: (:obj:`bool`) enabled flag
        self._enabled = False
        #: (:obj:`float`) minimum refresh time in s
        self._refreshtime = 0.02

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """

    def transpose(self):
        """ transposes subwidget
        """

    def setRefreshTime(self, refreshtime):
        """ sets refresh time

        :param refreshtime: refresh time in seconds
        :type refreshtime: :obj:`float`
        """
        self._refreshtime = refreshtime

    def refreshTime(self):
        """ provides refresh time

        :returns: refresh time in seconds
        :rtype: :obj:`float`
        """
        return self._refreshtime

    def enabled(self):
        """ is extension enabled

        :returns: is extension enabled
        :rtype: :obj:`bool`
        """
        return self._enabled

    def coordinates(self):
        """ returns coordinates
        """
        return None, None

    def mouse_position(self, x, y):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        """

    def mouse_doubleclick(self, x, y, locked):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        :param locked: double click lock
        :type locked: bool
        """

    def mouse_click(self, x, y):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        """

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: str
        """


class ROIExtension(DisplayExtension):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "rois"

        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) current roi mapper
        self.__currentroimapper = QtCore.QSignalMapper(self)
        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) roi region mapper
        self.__roiregionmapper = QtCore.QSignalMapper(self)

        #: (:obj:`int`) current roi id
        self.__current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2 rois coordinates
        self.__coords = [[10, 10, 60, 60]]
        #: (:obj:`list` < (int, int, int) > ) list with roi colors
        self.__colors = []

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.TextItem`>)
        #:            list of roi widgets
        self.__roitext = []
        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:            list of roi widgets
        self.__roi = []
        self.__roi.append(ROI(0, _pg.Point(50, 50)))
        self.__roi[0].addScaleHandle([1, 1], [0, 0])
        self.__roi[0].addScaleHandle([0, 0], [1, 1])
        text = _pg.TextItem("1.", anchor=(1, 1))
        text.setParentItem(self.__roi[0])
        self.__roitext.append(text)
        self._mainwidget.viewbox().addItem(self.__roi[0])
        self.__roi[0].hide()
        self.setColors()

        self.__roiregionmapper.mapped.connect(self.changeROIRegion)
        self.__currentroimapper.mapped.connect(self._emitROICoordsChanged)
        self._getROI().sigHoverEvent.connect(
            self.__currentroimapper.map)
        self._getROI().sigRegionChanged.connect(
            self.__roiregionmapper.map)
        self.__currentroimapper.setMapping(self._getROI(), 0)
        self.__roiregionmapper.setMapping(self._getROI(), 0)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.rois is not None:
            self.__showROIs(parameters.rois)
            self._enabled = parameters.rois

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: str
        """
        return "intensity"

    def __addROI(self, coords=None):
        """ adds ROIs

        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if not coords or not isinstance(coords, list) or len(coords) != 4:
            pnt = 10 * len(self.__roi)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt + sz]
            spnt = _pg.Point(sz, sz)
        else:
            if not self._mainwidget.transformations()[0]:
                pnt = _pg.Point(coords[0], coords[1])
                spnt = _pg.Point(coords[2] - coords[0], coords[3] - coords[1])
            else:
                pnt = _pg.Point(coords[1], coords[0])
                spnt = _pg.Point(coords[3] - coords[1], coords[2] - coords[0])
        self.__roi.append(ROI(pnt, spnt))
        self.__roi[-1].addScaleHandle([1, 1], [0, 0])
        self.__roi[-1].addScaleHandle([0, 0], [1, 1])
        text = _pg.TextItem("%s." % len(self.__roi), anchor=(1, 1))
        text.setParentItem(self.__roi[-1])
        self.__roitext.append(text)
        self._mainwidget.viewbox().addItem(self.__roi[-1])

        self.__coords.append(coords)
        self.setColors()

    def __removeROI(self):
        """ removes the last roi
        """
        roi = self.__roi.pop()
        roi.hide()
        roitext = self.__roitext.pop()
        roitext.hide()
        self._mainwidget.viewbox().removeItem(roi)
        self.__coords.pop()

    def _getROI(self, rid=-1):
        """ get the given or the last ROI

        :param rid: roi id
        :type rid: :obj:`int`
        """
        if self.__roi and len(self.__roi) > rid:
            return self.__roi[rid]
        else:
            return None

    def __showROIs(self, status):
        """ shows or hides rois

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for roi in self.__roi:
                roi.show()
        else:
            for roi in self.__roi:
                roi.hide()

    def __addROICoords(self, coords):
        """ adds ROI coorinates

        :param coords: roi coordinates
        :type coords: :obj:`list`
                < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__roi):
                if i < len(coords):
                    self.__coords[i] = coords[i]
                    if not self._mainwidget.transformations()[0]:
                        crd.setPos([coords[i][0], coords[i][1]])
                        crd.setSize(
                            [coords[i][2] - coords[i][0],
                             coords[i][3] - coords[i][1]])
                    else:
                        crd.setPos([coords[i][1], coords[i][0]])
                        crd.setSize(
                            [coords[i][3] - coords[i][1],
                             coords[i][2] - coords[i][0]])

    def __calcROIsum(self, rid):
        """calculates the current roi sum

        :param rid: roi id
        :type rid: :obj:`int`
        :returns: sum roi value, roi id
        :rtype: (float, int)
        """
        if rid >= 0:
            image = self._mainwidget.rawData()
            if image is not None:
                if self._enabled:
                    if rid >= 0:
                        roicoords = self.__coords
                        if not self._mainwidget.transformations()[0]:
                            rcrds = list(roicoords[rid])
                            if self._mainwidget.rangeWindowEnabled():
                                tx, ty = self._mainwidget.descaledxy(
                                    rcrds[0], rcrds[1], useraxes=False)
                                if tx is not None:
                                    tx2, ty2 = self._mainwidget.descaledxy(
                                        rcrds[2], rcrds[3], useraxes=False)
                                    rcrds = [tx, ty, tx2, ty2]
                        else:
                            rc = roicoords[rid]
                            rcrds = [rc[1], rc[0], rc[3], rc[2]]
                            if self._mainwidget.rangeWindowEnabled():
                                ty, tx = self._mainwidget.descaledxy(
                                    rcrds[1], rcrds[0], useraxes=False)
                                if ty is not None:
                                    ty2, tx2 = self._mainwidget.descaledxy(
                                        rcrds[3], rcrds[2], useraxes=False)
                                    rcrds = [tx, ty, tx2, ty2]
                        for i in [0, 2]:
                            if rcrds[i] > image.shape[0]:
                                rcrds[i] = image.shape[0]
                            elif rcrds[i] < -i // 2:
                                rcrds[i] = -i // 2
                        for i in [1, 3]:
                            if rcrds[i] > image.shape[1]:
                                rcrds[i] = image.shape[1]
                            elif rcrds[i] < - (i - 1) // 2:
                                rcrds[i] = - (i - 1) // 2
                        roival = np.nansum(image[
                            int(rcrds[0]):(int(rcrds[2]) + 1),
                            int(rcrds[1]):(int(rcrds[3]) + 1)
                        ])
                    else:
                        roival = 0.
                else:
                    roival = 0.
                return roival, rid
            else:
                return 0., rid
        return None, None

    def calcROIsum(self):
        """calculates the current roi sum

        :returns: sum roi value, roi id
        :rtype: (float, int)
        """
        if self._enabled and self._getROI() is not None:
            rid = self.__current
            return self.__calcROIsum(rid)
        return None, None

    def calcROIsums(self):
        """ calculates all roi sums

        :returns: sum roi value, roi id
        :rtype: :obj:list < float >
        """
        if self._mainwidget.rawData() is None:
            return None
        return [self.__calcROIsum(rid)[0]
                for rid in range(len(self.__coords))]

    @QtCore.pyqtSlot(int)
    def changeROIRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            rid = self.__current
            roi = self._getROI(rid)
            if roi is not None:
                state = roi.state
                rcrds = [
                    state['pos'].x(),
                    state['pos'].y(),
                    state['pos'].x() + state['size'].x(),
                    state['pos'].y() + state['size'].y()]
                if not self._mainwidget.transformations()[0]:
                    ptx1 = int(math.floor(rcrds[0]))
                    pty1 = int(math.floor(rcrds[1]))
                    ptx2 = int(math.floor(rcrds[2]))
                    pty2 = int(math.floor(rcrds[3]))
                else:
                    pty1 = int(math.floor(rcrds[0]))
                    ptx1 = int(math.floor(rcrds[1]))
                    pty2 = int(math.floor(rcrds[2]))
                    ptx2 = int(math.floor(rcrds[3]))
                crd = [ptx1, pty1, ptx2, pty2]
                if self.__coords[rid] != crd:
                    self.__coords[rid] = crd
                    self.roiCoordsChanged.emit()
        except Exception as e:
            logger.warning(str(e))
            # print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _emitROICoordsChanged(self, rid):
        """ emits roiCoordsChanged signal

        :param rid: roi id
        :type rid: :obj:`int`
        """
        oldrid = self.__current
        if rid != oldrid:
            self.__current = rid
            self.roiCoordsChanged.emit()

    def updateROIs(self, rid, coords):
        """ update ROIs

        :param rid: roi id
        :type rid: :obj:`int`
        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.__addROICoords(coords)
        while rid > len(self.__roi):
            if coords and len(coords) >= len(self.__roi):
                self.__addROI(coords[len(self.__roi)])
            else:
                self.__addROI()
            self._getROI().sigHoverEvent.connect(self.__currentroimapper.map)
            self._getROI().sigRegionChanged.connect(self.__roiregionmapper.map)
            self.__currentroimapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
            self.__roiregionmapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
        if rid <= 0:
            self.__current = -1
        elif self.__current >= rid:
            self.__current = 0
        while self._getROI(max(rid, 0)) is not None:
            self.__currentroimapper.removeMappings(self._getROI())
            self.__roiregionmapper.removeMappings(self._getROI())
            self.__removeROI()
        self.__showROIs(self._enabled)

    def setColors(self, colors=None):
        """ sets colors

        :param colors: json list of roi colors
        :type colors: :obj:`str`
        :returns: change status
        :rtype: :obj:`bool`
        """
        force = False
        if colors is not None:
            colors = json.loads(colors)
            if not isinstance(colors, list):
                return False
            for cl in colors:
                if not isinstance(cl, list):
                    return False
                if len(cl) != 3:
                    return False
                for clit in cl:
                    if not isinstance(clit, int):
                        return False
        else:
            colors = self.__colors
            force = True
        if self.__colors != colors or force:
            self.__colors = colors
            defpen = (255, 255, 255)
            for it, roi in enumerate(self.__roi):
                clr = tuple(colors[it % len(colors)]) if colors else defpen
                roi.setPen(clr)
                if hasattr(self.__roitext[it], "setColor"):
                    self.__roitext[it].setColor(clr)
                else:
                    self.__roitext[it].color = _pg.functions.mkColor(clr)
                    self.__roitext[it].textItem.setDefaultTextColor(
                        self.__roitext[it].color)
        return True

    def roiCoords(self):
        """ provides rois coordinates

        :return: rois coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__coords

    def isROIsEnabled(self):
        """ provides flag rois enabled

        :return: roi enabled flag
        :rtype: :obj:`bool`
        """
        return self._enabled

    def currentROI(self):
        """ provides current roi id

        :return: roi id
        :rtype: :obj:`int`
        """
        return self.__current

    def transpose(self):
        """ transposes ROIs
        """
        for crd in self.__roi:
            pos = crd.pos()
            size = crd.size()
            crd.setPos([pos[1], pos[0]])
            crd.setSize([size[1], size[0]])


class CutExtension(DisplayExtension):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) cut coordinate changed signal
    cutCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "cuts"

        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) current cut mapper
        self.__currentcutmapper = QtCore.QSignalMapper(self)
        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) cut region mapper
        self.__cutregionmapper = QtCore.QSignalMapper(self)

        #: (:obj:`int`) current cut id
        self.__current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2, width rois coordinates
        self.__coords = [[10, 10, 60, 10, 0.00001]]

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:        list of cut widgets
        self.__cut = []
        self.__cut.append(SimpleLineROI([10, 10], [60, 10], pen='r'))
        self._mainwidget.viewbox().addItem(self.__cut[0])
        self.__cut[0].hide()

        self.__cutregionmapper.mapped.connect(self.changeCutRegion)
        self.__currentcutmapper.mapped.connect(self._emitCutCoordsChanged)
        self._getCut().sigHoverEvent.connect(
            self.__currentcutmapper.map)
        self._getCut().sigRegionChanged.connect(
            self.__cutregionmapper.map)
        self._getCut().handle1.hovered.connect(
            self.__currentcutmapper.map)
        self._getCut().handle2.hovered.connect(
            self.__currentcutmapper.map)
        self._getCut().vhandle.hovered.connect(
            self.__currentcutmapper.map)
        self.__currentcutmapper.setMapping(self._getCut().handle1, 0)
        self.__currentcutmapper.setMapping(self._getCut().handle2, 0)
        self.__currentcutmapper.setMapping(self._getCut().vhandle, 0)
        self.__currentcutmapper.setMapping(self._getCut(), 0)
        self.__cutregionmapper.setMapping(self._getCut(), 0)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.cuts is not None:
            self.__showCuts(parameters.cuts)
            self._enabled = parameters.cuts

    def __addCutCoords(self, coords):
        """ adds Cut coordinates

        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__cut):
                if i < len(coords):
                    self.__coords[i] = coords[i]
                    if not self._mainwidget.transformations()[0]:
                        crd.setPos([coords[i][0], coords[i][1]])
                        crd.setSize(
                            [coords[i][2] - coords[i][0],
                             coords[i][3] - coords[i][1]])
                    else:
                        crd.setPos([coords[i][1], coords[i][0]])
                        crd.setSize(
                            [coords[i][3] - coords[i][1],
                             coords[i][2] - coords[i][0]])

    def __addCut(self, coords=None):
        """ adds Cuts

        :param coords: cut coordinates
        :type coords: :obj:`list`
                  < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if not coords or not isinstance(coords, list) or len(coords) != 5:
            pnt = 10 * (len(self.__cut) + 1)
            sz = 50
            coords = [pnt, pnt, pnt + sz, pnt, 0.00001]

        if not self._mainwidget.transformations()[0]:
            self.__cut.append(SimpleLineROI(
                coords[:2], coords[2:4], width=coords[4], pen='r'))
        else:
            self.__cut.append(SimpleLineROI(
                [coords[1], coords[0]],
                [coords[3], coords[2]],
                width=coords[4], pen='r'))
        self._mainwidget.viewbox().addItem(self.__cut[-1])
        self.__coords.append(coords)

    def __removeCut(self):
        """ removes the last cut
        """
        cut = self.__cut.pop()
        cut.hide()
        self._mainwidget.viewbox().removeItem(cut)
        self.__coords.pop()

    def _getCut(self, cid=-1):
        """ get the given or the last Cut

        :param cid: roi id
        :type cid: :obj:`int`
        """
        if self.__cut and len(self.__cut) > cid:
            return self.__cut[cid]
        else:
            return None

    def __showCuts(self, status):
        """ shows or hides cuts

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for cut in self.__cut:
                cut.show()
        else:
            for cut in self.__cut:
                cut.hide()

    def cutData(self, cid=None):
        """ provides the current cut data

        :param cid: cut id
        :type cid: :obj:`int`
        :returns: current cut data
        :rtype: :class:`numpy.ndarray`
        """
        if cid is None:
            cid = self.__current
        if cid > -1 and len(self.__cut) > cid:
            cut = self._getCut(cid)
            if self._mainwidget.rawData() is not None:
                dt = cut.getArrayRegion(
                    self._mainwidget.rawData(),
                    self._mainwidget.image(),
                    axes=(0, 1))
                with np.warnings.catch_warnings():
                    np.warnings.filterwarnings(
                        'ignore', r'Mean of empty slice')
                    while dt.ndim > 1:
                        dt = np.nanmean(dt, axis=1)
                return dt
        return None

    def cutCoords(self):
        """ provides cuts coordinates

        :return: cuts coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__coords

    @QtCore.pyqtSlot(int)
    def changeCutRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            cid = self.__current
            crds = self._getCut(cid).getCoordinates()
            if not self._mainwidget.transformations()[0]:
                self.__coords[cid] = crds
            else:
                self.__coords[cid] = [
                    crds[1], crds[0], crds[3], crds[2], crds[4]]

            self.cutCoordsChanged.emit()
        except Exception as e:
            logger.warning(str(e))
            # print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _emitCutCoordsChanged(self, cid):
        """ emits cutCoordsChanged signal

        :param cid: cut id
        :type cid: :obj:`int`
        """
        oldcid = self.__current
        if cid != oldcid:
            self.__current = cid
            self.cutCoordsChanged.emit()

    def updateCuts(self, cid, coords):
        """ update Cuts

        :param cid: cut id
        :type cid: :obj:`int`
        :param coords: cut coordinates
        :type coords: :obj:`list` < [float, float, float, float] >
        """
        self.__addCutCoords(coords)
        while cid > len(self.__cut):
            if coords and len(coords) >= len(self.__cut):
                self.__addCut(coords[len(self.__cut)])
            else:
                self.__addCut()
            self._getCut().sigHoverEvent.connect(self.__currentcutmapper.map)
            self._getCut().sigRegionChanged.connect(self.__cutregionmapper.map)
            self._getCut().handle1.hovered.connect(self.__currentcutmapper.map)
            self._getCut().handle2.hovered.connect(self.__currentcutmapper.map)
            self._getCut().vhandle.hovered.connect(self.__currentcutmapper.map)
            self.__currentcutmapper.setMapping(
                self._getCut(), len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().handle1, len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().handle2, len(self.__cut) - 1)
            self.__currentcutmapper.setMapping(
                self._getCut().vhandle, len(self.__cut) - 1)
            self.__cutregionmapper.setMapping(
                self._getCut(), len(self.__cut) - 1)
        if cid <= 0:
            self.__current = -1
        elif self.__current >= cid:
            self.__current = 0
        while max(cid, 0) < len(self.__cut):
            self.__currentcutmapper.removeMappings(self._getCut())
            self.__currentcutmapper.removeMappings(self._getCut().handle1)
            self.__currentcutmapper.removeMappings(self._getCut().handle2)
            self.__cutregionmapper.removeMappings(self._getCut())
            self.__removeCut()

    def isCutsEnabled(self):
        """ provides flag cuts enabled

        :return: cut enabled flag
        :rtype: :obj:`bool`
        """
        return self._enabled

    def currentCut(self):
        """ provides current cut id

        :return: cut id
        :rtype: :obj:`int`
        """
        return self.__current

    def transpose(self):
        """ transposes Cuts
        """
        for crd in self.__cut:
            pos = crd.pos()
            size = crd.size()
            angle = crd.angle()
            ra = angle * np.pi / 180.
            crd.setPos(
                [pos[1] + math.sin(ra) * size[0],
                 pos[0] + math.cos(ra) * size[0]])
            crd.setAngle(270-angle)


class MeshExtension(DisplayExtension):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "mesh"

        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) current roi mapper
        self.__currentroimapper = QtCore.QSignalMapper(self)
        #: (:class:`pyqtgraph.QtCore.QSignalMapper`) roi region mapper
        self.__roiregionmapper = QtCore.QSignalMapper(self)

        #: (:obj:`int`) current roi id
        self.__current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2 rois coordinates
        self.__coords = [[10, 10, 60, 60]]
        #: (:obj:`list` < (int, int, int) > ) list with roi colors
        self.__colors = []

        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.TextItem`>)
        #:            list of roi widgets
        self.__roitext = []
        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:            list of roi widgets
        self.__roi = []
        self.__roi.append(ROI(0, _pg.Point(50, 50)))
        self.__roi[0].addScaleHandle([1, 1], [0, 0])
        self.__roi[0].addScaleHandle([0, 0], [1, 1])
        text = _pg.TextItem("1.", anchor=(1, 1))
        text.setParentItem(self.__roi[0])
        self.__roitext.append(text)
        self._mainwidget.viewbox().addItem(self.__roi[0])
        self.__roi[0].hide()

        self.__roiregionmapper.mapped.connect(self.changeROIRegion)
        self.__currentroimapper.mapped.connect(self._emitROICoordsChanged)
        self._getROI().sigHoverEvent.connect(
            self.__currentroimapper.map)
        self._getROI().sigRegionChanged.connect(
            self.__roiregionmapper.map)
        self.__currentroimapper.setMapping(self._getROI(), 0)
        self.__roiregionmapper.setMapping(self._getROI(), 0)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.mesh is not None:
            self.__showROIs(parameters.mesh)
            self._enabled = parameters.mesh

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: str
        """
        return "intensity"

    def _getROI(self, rid=-1):
        """ get the given or the last ROI

        :param rid: roi id
        :type rid: :obj:`int`
        """
        if self.__roi and len(self.__roi) > rid:
            return self.__roi[rid]
        else:
            return None

    def __showROIs(self, status):
        """ shows or hides rois

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for roi in self.__roi:
                roi.show()
        else:
            for roi in self.__roi:
                roi.hide()

    def __addROICoords(self, coords):
        """ adds ROI coorinates

        :param coords: roi coordinates
        :type coords: :obj:`list`
                < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if coords:
            for i, crd in enumerate(self.__roi):
                if i < len(coords):
                    self.__coords[i] = coords[i]
                    if not self._mainwidget.transformations()[0]:
                        crd.setPos([coords[i][0], coords[i][1]])
                        crd.setSize(
                            [coords[i][2] - coords[i][0],
                             coords[i][3] - coords[i][1]])
                    else:
                        crd.setPos([coords[i][1], coords[i][0]])
                        crd.setSize(
                            [coords[i][3] - coords[i][1],
                             coords[i][2] - coords[i][0]])

    @QtCore.pyqtSlot(int)
    def changeROIRegion(self, _=None):
        """ changes the current roi region
        """
        try:
            rid = self.__current
            roi = self._getROI(rid)
            if roi is not None:
                state = roi.state
                if not self._mainwidget.transformations()[0]:
                    ptx = state['pos'].x()
                    pty = state['pos'].y()
                    szx = state['size'].x()
                    szy = state['size'].y()
                else:
                    pty = state['pos'].x()
                    ptx = state['pos'].y()
                    szy = state['size'].x()
                    szx = state['size'].y()
                crd = [ptx, pty, ptx + szx, pty + szy]
                if self.__coords[rid] != crd:
                    self.__coords[rid] = crd
                    self.roiCoordsChanged.emit()
        except Exception as e:
            logger.warning(str(e))
            # print("Warning: %s" % str(e))

    @QtCore.pyqtSlot(int)
    def _emitROICoordsChanged(self, rid):
        """ emits roiCoordsChanged signal

        :param rid: roi id
        :type rid: :obj:`int`
        """
        oldrid = self.__current
        if rid != oldrid:
            self.__current = rid
            self.roiCoordsChanged.emit()

    def updateROIs(self, rid, coords):
        """ update ROIs

        :param rid: roi id
        :type rid: :obj:`int`
        :param coords: roi coordinates
        :type coords: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        self.__addROICoords(coords)
        while rid > len(self.__roi):
            if coords and len(coords) >= len(self.__roi):
                self.__addROI(coords[len(self.__roi)])
            else:
                self.__addROI()
            self._getROI().sigHoverEvent.connect(self.__currentroimapper.map)
            self._getROI().sigRegionChanged.connect(self.__roiregionmapper.map)
            self.__currentroimapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
            self.__roiregionmapper.setMapping(
                self._getROI(), len(self.__roi) - 1)
        if rid <= 0:
            self.__current = -1
        elif self.__current >= rid:
            self.__current = 0
        while self._getROI(max(rid, 0)) is not None:
            self.__currentroimapper.removeMappings(self._getROI())
            self.__roiregionmapper.removeMappings(self._getROI())
            self.__removeROI()
        self.__showROIs(self._enabled)

    def roiCoords(self):
        """ provides rois coordinates

        :return: rois coordinates
        :rtype: :obj:`list`
               < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        return self.__coords

    def isROIsEnabled(self):
        """ provides flag rois enabled

        :return: roi enabled flag
        :rtype: :obj:`bool`
        """
        return self._enabled

    def currentROI(self):
        """ provides current roi id

        :return: roi id
        :rtype: :obj:`int`
        """
        return self.__current

    def transpose(self):
        """ transposes ROIs
        """
        for crd in self.__roi:
            pos = crd.pos()
            size = crd.size()
            crd.setPos([pos[1], pos[0]])
            crd.setSize([size[1], size[0]])


class RegionsExtension(DisplayExtension):

    #: (:class:`pyqtgraph.QtCore.pyqtSignal`) region points changed signal
    regionPointsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "regions"

        #: (:obj:`int`) current roi id
        self.__current = 0
        #: (:obj:`list` < [int, int, int, int] > )
        #: x1,y1,x2,y2 regions coordinates
        self.__points = [[[(0, 0)]]]
        #: (:obj:`list` < (int, int, int) > ) list with region colors
        self.__colors = []

        #: ( (:obj:`int`, :obj:`int', :obj:`int`)) default pen color
        self.__defpen = (0, 255, 127)
        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.TextItem`>)
        #:            list of region widgets
        self.__regiontext = []
        #: (:obj:`list` <:class:`pyqtgraph.graphicsItems.ROI`>)
        #:            list of region widgets
        self.__region = []
        self.__region.append(RegionItem(self.__points[0],
                                        pen=_pg.mkPen('#00ff7f', width=2)))
        # text = _pg.TextItem("1.", anchor=(1, 1))
        # text.setParentItem(self.__region[0])
        # self.__regiontext.append(text)
        # clr = '#00ff7f'
        # if hasattr(self.__regiontext[0], "setColor"):
        #     self.__regiontext[0].setColor(clr)
        # else:
        #     self.__regiontext[0].color = _pg.functions.mkColor(clr)
        #     self.__regiontext[0].textItem.setDefaultTextColor(
        #         self.__regiontext[it].color)
        self._mainwidget.viewbox().addItem(self.__region[0])
        self.__region[0].hide()
        self.setColors()

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.regions is not None:
            self.__showRegions(parameters.regions)
            self._enabled = parameters.regions

    def scalingLabel(self):
        """ provides scaling label

        :returns:  scaling label
        :rtype: str
        """
        return "intensity"

    def __addRegion(self, points=None, rid=0):
        """ adds Regions

        :param points: region coordinates
        :type points: :obj:`list`
                 < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if not points or not isinstance(points, list):
            points = [[(0, 0)]]

        if self._mainwidget.transformations()[0]:
            points = [[(p[1], p[0]) for p in pt] for pt in points]
        clr = tuple(self.__colors[rid % len(self.__colors)]) \
            if self.__colors else self.__defpen
        self.__region.append(
            RegionItem(points, pen=_pg.mkPen(clr, width=2)))
        # text = _pg.TextItem("%s." % len(self.__region), anchor=(1, 1))
        # text.setParentItem(self.__region[-1])
        # self.__regiontext.append(text)
        self._mainwidget.viewbox().addItem(self.__region[-1])

        self.__points.append(points)
        # self.setColors()

    def __removeRegion(self):
        """ removes the last region
        """
        region = self.__region.pop()
        region.hide()
        # regiontext = self.__regiontext.pop()
        # regiontext.hide()
        self._mainwidget.viewbox().removeItem(region)
        self.__points.pop()

    def _getRegion(self, rid=-1):
        """ get the given or the last region

        :param rid: region id
        :type rid: :obj:`int`
        """
        if self.__region and len(self.__region) > rid:
            return self.__region[rid]
        else:
            return None

    def __showRegions(self, status):
        """ shows or hides regions

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            for rng in self.__region:
                rng.show()
        else:
            for rng in self.__region:
                rng.hide()

    def __addRegionPoints(self, points):
        """ adds region coorinates

        :param points: region coordinates
        :type points: :obj:`list`
                < [:obj:`float`, :obj:`float`, :obj:`float`, :obj:`float`] >
        """
        if points:
            for i, crd in enumerate(self.__region):
                if i < len(points):
                    self.__points[i] = points[i]
                    if self._mainwidget.transformations()[0]:
                        pnts = [[(p[1], p[0]) for p in pt] for pt in points[i]]
                    else:
                        pnts = points[i]
                    crd.setData(pnts)

    def updateRegions(self, points, rid=None):
        """ update Regions

        :param rid: rng id
        :type rid: :obj:`int`
        :param points: rng coordinates
        :type points: :obj:`list` <  :obj:`list` <  :obj:`list`
                  < (:obj:`float`, :obj:`float`) > > >
        """
        if rid is None:
            if points is None:
                points = []
            rid = len(points)
        self.__addRegionPoints(points)
        while rid > len(self.__region):
            if points and len(points) >= len(self.__region):
                self.__addRegion(points[len(self.__region)],
                                 rid=len(self.__region))
            else:
                self.__addRegion(rid=len(self.__region))
        if rid <= 0:
            self.__current = -1
        elif self.__current >= rid:
            self.__current = 0
        while self._getRegion(max(rid, 0)) is not None:
            self.__removeRegion()
        self.__showRegions(self._enabled)

    def setColors(self, colors=None):
        """ sets colors

        :param colors: json list of roi colors
        :type colors: :obj:`str`
        :returns: change status
        :rtype: :obj:`bool`
        """
        force = False
        if colors is not None:
            colors = json.loads(colors)
            if not isinstance(colors, list):
                return False
            for cl in colors:
                if not isinstance(cl, list):
                    return False
                if len(cl) != 3:
                    return False
                for clit in cl:
                    if not isinstance(clit, int):
                        return False
        else:
            colors = self.__colors
            force = True
        if self.__colors != colors or force:
            self.__colors = colors
            for it, rg in enumerate(self.__region):
                clr = tuple(colors[it % len(colors)]) if colors \
                    else self.__defpen
                rg.setPen(_pg.mkPen(clr, width=2))
                # if hasattr(self.__regiontext[it], "setColor"):
                #     self.__regiontext[it].setColor(clr)
                # else:
                #     self.__regiontext[it].color = _pg.functions.mkColor(clr)
                #     self.__regiontext[it].textItem.setDefaultTextColor(
                #         self.__regiontext[it].color)
        return True

    def regionPoints(self):
        """ provides region coordinates

        :return: region coordinates
        :rtype: :obj:`list` <  :obj:`list` <  :obj:`list`
                  < (:obj:`float`, :obj:`float`) > > >
        """
        return self.__points

    def isRegionEnabled(self):
        """ provides flag regions enabled

        :return: region enabled flag
        :rtype: :obj:`bool`
        """
        return self._enabled

    def currentRegion(self):
        """ provides current region id

        :return: region id
        :rtype: :obj:`int`
        """
        return self.__current

    def transpose(self):
        """ transposes Regions
        """
        for i, crd in enumerate(self.__region):
            if i < len(self.__points):
                if self._mainwidget.transformations()[0]:
                    pnts = [[(p[1], p[0]) for p in pt]
                            for pt in self.__points[i]]
                else:
                    pnts = self.__points[i]
                crd.setData(pnts)


class LockerExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "locker"
        #: (:obj:`bool`) crooshair locked flag
        self.__crosshairlocked = False
        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self.__lockercoordinates = None
        #: (:obj:`float`) last time in s
        self.__lasttime = 0.
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical locker line of the mouse position
        self.__lockerVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(255, 0, 0))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal locker line of the mouse position
        self.__lockerHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(255, 0, 0))
        self._mainwidget.viewbox().addItem(
            self.__lockerVLine, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(
            self.__lockerHLine, ignoreBounds=True)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.crosshairlocker is not None:
            self.__showLockerLines(parameters.crosshairlocker)
            self._enabled = parameters.crosshairlocker

    def coordinates(self):
        """ returns coordinates
        """
        xfdata = None
        yfdata = None
        if self.__crosshairlocked:
            xfdata = math.floor(self.__lockercoordinates[0])
            yfdata = math.floor(self.__lockercoordinates[1])
        return xfdata, yfdata

    def __showLockerLines(self, status):
        """ shows or hides HV locker mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__lockerVLine.show()
            self.__lockerHLine.show()
        else:
            self.__lockerVLine.hide()
            self.__lockerHLine.hide()

    def mouse_position(self, x, y):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        """
        if not self.__crosshairlocked:
            now = time.time()
            if now - self.__lasttime > self._refreshtime:
                self.__lasttime = now
                pos0, pos1, scale0, scale1 = self._mainwidget.scale()
                fx = math.floor(x)
                fy = math.floor(y)
                if pos0 is not None:
                    if not self._mainwidget.transformations()[0]:
                        self.__lockerVLine.setPos((fx + .5) * scale0 + pos0)
                        self.__lockerHLine.setPos((fy + .5) * scale1 + pos1)
                    else:
                        self.__lockerVLine.setPos((fy + .5) * scale1 + pos1)
                        self.__lockerHLine.setPos((fx + .5) * scale0 + pos0)
                else:
                    if not self._mainwidget.transformations()[0]:
                        self.__lockerVLine.setPos(fx + .5)
                        self.__lockerHLine.setPos(fy + .5)
                    else:
                        self.__lockerVLine.setPos(fy + .5)
                        self.__lockerHLine.setPos(fx + .5)

    def mouse_doubleclick(self, x, y, locked):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        :param locked: double click lock
        :type locked: bool
        """
        self.updateLocker(x, y)

    @QtCore.pyqtSlot(float, float)
    def updateLocker(self, xdata, ydata):
        """ updates the locker position

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__crosshairlocked = not self.__crosshairlocked
        if not self.__crosshairlocked:
            if not self._mainwidget.transformations()[0]:
                self.__lockerVLine.setPos(xdata + 0.5)
                self.__lockerHLine.setPos(ydata + 0.5)
            else:
                self.__lockerVLine.setPos(ydata + 0.5)
                self.__lockerHLine.setPos(xdata + 0.5)
        else:
            self.__lockercoordinates = [xdata, ydata]

    def transpose(self):
        """ transposes locker lines
        """
        v = self.__lockerHLine.getPos()[1]
        h = self.__lockerVLine.getPos()[0]
        self.__lockerVLine.setPos(v)
        self.__lockerHLine.setPos(h)


class CenterExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "center"

        #: ([:obj:`float`, :obj:`float`]) center coordinates
        self.__centercoordinates = None
        #: (:obj:`float`) last time in s
        self.__lasttime = 0.

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical center line of the mouse position
        self.__centerVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(0, 255, 0))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal center line of the mouse position
        self.__centerHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(0, 255, 0))
        self._mainwidget.viewbox().addItem(
            self.__centerVLine, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(
            self.__centerHLine, ignoreBounds=True)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.centerlines is not None:
            self.__showCenterLines(parameters.centerlines)
            self._enabled = parameters.centerlines

    def __showCenterLines(self, status):
        """ shows or hides HV center mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__centerVLine.show()
            self.__centerHLine.show()
        else:
            self.__centerVLine.hide()
            self.__centerHLine.hide()

    def mouse_position(self, x, y):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        """
        if not self.__centercoordinates:
            now = time.time()
            if now - self.__lasttime > self._refreshtime:
                self.__lasttime = now
                if not self._mainwidget.transformations()[0]:
                    self.__centerVLine.setPos(x)
                    self.__centerHLine.setPos(y)
                else:
                    self.__centerVLine.setPos(y)
                    self.__centerHLine.setPos(x)

    def mouse_doubleclick(self, x, y, locked):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        :param locked: double click lock
        :type locked: bool
        """
        self.updateCenter(x, y)

    @QtCore.pyqtSlot(float, float)
    def updateCenter(self, xdata, ydata):
        """ updates the image center

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__centercoordinates = [xdata, ydata]
        pos0, pos1, scale0, scale1 = self._mainwidget.scale(useraxes=False)
        if pos0 is not None:
            if not self._mainwidget.transformations()[0]:
                self.__centerVLine.setPos((xdata) * scale0 + pos0)
                self.__centerHLine.setPos((ydata) * scale1 + pos1)
            else:
                self.__centerVLine.setPos((ydata) * scale1 + pos1)
                self.__centerHLine.setPos((xdata) * scale0 + pos0)
        else:
            if not self._mainwidget.transformations()[0]:
                self.__centerVLine.setPos(xdata)
                self.__centerHLine.setPos(ydata)
            else:
                self.__centerVLine.setPos(ydata)
                self.__centerHLine.setPos(xdata)

    def transpose(self):
        """ transposes Center lines
        """
        v = self.__centerHLine.getPos()[1]
        h = self.__centerVLine.getPos()[0]
        self.__centerVLine.setPos(v)
        self.__centerHLine.setPos(h)


class VHBoundsExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "vhbounds"

        #: ([:obj:`float`, :obj:`float`]) vertical bound coordinates
        self.__vbounds = None
        #: ([:obj:`float`, :obj:`float`]) horizontal bound coordinates
        self.__hbounds = None

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 first vertical center line of the mouse position
        self.__centerVLine1 = _pg.InfiniteLine(
            angle=90, movable=False, pen=_pg.mkPen('r', width=2))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 second vertical center line of the mouse position
        self.__centerVLine2 = _pg.InfiniteLine(
            angle=90, movable=False, pen=_pg.mkPen('r', width=2))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:          first horizontal center line of the mouse position
        self.__centerHLine1 = _pg.InfiniteLine(
            angle=0, movable=False, pen=_pg.mkPen('r', width=2))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:          second horizontal center line of the mouse position
        self.__centerHLine2 = _pg.InfiniteLine(
            angle=0, movable=False, pen=_pg.mkPen('r', width=2))
        self._mainwidget.viewbox().addItem(
            self.__centerVLine1, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(
            self.__centerVLine2, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(
            self.__centerHLine1, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(
            self.__centerHLine2, ignoreBounds=True)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.vhbounds is not None:
            self.__showBounds(parameters.vhbounds)
            self._enabled = parameters.vhbounds

    def __showBounds(self, status):
        """ shows or hides HV center mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__centerVLine1.show()
            self.__centerHLine1.show()
            self.__centerVLine2.show()
            self.__centerHLine2.show()
        else:
            self.__centerVLine1.hide()
            self.__centerHLine1.hide()
            self.__centerVLine2.hide()
            self.__centerHLine2.hide()

    @QtCore.pyqtSlot(float, float)
    def updateVBounds(self, xdata1, xdata2):
        """ updates the vertical bounds

        :param xdata1: first x-pixel position
        :type xdata1: :obj:`float`
        :param xdata2: second x-pixel position
        :type xdata2: :obj:`float`
        """
        self.__vbounds = [xdata1, xdata2]
        if xdata1 is None:
            self.__centerVLine1.hide()
        else:
            self.__centerVLine1.setPos(xdata1)
            self.__centerVLine1.show()
        if xdata2 is None:
            self.__centerVLine2.hide()
        else:
            self.__centerVLine2.setPos(xdata2)
            self.__centerVLine2.show()

    @QtCore.pyqtSlot(float, float)
    def updateHBounds(self, ydata1, ydata2):
        """ updates the horizontal bounds

        :param ydata1: first y-pixel position
        :type ydata1: :obj:`float`
        :param ydata2: second y-pixel position
        :type ydata2: :obj:`float`
        """
        self.__hbounds = [ydata1, ydata2]
        if ydata1 is None:
            self.__centerHLine1.hide()
        else:
            self.__centerHLine1.setPos(ydata1)
            self.__centerHLine1.show()
        if ydata2 is None:
            self.__centerHLine2.hide()
        else:
            self.__centerHLine2.setPos(ydata2)
            self.__centerHLine2.show()


class BaseMarkExtension(DisplayExtension):

    """ base mark extension """

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "basemark"

        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self._markcoordinates = None
        #: (:obj:`float`) last time in s
        self._lasttime = 0.

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical mark line of the mouse position
        self._markVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(255, 255, 255))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal mark line of the mouse position
        self._markHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(255, 255, 255))
        self._mainwidget.viewbox().addItem(self._markVLine, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(self._markHLine, ignoreBounds=True)

    def _showMarkLines(self, status):
        """ shows or hides HV mark mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self._markVLine.show()
            self._markHLine.show()
        else:
            self._markVLine.hide()
            self._markHLine.hide()

    @QtCore.pyqtSlot(float, float)
    def updatePositionMark(self, xdata, ydata, scaled=False):
        """ updates the position mark

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        :param scaled: scaled flag
        :type scaled: :obj:`bool`
        """
        self._markcoordinates = [xdata, ydata]
        pos0, pos1, scale0, scale1 = self._mainwidget.scale()
        if pos0 is not None and not scaled:
            if not self._mainwidget.transformations()[0]:
                self._markVLine.setPos((xdata) * scale0 + pos0)
                self._markHLine.setPos((ydata) * scale1 + pos1)
            else:
                self._markVLine.setPos((ydata) * scale1 + pos1)
                self._markHLine.setPos((xdata) * scale0 + pos0)
        else:
            if not self._mainwidget.transformations()[0]:
                self._markVLine.setPos(xdata)
                self._markHLine.setPos(ydata)
            else:
                self._markVLine.setPos(ydata)
                self._markHLine.setPos(xdata)

    def transpose(self):
        """ transposes Mark Position lines
        """
        v = self._markHLine.getPos()[1]
        h = self._markVLine.getPos()[0]
        self._markVLine.setPos(v)
        self._markHLine.setPos(h)


class MarkExtension(BaseMarkExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseMarkExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "mark"

        self._markVLine.setPen((0, 0, 255))
        self._markHLine.setPen((0, 0, 255))

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.marklines is not None:
            self._showMarkLines(parameters.marklines)
            self._enabled = parameters.marklines

    def mouse_position(self, x, y):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        """
        if not self._markcoordinates:
            now = time.time()
            if now - self._lasttime > self._refreshtime:
                self._lasttime = now
                pos0, pos1, scale0, scale1 = self._mainwidget.scale()
                if pos0 is not None:
                    if not self._mainwidget.transformations()[0]:
                        self._markVLine.setPos((x) * scale0 + pos0)
                        self._markHLine.setPos((y) * scale1 + pos1)
                    else:
                        self._markVLine.setPos((y) * scale1 + pos1)
                        self._markHLine.setPos((x) * scale0 + pos0)
                else:
                    if not self._mainwidget.transformations()[0]:
                        self._markVLine.setPos(x)
                        self._markHLine.setPos(y)
                    else:
                        self._markVLine.setPos(y)
                        self._markHLine.setPos(x)

    def mouse_doubleclick(self, x, y, locked):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        :param locked: double click lock
        :type locked: bool
        """
        if not locked:
            self.updatePositionMark(x, y)


class TrackingExtension(BaseMarkExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        BaseMarkExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "tracking"

        self._markVLine.setPen((0, 255, 255))
        self._markHLine.setPen((0, 255, 255))

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.trackinglines is not None:
            self._showMarkLines(parameters.trackinglines)
            self._enabled = parameters.trackinglines


class MaximaExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`pyqtgraph.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "maxima"

        #: (:obj:`list` < > ) maxima parameters
        self.__positions = []

        self.__maxplot = _pg.ScatterPlotItem(
            size=30, symbol='+', pen=_pg.mkPen((0, 0, 0)))
        self._mainwidget.viewbox().addItem(self.__maxplot)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.maxima is not None:
            self.__showMaxima(parameters.maxima)
            self._enabled = parameters.maxima

    def __showMaxima(self, status):
        """ shows or hides maxima

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__maxplot.show()
        else:
            self.__maxplot.hide()

    def setMaximaPos(self, positionlist, offset=None):
        """
        sets maxima postions

        :param positionlist: [(x1, y1), ... , (xn, yn)]
        :type positionlist: :obj:`list` < (float, float) >
        :param offset: offset of position
        :type offset: [ :obj:`float`, :obj:`float`]
        """
        self.__positions = positionlist
        if offset is None:
            offset = [0.5, 0.5]
        spots = [{'pos': [i + offset[0], j + offset[1]], 'data': 1,
                  'brush': _pg.mkBrush((255, 0, 255))}
                 for i, j in self.__positions]
        if spots:
            spots[-1]['brush'] = _pg.mkBrush((255, 255, 0))
        self.__maxplot.clear()
        self.__maxplot.addPoints(spots)

    def transpose(self):
        """ transposes maxima
        """
        positionlist = [(pos[1], pos[0]) for pos in self.__positions]
        self.setMaximaPos(positionlist)
