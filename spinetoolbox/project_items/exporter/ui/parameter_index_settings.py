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

# Form implementation generated from reading ui file 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\parameter_index_settings.ui',
# licensing of 'C:\data\GIT\SPINETOOLBOX\bin\..\spinetoolbox\project_items\exporter\ui\parameter_index_settings.ui' applies.
#
# Created: Thu Feb 13 11:53:49 2020
#      by: pyside2-uic  running on PySide2 5.11.2
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(588, 433)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.box = QtWidgets.QGroupBox(Form)
        self.box.setObjectName("box")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.box)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.message_label = QtWidgets.QLabel(self.box)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.message_label.sizePolicy().hasHeightForWidth())
        self.message_label.setSizePolicy(sizePolicy)
        self.message_label.setTextFormat(QtCore.Qt.RichText)
        self.message_label.setObjectName("message_label")
        self.verticalLayout_3.addWidget(self.message_label)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label = QtWidgets.QLabel(self.box)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.indexing_domains_label = QtWidgets.QLabel(self.box)
        self.indexing_domains_label.setTextFormat(QtCore.Qt.RichText)
        self.indexing_domains_label.setObjectName("indexing_domains_label")
        self.horizontalLayout_2.addWidget(self.indexing_domains_label)
        self.move_domain_left_button = QtWidgets.QPushButton(self.box)
        self.move_domain_left_button.setObjectName("move_domain_left_button")
        self.horizontalLayout_2.addWidget(self.move_domain_left_button)
        self.move_domain_right_button = QtWidgets.QPushButton(self.box)
        self.move_domain_right_button.setObjectName("move_domain_right_button")
        self.horizontalLayout_2.addWidget(self.move_domain_right_button)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.splitter = QtWidgets.QSplitter(self.box)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget_3 = QtWidgets.QWidget(self.splitter)
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.use_existing_domain_radio_button = QtWidgets.QRadioButton(self.verticalLayoutWidget_3)
        self.use_existing_domain_radio_button.setChecked(True)
        self.use_existing_domain_radio_button.setObjectName("use_existing_domain_radio_button")
        self.verticalLayout_6.addWidget(self.use_existing_domain_radio_button)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.existing_domains_combo = QtWidgets.QComboBox(self.verticalLayoutWidget_3)
        self.existing_domains_combo.setObjectName("existing_domains_combo")
        self.horizontalLayout.addWidget(self.existing_domains_combo)
        self.verticalLayout_6.addLayout(self.horizontalLayout)
        self.formLayout_3 = QtWidgets.QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.pick_expression_label = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.pick_expression_label.setObjectName("pick_expression_label")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.pick_expression_label)
        self.pick_expression_edit = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.pick_expression_edit.setPlaceholderText("")
        self.pick_expression_edit.setObjectName("pick_expression_edit")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.pick_expression_edit)
        self.verticalLayout_6.addLayout(self.formLayout_3)
        self.verticalLayout_4.addLayout(self.verticalLayout_6)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.create_domain_radio_button = QtWidgets.QRadioButton(self.verticalLayoutWidget_3)
        self.create_domain_radio_button.setObjectName("create_domain_radio_button")
        self.verticalLayout.addWidget(self.create_domain_radio_button)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.domain_name_label = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.domain_name_label.setObjectName("domain_name_label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.domain_name_label)
        self.domain_name_edit = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.domain_name_edit.setText("")
        self.domain_name_edit.setObjectName("domain_name_edit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.domain_name_edit)
        self.domain_description_label = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.domain_description_label.setObjectName("domain_description_label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.domain_description_label)
        self.domain_description_edit = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.domain_description_edit.setObjectName("domain_description_edit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.domain_description_edit)
        self.verticalLayout.addLayout(self.formLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.generator_expression_label = QtWidgets.QLabel(self.verticalLayoutWidget_3)
        self.generator_expression_label.setObjectName("generator_expression_label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.generator_expression_label)
        self.generator_expression_edit = QtWidgets.QLineEdit(self.verticalLayoutWidget_3)
        self.generator_expression_edit.setObjectName("generator_expression_edit")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.generator_expression_edit)
        self.verticalLayout_2.addLayout(self.formLayout_2)
        self.extract_indexes_button = QtWidgets.QPushButton(self.verticalLayoutWidget_3)
        self.extract_indexes_button.setObjectName("extract_indexes_button")
        self.verticalLayout_2.addWidget(self.extract_indexes_button)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_4.addLayout(self.verticalLayout)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_4.addItem(spacerItem1)
        self.index_table_view = QtWidgets.QTableView(self.splitter)
        self.index_table_view.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.index_table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.index_table_view.setObjectName("index_table_view")
        self.index_table_view.horizontalHeader().setVisible(True)
        self.verticalLayout_3.addWidget(self.splitter)
        self.verticalLayout_5.addWidget(self.box)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate("Form", "Form", None, -1))
        self.box.setTitle(QtWidgets.QApplication.translate("Form", "Parameter name", None, -1))
        self.message_label.setText(QtWidgets.QApplication.translate("Form", "TextLabel", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("Form", "Indexing domains:", None, -1))
        self.indexing_domains_label.setText(QtWidgets.QApplication.translate("Form", "(<b>unnamed</b>)", None, -1))
        self.move_domain_left_button.setText(QtWidgets.QApplication.translate("Form", "Move Left", None, -1))
        self.move_domain_right_button.setText(QtWidgets.QApplication.translate("Form", "Move Right", None, -1))
        self.use_existing_domain_radio_button.setText(QtWidgets.QApplication.translate("Form", "Use existing domain", None, -1))
        self.pick_expression_label.setToolTip(QtWidgets.QApplication.translate("Form", "Select rows for which this Python expression evaluates to True. Use <i>i</i> as the row index.", None, -1))
        self.pick_expression_label.setText(QtWidgets.QApplication.translate("Form", "Label picking expression:", None, -1))
        self.create_domain_radio_button.setText(QtWidgets.QApplication.translate("Form", "Create new index domain", None, -1))
        self.domain_name_label.setText(QtWidgets.QApplication.translate("Form", "Domain name:", None, -1))
        self.domain_name_edit.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type domain\'s name here...", None, -1))
        self.domain_description_label.setText(QtWidgets.QApplication.translate("Form", "Description:", None, -1))
        self.domain_description_edit.setPlaceholderText(QtWidgets.QApplication.translate("Form", "Type explanatory text here...", None, -1))
        self.generator_expression_label.setToolTip(QtWidgets.QApplication.translate("Form", "Generate index labels from Python expression. Use <i>i</i> as the row number.", None, -1))
        self.generator_expression_label.setText(QtWidgets.QApplication.translate("Form", "Generator expression:", None, -1))
        self.extract_indexes_button.setText(QtWidgets.QApplication.translate("Form", "Extract index from parameter", None, -1))

