# Copyright (c) 2012  University of North Carolina at Chapel Hill
# Luke Campagnola    ('luke.campagnola@%s.com' % 'gmail')

# The MIT License
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to
# whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from pyqtgraph.Qt import QtGui
from pyqtgraph.Point import Point
from pyqtgraph import functions as fn
from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.GradientEditorItem import GradientEditorItem
from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.graphicsItems.AxisItem import AxisItem
from pyqtgraph.graphicsItems.LinearRegionItem import LinearRegionItem


def histogram__init__(self, image=None, fillHistogram=True, levelMode='mono',
                      gradientPosition='right', orientation='vertical'):
    GraphicsWidget.__init__(self)
    self.lut = None
    self.imageItem = lambda: None  # fake a dead weakref
    self.levelMode = levelMode
    self.orientation = orientation
    self.gradientPosition = gradientPosition

    if orientation == 'vertical' and gradientPosition not in {'right', 'left'}:
        self.gradientPosition = 'right'
    elif orientation == 'horizontal' and \
            gradientPosition not in {'top', 'bottom'}:
        self.gradientPosition = 'bottom'

    self.layout = QtGui.QGraphicsGridLayout()
    self.setLayout(self.layout)
    self.layout.setContentsMargins(1, 1, 1, 1)
    self.layout.setSpacing(0)

    self.vb = ViewBox(parent=self)
    if self.orientation == 'vertical':
        self.vb.setMaximumWidth(152)
        self.vb.setMinimumWidth(45)
        self.vb.setMouseEnabled(x=False, y=True)
    else:
        self.vb.setMaximumHeight(152)
        self.vb.setMinimumHeight(45)
        self.vb.setMouseEnabled(x=True, y=False)

    self.gradient = GradientEditorItem(orientation=self.gradientPosition)
    self.gradient.loadPreset('grey')

    # LinearRegionItem orientation refers to the bounding lines
    regionOrientation = 'horizontal' \
        if self.orientation == 'vertical' else 'vertical'
    self.regions = [
        # single region for mono levelMode
        LinearRegionItem([0, 1], regionOrientation, swapMode='block'),
        # r/g/b/a regions for rgba levelMode
        LinearRegionItem(
            [0, 1], regionOrientation, swapMode='block', pen='r',
            brush=fn.mkBrush((255, 50, 50, 50)), span=(0., 1/3.)),
        LinearRegionItem(
            [0, 1], regionOrientation, swapMode='block', pen='g',
            brush=fn.mkBrush((50, 255, 50, 50)), span=(1/3., 2/3.)),
        LinearRegionItem(
            [0, 1], regionOrientation, swapMode='block', pen='b',
            brush=fn.mkBrush((50, 50, 255, 80)), span=(2/3., 1.)),
        LinearRegionItem(
            [0, 1], regionOrientation, swapMode='block', pen='w',
            brush=fn.mkBrush((255, 255, 255, 50)), span=(2/3., 1.))
    ]
    self.region = self.regions[0]  # for backward compatibility.
    for region in self.regions:
        region.setZValue(1000)
        self.vb.addItem(region)
        region.lines[0].addMarker('<|', 0.5)
        region.lines[1].addMarker('|>', 0.5)
        region.sigRegionChanged.connect(self.regionChanging)
        region.sigRegionChangeFinished.connect(self.regionChanged)

    # gradient position to axis orientation
    ax = {'left': 'right', 'right': 'left',
          'top': 'bottom', 'bottom': 'top'}[self.gradientPosition]
    self.axis = AxisItem(ax, linkView=self.vb, maxTickLength=-10, parent=self)

    # axis / viewbox / gradient order in the grid
    avg = (0, 1, 2) if self.gradientPosition in {'right', 'bottom'} \
        else (2, 1, 0)
    if self.orientation == 'vertical':
        self.layout.addItem(self.axis, 0, avg[0])
        self.layout.addItem(self.vb, 0, avg[1])
        self.layout.addItem(self.gradient, 0, avg[2])
    else:
        self.layout.addItem(self.axis, avg[0], 0)
        self.layout.addItem(self.vb, avg[1], 0)
        self.layout.addItem(self.gradient, avg[2], 0)

    self.gradient.setFlag(
        self.gradient.GraphicsItemFlag.ItemStacksBehindParent)
    self.vb.setFlag(self.gradient.GraphicsItemFlag.ItemStacksBehindParent)

    self.gradient.sigGradientChanged.connect(self.gradientChanged)
    self.vb.sigRangeChanged.connect(self.viewRangeChanged)

    comp = QtGui.QPainter.CompositionMode.CompositionMode_Plus
    self.plots = [
        PlotCurveItem(pen=(200, 200, 200, 100)),  # mono
        PlotCurveItem(pen=(255, 0, 0, 100), compositionMode=comp),  # r
        PlotCurveItem(pen=(0, 255, 0, 100), compositionMode=comp),  # g
        PlotCurveItem(pen=(0, 0, 255, 100), compositionMode=comp),  # b
        PlotCurveItem(pen=(200, 200, 200, 100), compositionMode=comp),  # a
    ]
    self.plot = self.plots[0]  # for backward compatibility.
    for plot in self.plots:
        if self.orientation == 'vertical':
            plot.setRotation(90)
        self.vb.addItem(plot)

    self.fillHistogram(fillHistogram)
    self._showRegions()

    self.autoHistogramRange()

    if image is not None:
        self.setImageItem(image)


def histogram_paint(self, p, *args):
    # paint the bounding edges of the region item and gradient item with lines
    # connecting them
    if self.levelMode != 'mono' or not self.region.isVisible():
        return

    pen = self.region.lines[0].pen

    mn, mx = self.getLevels()
    vbc = self.vb.viewRect().center()
    gradRect = self.gradient.mapRectToParent(self.gradient.gradRect.rect())
    if self.orientation == 'vertical':
        p1mn = self.vb.mapFromViewToItem(
            self, Point(vbc.x(), mn)) + Point(0, 5)
        p1mx = self.vb.mapFromViewToItem(
            self, Point(vbc.x(), mx)) - Point(0, 5)
        if self.gradientPosition == 'right':
            p2mn = gradRect.bottomLeft()
            p2mx = gradRect.topLeft()
        else:
            p2mn = gradRect.bottomRight()
            p2mx = gradRect.topRight()
    else:
        p1mn = self.vb.mapFromViewToItem(
            self, Point(mn, vbc.y())) - Point(5, 0)
        p1mx = self.vb.mapFromViewToItem(
            self, Point(mx, vbc.y())) + Point(5, 0)
        if self.gradientPosition == 'bottom':
            p2mn = gradRect.topLeft()
            p2mx = gradRect.topRight()
        else:
            p2mn = gradRect.bottomLeft()
            p2mx = gradRect.bottomRight()

    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    for pen in [fn.mkPen((0, 0, 0, 100), width=3), pen]:
        p.setPen(pen)

        # lines from the linear region item bounds to the gradient item bounds
        p.drawLine(p1mn, p2mn)
        p.drawLine(p1mx, p2mx)

        # lines bounding the edges of the gradient item
        if self.orientation == 'vertical':
            p.drawLine(gradRect.topLeft(), gradRect.topRight())
            p.drawLine(gradRect.bottomLeft(), gradRect.bottomRight())
        else:
            p.drawLine(gradRect.topLeft(), gradRect.bottomLeft())
            p.drawLine(gradRect.topRight(), gradRect.bottomRight())


def histogram_setHistogramRange(self, mn, mx, padding=0.1):
    """Set the Y range on the histogram plot. This disables auto-scaling."""
    if self.orientation == 'vertical':
        self.vb.enableAutoRange(self.vb.YAxis, False)
        self.vb.setYRange(mn, mx, padding)
    else:
        self.vb.enableAutoRange(self.vb.XAxis, False)
        self.vb.setXRange(mn, mx, padding)
