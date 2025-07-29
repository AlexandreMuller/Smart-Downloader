# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'interface.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QFrame, QHeaderView,
    QLabel, QMainWindow, QPushButton, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(542, 642)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setMaximumSize(QSize(763, 16777215))
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_5 = QFrame(self.frame)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_5)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.downloads_label = QLabel(self.frame_5)
        self.downloads_label.setObjectName(u"downloads_label")
        font = QFont()
        font.setFamilies([u"Open Sans"])
        font.setPointSize(8)
        font.setBold(True)
        self.downloads_label.setFont(font)

        self.verticalLayout_3.addWidget(self.downloads_label)

        self.novo_download = QPushButton(self.frame_5)
        self.novo_download.setObjectName(u"novo_download")

        self.verticalLayout_3.addWidget(self.novo_download)


        self.verticalLayout_2.addWidget(self.frame_5)

        self.frame_6 = QFrame(self.frame)
        self.frame_6.setObjectName(u"frame_6")
        sizePolicy.setHeightForWidth(self.frame_6.sizePolicy().hasHeightForWidth())
        self.frame_6.setSizePolicy(sizePolicy)
        self.frame_6.setFrameShape(QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_6)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.downloads_window = QTreeWidget(self.frame_6)
        font1 = QFont()
        font1.setStyleStrategy(QFont.PreferAntialias)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setFont(0, font1);
        self.downloads_window.setHeaderItem(__qtreewidgetitem)
        self.downloads_window.setObjectName(u"downloads_window")
        sizePolicy.setHeightForWidth(self.downloads_window.sizePolicy().hasHeightForWidth())
        self.downloads_window.setSizePolicy(sizePolicy)
        self.downloads_window.setFrameShape(QFrame.NoFrame)
        self.downloads_window.setFrameShadow(QFrame.Plain)
        self.downloads_window.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.downloads_window.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.downloads_window.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        self.downloads_window.setAutoExpandDelay(0)
        self.downloads_window.setRootIsDecorated(True)
        self.downloads_window.setUniformRowHeights(False)
        self.downloads_window.setItemsExpandable(True)
        self.downloads_window.setSortingEnabled(False)
        self.downloads_window.setAllColumnsShowFocus(False)
        self.downloads_window.setWordWrap(False)
        self.downloads_window.setHeaderHidden(True)
        self.downloads_window.setExpandsOnDoubleClick(True)
        self.downloads_window.setColumnCount(1)
        self.downloads_window.header().setVisible(False)
        self.downloads_window.header().setCascadingSectionResizes(False)
        self.downloads_window.header().setHighlightSections(False)
        self.downloads_window.header().setProperty("showSortIndicator", False)
        self.downloads_window.header().setStretchLastSection(True)

        self.verticalLayout_4.addWidget(self.downloads_window)


        self.verticalLayout_2.addWidget(self.frame_6)

        self.btn_clean_debug = QPushButton(self.frame)
        self.btn_clean_debug.setObjectName(u"btn_clean_debug")
        self.btn_clean_debug.setStyleSheet(u"")

        self.verticalLayout_2.addWidget(self.btn_clean_debug)


        self.verticalLayout.addWidget(self.frame)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.downloads_label.setText(QCoreApplication.translate("MainWindow", u"Downloads:", None))
        self.novo_download.setText(QCoreApplication.translate("MainWindow", u"Novo Download", None))
        ___qtreewidgetitem = self.downloads_window.headerItem()
        ___qtreewidgetitem.setText(0, QCoreApplication.translate("MainWindow", u"Logs", None));
        self.btn_clean_debug.setText(QCoreApplication.translate("MainWindow", u"Limpar Downloads", None))
    # retranslateUi

