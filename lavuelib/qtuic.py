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

""" uic support """
import os


uic = None
QWebView = None
qt_api = os.getenv("QT_API", os.getenv('DEFAULT_QT_API', 'pyqt5'))
if qt_api != 'pyqt4':
    try:
        from PyQt5 import uic
        # from PyQt5.QtWebKitWidgets import QWebView
        QWebView = __import__(
            'PyQt5.QtWebKitWidgets', globals(), locals(),
            ['QWebView'], 0).QWebView
    except Exception:
        from PyQt4 import uic
        # from PyQt4.QtWebKitWidgets import QWebView
        QWebView = __import__(
            'PyQt4.QtWebKit', globals(), locals(),
            ['QWebView'], 0).QWebView
else:
    from PyQt4 import uic
    # from PyQt4.QtWebKitWidgets import QWebView
    QWebView = __import__(
        'PyQt4.QtWebKit', globals(), locals(),
        ['QWebView'], 0).QWebView


__all__ = ['uic', 'QWebView']
