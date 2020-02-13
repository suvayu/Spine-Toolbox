# -*- coding: utf-8 -*-
######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\spine_datapackage_form.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\ui\spine_datapackage_form.ui' applies.
#
# Created: Wed Feb 12 13:45:26 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1088, 824)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.frame = QtWidgets.QFrame(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(9, 0, 9, 9)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.tableView_resources = CopyPasteTableView(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView_resources.sizePolicy().hasHeightForWidth())
        self.tableView_resources.setSizePolicy(sizePolicy)
        self.tableView_resources.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tableView_resources.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.tableView_resources.setShowGrid(False)
        self.tableView_resources.setObjectName("tableView_resources")
        self.tableView_resources.horizontalHeader().setHighlightSections(False)
        self.tableView_resources.verticalHeader().setVisible(False)
        self.verticalLayout.addWidget(self.tableView_resources)
        self.frame_2 = QtWidgets.QFrame(self.splitter)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.frame_2)
        self.verticalLayout_3.setContentsMargins(9, 0, 9, 9)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_2 = QtWidgets.QLabel(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_3.addWidget(self.label_2)
        self.tableView_resource_data = CopyPasteTableView(self.frame_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableView_resource_data.sizePolicy().hasHeightForWidth())
        self.tableView_resource_data.setSizePolicy(sizePolicy)
        self.tableView_resource_data.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tableView_resource_data.setTabKeyNavigation(False)
        self.tableView_resource_data.setObjectName("tableView_resource_data")
        self.tableView_resource_data.horizontalHeader().setVisible(True)
        self.tableView_resource_data.horizontalHeader().setHighlightSections(False)
        self.tableView_resource_data.verticalHeader().setVisible(False)
        self.tableView_resource_data.verticalHeader().setHighlightSections(False)
        self.verticalLayout_3.addWidget(self.tableView_resource_data)
        self.verticalLayout_2.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1088, 28))
        self.menubar.setNativeMenuBar(False)
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setToolTipsVisible(True)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QtWidgets.QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuDock_Widgets = QtWidgets.QMenu(self.menuView)
        self.menuDock_Widgets.setObjectName("menuDock_Widgets")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.dockWidget_fields = QtWidgets.QDockWidget(MainWindow)
        self.dockWidget_fields.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.dockWidget_fields.setObjectName("dockWidget_fields")
        self.dockWidgetContents_5 = QtWidgets.QWidget()
        self.dockWidgetContents_5.setObjectName("dockWidgetContents_5")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.dockWidgetContents_5)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.tableView_fields = CopyPasteTableView(self.dockWidgetContents_5)
        self.tableView_fields.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tableView_fields.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.tableView_fields.setShowGrid(True)
        self.tableView_fields.setObjectName("tableView_fields")
        self.tableView_fields.horizontalHeader().setHighlightSections(False)
        self.tableView_fields.horizontalHeader().setSortIndicatorShown(False)
        self.tableView_fields.verticalHeader().setVisible(False)
        self.verticalLayout_8.addWidget(self.tableView_fields)
        self.dockWidget_fields.setWidget(self.dockWidgetContents_5)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWidget_fields)
        self.dockWidget_foreign_keys = QtWidgets.QDockWidget(MainWindow)
        self.dockWidget_foreign_keys.setObjectName("dockWidget_foreign_keys")
        self.dockWidgetContents_6 = QtWidgets.QWidget()
        self.dockWidgetContents_6.setObjectName("dockWidgetContents_6")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.dockWidgetContents_6)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.tableView_foreign_keys = CopyPasteTableView(self.dockWidgetContents_6)
        self.tableView_foreign_keys.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tableView_foreign_keys.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.tableView_foreign_keys.setShowGrid(True)
        self.tableView_foreign_keys.setGridStyle(QtCore.Qt.SolidLine)
        self.tableView_foreign_keys.setObjectName("tableView_foreign_keys")
        self.tableView_foreign_keys.horizontalHeader().setHighlightSections(False)
        self.tableView_foreign_keys.verticalHeader().setVisible(True)
        self.verticalLayout_9.addWidget(self.tableView_foreign_keys)
        self.dockWidget_foreign_keys.setWidget(self.dockWidgetContents_6)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWidget_foreign_keys)
        self.actionSave_datapackage = QtWidgets.QAction(MainWindow)
        self.actionSave_datapackage.setObjectName("actionSave_datapackage")
        self.actionClose = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/close.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionClose.setIcon(icon)
        self.actionClose.setObjectName("actionClose")
        self.actionRemove_foreign_keys = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRemove_foreign_keys.setIcon(icon1)
        self.actionRemove_foreign_keys.setObjectName("actionRemove_foreign_keys")
        self.actionInfer_datapackage = QtWidgets.QAction(MainWindow)
        self.actionInfer_datapackage.setObjectName("actionInfer_datapackage")
        self.actionExport_to_spine = QtWidgets.QAction(MainWindow)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/Spine_db_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionExport_to_spine.setIcon(icon2)
        self.actionExport_to_spine.setObjectName("actionExport_to_spine")
        self.actionCopy = QtWidgets.QAction(MainWindow)
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/copy.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionCopy.setIcon(icon3)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QtWidgets.QAction(MainWindow)
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/paste.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPaste.setIcon(icon4)
        self.actionPaste.setObjectName("actionPaste")
        self.actionxx = QtWidgets.QAction(MainWindow)
        self.actionxx.setObjectName("actionxx")
        self.menuFile.addAction(self.actionInfer_datapackage)
        self.menuFile.addAction(self.actionSave_datapackage)
        self.menuFile.addSeparator()
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExport_to_spine)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionClose)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuView.addAction(self.menuDock_Widgets.menuAction())
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Spine datapackage editor", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MainWindow", "Resources", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("MainWindow", "Data", None, -1))
        self.menuFile.setTitle(QtWidgets.QApplication.translate("MainWindow", "File", None, -1))
        self.menuEdit.setTitle(QtWidgets.QApplication.translate("MainWindow", "Edit", None, -1))
        self.menuView.setTitle(QtWidgets.QApplication.translate("MainWindow", "View", None, -1))
        self.menuDock_Widgets.setTitle(QtWidgets.QApplication.translate("MainWindow", "Dock Widgets", None, -1))
        self.dockWidget_fields.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Fields", None, -1))
        self.dockWidget_foreign_keys.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "Foreign keys", None, -1))
        self.actionSave_datapackage.setText(QtWidgets.QApplication.translate("MainWindow", "Save \"datapackage.json\"", None, -1))
        self.actionSave_datapackage.setToolTip(QtWidgets.QApplication.translate("MainWindow", "Save as \'datapackage.json\'", None, -1))
        self.actionSave_datapackage.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+S", None, -1))
        self.actionClose.setText(QtWidgets.QApplication.translate("MainWindow", "Close", None, -1))
        self.actionClose.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+W", None, -1))
        self.actionRemove_foreign_keys.setText(QtWidgets.QApplication.translate("MainWindow", "Remove foreign keys", None, -1))
        self.actionRemove_foreign_keys.setToolTip(QtWidgets.QApplication.translate("MainWindow", "Remove selected foreign keys.", None, -1))
        self.actionInfer_datapackage.setText(QtWidgets.QApplication.translate("MainWindow", "Infer datapackage", None, -1))
        self.actionInfer_datapackage.setToolTip(QtWidgets.QApplication.translate("MainWindow", "(Re)infer datapackage from CSV files in data directory.", None, -1))
        self.actionInfer_datapackage.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+I", None, -1))
        self.actionExport_to_spine.setText(QtWidgets.QApplication.translate("MainWindow", "Export to Spine format", None, -1))
        self.actionExport_to_spine.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+E", None, -1))
        self.actionCopy.setText(QtWidgets.QApplication.translate("MainWindow", "Copy", None, -1))
        self.actionCopy.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+C", None, -1))
        self.actionPaste.setText(QtWidgets.QApplication.translate("MainWindow", "Paste", None, -1))
        self.actionPaste.setShortcut(QtWidgets.QApplication.translate("MainWindow", "Ctrl+V", None, -1))
        self.actionxx.setText(QtWidgets.QApplication.translate("MainWindow", "xx", None, -1))

from spinetoolbox.widgets.custom_qtableview import CopyPasteTableView
from spinetoolbox import resources_icons_rc
