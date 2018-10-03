# Copyright (c) 2012  University of North Carolina at Chapel Hill
# Luke Campagnola    ('luke.campagnola@%s.com' % 'gmail')
#
# The MIT License
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#: hooks for 0.9.10 from 0.10


from pyqtgraph.Point import Point
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from PyQt4 import QtGui


def viewbox_updateMatrix(self, changed=None):
    # Make the childGroup's transform match the requested viewRange.
    bounds = self.rect()

    vr = self.viewRect()
    if vr.height() == 0 or vr.width() == 0:
        return
    scale = Point(bounds.width()/vr.width(), bounds.height()/vr.height())
    if not self.state['yInverted']:
        scale = scale * Point(1, -1)
    if self.state['xInverted']:
        scale = scale * Point(-1, 1)
    m = QtGui.QTransform()

    # First center the viewport at 0
    center = bounds.center()
    m.translate(center.x(), center.y())

    # Now scale and translate properly
    m.scale(scale[0], scale[1])
    st = Point(vr.center())
    m.translate(-st[0], -st[1])

    self.childGroup.setTransform(m)

    self.sigTransformChanged.emit(self)  # segfaults here: 1
    self._matrixNeedsUpdate = False


def viewbox_invertX(self, b=True):
    """
    By default, the positive y-axis points upward on the screen.
    Use invertX(True) to reverse the x-axis.
    """
    if self.state['xInverted'] == b:
        return

    self.state['xInverted'] = b
    self._matrixNeedsUpdate = True
    self.updateViewRange()
    self.sigStateChanged.emit(self)
    self.sigXRangeChanged.emit(self, tuple(self.state['viewRange'][0]))


def viewbox_xInverted(self):
    return self.state['xInverted']


def axisitem_linkedViewChanged(self, view, newRange=None):
    if self.orientation in ['right', 'left']:
        if newRange is None:
            newRange = view.viewRange()[1]
        if view.yInverted():
            self.setRange(*newRange[::-1])
        else:
            self.setRange(*newRange)
    else:
        if newRange is None:
            newRange = view.viewRange()[0]
        if view.xInverted():
            self.setRange(*newRange[::-1])
        else:
            self.setRange(*newRange)


def viewbox_linkedViewChanged(self, view, axis):
    if self.linksBlocked or view is None:
        return

    vr = view.viewRect()
    vg = view.screenGeometry()
    sg = self.screenGeometry()
    if vg is None or sg is None:
        return

    view.blockLink(True)
    try:
        if axis == ViewBox.XAxis:
            overlap = min(sg.right(), vg.right()) - max(sg.left(), vg.left())
            # if less than 1/3 of views overlap,
            if overlap < min(vg.width()/3, sg.width()/3):
                # then just replicate the view
                x1 = vr.left()
                x2 = vr.right()
            else:
                # views overlap; line them up
                upp = float(vr.width()) / vg.width()
                if self.xInverted():
                    x1 = vr.left() + (sg.right()-vg.right()) * upp
                else:
                    x1 = vr.left() + (sg.x()-vg.x()) * upp
                x2 = x1 + sg.width() * upp
            self.enableAutoRange(ViewBox.XAxis, False)
            self.setXRange(x1, x2, padding=0)
        else:
            overlap = min(sg.bottom(), vg.bottom()) - max(sg.top(), vg.top())
            # if less than 1/3 of views overlap,
            if overlap < min(vg.height()/3, sg.height()/3):
                # then just replicate the view
                y1 = vr.top()
                y2 = vr.bottom()
            else:  # views overlap; line them up
                upp = float(vr.height()) / vg.height()
                if self.yInverted():
                    y2 = vr.bottom() + (sg.bottom()-vg.bottom()) * upp
                else:
                    y2 = vr.bottom() + (sg.top()-vg.top()) * upp
                y1 = y2 - sg.height() * upp
            self.enableAutoRange(ViewBox.YAxis, False)
            self.setYRange(y1, y2, padding=0)
    finally:
        view.blockLink(False)
