# -*- coding: utf-8 -*-
"""
    Copyright (c) 2009 Fabian Henze <flyser42@gmx.de>

    "Wo ist der Eismann?" is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License, version 2,
    as published by the Free Software Foundation.

    "Wo ist der Eismann?" is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *
from PyQt4.QtWebKit import *
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript
from PyKDE4.kdeui import *
from PyKDE4.kdecore import *

# Why do I have to subclass Plasma.WebView just to disable the context menu?
class MyWebView(Plasma.WebView):
    def contextMenuEvent(self, event):
        event.ignore()

class Eismann(plasmascript.Applet):
    def __init__(self,parent,args=None):
        plasmascript.Applet.__init__(self,parent)


    def init(self):
        self.setHasConfigurationInterface(True)
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.setBackgroundHints(Plasma.Applet.TranslucentBackground)

        self.updateinterval = -1
        self.zoomlevel = -1
        self.networkaccessmanager = QNetworkAccessManager()
        self.networkrequest = QNetworkRequest(QUrl("http://www.wo-ist-der-eismann.de/exec?action=eismann&function=position"))
        self.webview = MyWebView(self.applet)

        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.layout.addItem(self.webview)
        self.setLayout(self.layout)

        self.refreshIcon = Plasma.IconWidget(self.applet)
        self.refreshIcon.setIcon(KIcon("view-refresh"))
        self.refreshIcon.setZValue(1.0)
        self.constraintsEvent(Plasma.SizeConstraint)
        self.refreshIcon.hide()

        self.timer = QTimer()
        self.timer.setSingleShot(True)

        self.timeouttimer = QTimer()
        self.timeouttimer.setSingleShot(True)
        self.timeouttimer.setInterval(60000) # 60 sec.

        self.readConfig()

        QObject.connect(self.timer, SIGNAL("timeout()"), self.feedLoad)
        QObject.connect(self.timeouttimer, SIGNAL("timeout()"), self.networkTimeout)
        QObject.connect(self.refreshIcon, SIGNAL("clicked()"), self.timer.stop)
        QObject.connect(self.refreshIcon, SIGNAL("clicked()"), self.feedLoad)
        QObject.connect(self.configScheme(), SIGNAL("configChanged()"), self.readConfig)
        QObject.connect(self.webview, SIGNAL("loadFinished(bool)"), self.feedLoad)
        QObject.connect(self.networkaccessmanager, SIGNAL("finished(QNetworkReply *)"), self.feedLoadFinished) # I hate PyQt!
        self.webview.setUrl(KUrl(self.package().path() + "contents/html/main.html"))

    def constraintsEvent(self, constraint):
        if constraint != Plasma.SizeConstraint:
            return
        contentsRect = self.contentsRect()
        padding = 15
        size = min(min(24, contentsRect.width() - 2*padding), contentsRect.height() - 2*padding)
        if size <= 2:
            size = 0
        x = contentsRect.right() - padding - size
        y = contentsRect.top() + padding

        self.refreshIcon.setGeometry(x, y, size, size)

    def hoverEnterEvent(self, event):
        self.refreshIcon.show()

    def hoverLeaveEvent(self, event):
        self.refreshIcon.hide()

    def feedLoad(self):
        # Fetch the coordinates asynchronously and execute feedLoadFinished()
        # when done. Also start a timer to execute self.reply.abort() in the
        # event of a timeout. 
        self.timeouttimer.start()
        self.reply = self.networkaccessmanager.get(self.networkrequest)

    def networkTimeout(self):
        # self.reply.abort will cause feedLoadFinished() to run, so
        # timeouttimer.stop shouldn't be needed here
        self.reply.abort()

    def feedLoadFinished(self, reply):
        self.timeouttimer.stop()
        if reply.error() == QNetworkReply.NoError and reply.bytesAvailable() > 0:
            # No errors occured, now we do our best to parse the javascript code
            regex = QRegExp("((\\d|\.)+)")
            jscript_coords = QString(reply.readAll())
            pos = jscript_coords.indexOf("EISMANN.doUpdateMakerOnMap") + 26 #  26 == count("EISMANN.doUpdateMakerOnMap")
            valueList = []

            pos = regex.indexIn(jscript_coords, pos)
            while pos != -1:
                valueList.append(regex.cap(1))
                pos += regex.matchedLength()
                pos = regex.indexIn(jscript_coords, pos)
            # The valueList now contains the following information:
            # IMEI, Latitude, Longitude, Heading, Speed, Timestamp

            self.lat = valueList[1]
            self.lon = valueList[2]

            self.webview.page().mainFrame().evaluateJavaScript("newPos(" + self.lon + ", " + self.lat + ");"
                                                             + "document.getElementById(\"error\").innerHTML=\"\";")
        else:
            # If self.reply was aborted due to a timeout of 'timeouttimer', we
            # set the error message by ourselves. See Qt bug #3443
            if reply.error() == QNetworkReply.OperationCanceledError:
                # FIXME: Use plasmoid.i18n("") here?!
                errorString = "Connection to \"www.wo-ist-der-eismann.de\" timed out."
            else:
                errorString = reply.errorString()
            self.webview.page().mainFrame().evaluateJavaScript("document.getElementById(\"error\").innerHTML=\'" + errorString + "\';")
        self.timer.start()

    def readConfig(self):
        # FIXME: an updateinterval of 0 should disable automatic updates
        oldupdateinterval = self.updateinterval
        oldzoomlevel = self.zoomlevel

        # readEntry(string key, defaultvalue) returns a QVariant
        # toInt() returns the tuple: (int value, bool ok)
        self.zoomlevel      = self.config("General").readEntry("ZoomLevel", 13).toInt()[0] - 1
        self.updateinterval = self.config("General").readEntry("UpdateInterval", 5).toInt()[0]

        # If oldupdateinterval and the oldzoomlevel is -1 it means that we are
        # called by the init() function. In this case:
        #  * don't start self.timer
        #  * don't try to execute JavaScript code
        if oldupdateinterval != self.updateinterval:
            self.timer.stop()
            self.timer.setInterval(self.updateinterval*1000*60)
            if oldupdateinterval != -1:
                self.timer.start()
        if oldzoomlevel != self.zoomlevel and oldzoomlevel != -1:
            self.webview.page().mainFrame().evaluateJavaScript("map.zoomTo(" + str(self.zoomlevel) + ");")


def CreateApplet(parent):
    return Eismann(parent) 
