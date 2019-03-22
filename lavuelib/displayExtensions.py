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
import numpy as np
import math
import json
from pyqtgraph.graphicsItems.ROI import ROI, LineROI, Handle
from PyQt4 import QtCore


_VMAJOR, _VMINOR, _VPATCH = _pg.__version__.split(".") \
    if _pg.__version__ else ("0", "9", "0")


class HandleWithSignals(Handle):
    """ handle with signals

    """
    #: (:class:`PyQt4.QtCore.pyqtSignal`) hover event emitted
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
        :type ev: :class:`PyQt4.QtCore.QEvent`:
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


class DisplayExtension(QtCore.QObject):
    """ display extension for ImageDisplayWidget
    """
    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        QtCore.QObject.__init__(self)
        #: (:obj:`str`) extension name
        self.name = "none"
        #: (:class:`PyQt4.QtCore.QObject`) mainwidget
        self._mainwidget = parent
        #: (:obj:`bool`) enabled flag
        self._enabled = False

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
    def transpose(self):
        """ transposes subwidget
        """

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

    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "rois"

        #: (:class:`PyQt4.QtCore.QSignalMapper`) current roi mapper
        self.__currentroimapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) roi region mapper
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
        self.setROIsColors()

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
        self.setROIsColors()

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
                        else:
                            rc = roicoords[rid]
                            rcrds = [rc[1], rc[0], rc[3], rc[2]]
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
                        roival = np.sum(image[
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
            print("Warning: %s" % str(e))

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

    def setROIsColors(self, colors=None):
        """ sets statistics without scaling flag

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

    #: (:class:`PyQt4.QtCore.pyqtSignal`) cut coordinate changed signal
    cutCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "cuts"

        #: (:class:`PyQt4.QtCore.QSignalMapper`) current cut mapper
        self.__currentcutmapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) cut region mapper
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
                while dt.ndim > 1:
                    dt = dt.mean(axis=1)
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
            print("Warning: %s" % str(e))

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

    #: (:class:`PyQt4.QtCore.pyqtSignal`) roi coordinate changed signal
    roiCoordsChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "mesh"

        #: (:class:`PyQt4.QtCore.QSignalMapper`) current roi mapper
        self.__currentroimapper = QtCore.QSignalMapper(self)
        #: (:class:`PyQt4.QtCore.QSignalMapper`) roi region mapper
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
            print("Warning: %s" % str(e))

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


class LockerExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "locker"

        #: (:obj:`bool`) crooshair locked flag
        self.__crosshairlocked = False
        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self.__lockercoordinates = None

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
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "center"

        #: ([:obj:`float`, :obj:`float`]) center coordinates
        self.__centercoordinates = None

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


class MarkExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
        """
        DisplayExtension.__init__(self, parent)

        #: (:obj:`str`) tool name
        self.name = "mark"

        #: ([:obj:`float`, :obj:`float`]) position mark coordinates
        self.__markcoordinates = None

        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                 vertical mark line of the mouse position
        self.__markVLine = _pg.InfiniteLine(
            angle=90, movable=False, pen=(0, 0, 255))
        #: (:class:`pyqtgraph.InfiniteLine`)
        #:                   horizontal mark line of the mouse position
        self.__markHLine = _pg.InfiniteLine(
            angle=0, movable=False, pen=(0, 0, 255))
        self._mainwidget.viewbox().addItem(self.__markVLine, ignoreBounds=True)
        self._mainwidget.viewbox().addItem(self.__markHLine, ignoreBounds=True)

    def show(self, parameters):
        """ set subwidget properties

        :param parameters: tool parameters
        :type parameters: :class:`lavuelib.toolWidget.ToolParameters`
        """
        if parameters.marklines is not None:
            self.__showMarkLines(parameters.marklines)
            self._enabled = parameters.marklines

    def __showMarkLines(self, status):
        """ shows or hides HV mark mouse lines

        :param status: will be shown
        :type status: :obj:`bool`
        """
        if status:
            self.__markVLine.show()
            self.__markHLine.show()
        else:
            self.__markVLine.hide()
            self.__markHLine.hide()

    def mouse_position(self, x, y):
        """  sets vLine and hLine positions

        :param x: x coordinate
        :type x: float
        :param y: y coordinate
        :type y: float
        """
        if not self.__markcoordinates:
            pos0, pos1, scale0, scale1 = self._mainwidget.scale()
            if pos0 is not None:
                if not self._mainwidget.transformations()[0]:
                    self.__markVLine.setPos((x) * scale0 + pos0)
                    self.__markHLine.setPos((y) * scale1 + pos1)
                else:
                    self.__markVLine.setPos((y) * scale1 + pos1)
                    self.__markHLine.setPos((x) * scale0 + pos0)
            else:
                if not self._mainwidget.transformations()[0]:
                    self.__markVLine.setPos(x)
                    self.__markHLine.setPos(y)
                else:
                    self.__markVLine.setPos(y)
                    self.__markHLine.setPos(x)

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

    @QtCore.pyqtSlot(float, float)
    def updatePositionMark(self, xdata, ydata):
        """ updates the position mark

        :param xdata: x pixel position
        :type xdata: :obj:`float`
        :param ydata: y-pixel position
        :type ydata: :obj:`float`
        """
        self.__markcoordinates = [xdata, ydata]
        pos0, pos1, scale0, scale1 = self._mainwidget.scale()
        if pos0 is not None:
            if not self._mainwidget.transformations()[0]:
                self.__markVLine.setPos((xdata) * scale0 + pos0)
                self.__markHLine.setPos((ydata) * scale1 + pos1)
            else:
                self.__markVLine.setPos((ydata) * scale1 + pos1)
                self.__markHLine.setPos((xdata) * scale0 + pos0)
        else:
            if not self._mainwidget.transformations()[0]:
                self.__markVLine.setPos(xdata)
                self.__markHLine.setPos(ydata)
            else:
                self.__markVLine.setPos(ydata)
                self.__markHLine.setPos(xdata)

    def transpose(self):
        """ transposes Mark Position lines
        """
        v = self.__markHLine.getPos()[1]
        h = self.__markVLine.getPos()[0]
        self.__markVLine.setPos(v)
        self.__markHLine.setPos(h)


class MaximaExtension(DisplayExtension):

    def __init__(self, parent=None):
        """ constructor

        :param parent: parent object
        :type parent: :class:`PyQt4.QtCore.QObject`
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

    def setMaximaPos(self, positionlist):
        """
        sets maxima postions

        :param positionlist: [(x1, y1), ... , (xn, yn)]
        :type positionlist: :obj:`list` < (float, float) >
        """
        self.__positions = positionlist
        spots = [{'pos': [i + 0.5, j + 0.5], 'data': 1,
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
