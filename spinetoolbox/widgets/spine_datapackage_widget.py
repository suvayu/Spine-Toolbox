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

"""
Widget shown to user when opening a 'datapackage.json' file
in Data Connection item.

:author: M. Marin (KTH)
:date:   7.7.2018
"""

import glob
import os
import csv
from PySide2.QtWidgets import QMainWindow, QMessageBox, QErrorMessage, QUndoStack, QAction
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QItemSelectionModel
from PySide2.QtGui import QGuiApplication, QFontMetrics, QFont, QIcon, QKeySequence
from datapackage import Package
from datapackage.exceptions import DataPackageException
from .custom_delegates import ForeignKeysDelegate, CheckBoxDelegate
from ..mvcmodels.data_package_models import (
    DatapackageResourcesModel,
    DatapackageFieldsModel,
    DatapackageForeignKeysModel,
    DatapackageResourceDataModel,
)
from ..helpers import ensure_window_is_on_screen
from ..config import STATUSBAR_SS


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.
    """

    msg = Signal(str)
    msg_error = Signal(str)

    def __init__(self, data_connection):
        """Initialize class.

        Args:
            data_connection (DataConnection): Data Connection associated to this widget
        """
        from ..ui.spine_datapackage_form import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        super().__init__(flags=Qt.Window)
        self._data_connection = data_connection
        self.datapackage = CustomPackage(base_path=self._data_connection.data_dir, unsafe=True)
        self.selected_resource_index = None
        self.resources_model = DatapackageResourcesModel(self, self.datapackage)
        self.fields_model = DatapackageFieldsModel(self, self.datapackage)
        self.foreign_keys_model = DatapackageForeignKeysModel(self, self.datapackage)
        self.resource_data_model = DatapackageResourceDataModel(self, self.datapackage)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.err_msg = QErrorMessage(self)
        self.remove_row_icon = QIcon(":/icons/minus.png")
        self.focus_widget = None  # Last widget which had focus before showing a menu from the menubar
        self.undo_stack = QUndoStack(self)
        self._save_resource_actions = []
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.takeCentralWidget()
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.restore_ui()
        self.add_menu_actions()
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.tableView_resources.setModel(self.resources_model)
        self.ui.tableView_resources.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.tableView_resource_data.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_fields.setModel(self.fields_model)
        self.ui.tableView_fields.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_fields.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_foreign_keys.setModel(self.foreign_keys_model)
        self.ui.tableView_foreign_keys.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_foreign_keys.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.connect_signals()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(
            "{0} [{1}][*] - Spine datapackage manager".format(
                self._data_connection.name, self._data_connection.data_dir
            )
        )

    def add_menu_actions(self):
        """Add extra menu actions."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_resources.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_data.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_fields.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_foreign_keys.toggleViewAction())
        undo_action = self.undo_stack.createUndoAction(self)
        redo_action = self.undo_stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        undo_action.setIcon(QIcon(":/icons/menu_icons/undo.svg"))
        redo_action.setIcon(QIcon(":/icons/menu_icons/redo.svg"))
        before = self.ui.menuEdit.actions()[0]
        self.ui.menuEdit.insertAction(before, undo_action)
        self.ui.menuEdit.insertAction(before, redo_action)
        self.ui.menuEdit.insertSeparator(before)

    def connect_signals(self):
        """Connect signals to slots."""
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        self._data_connection.data_dir_watcher.directoryChanged.connect(self.refresh_datapackage)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.actionSave_All.triggered.connect(self.save_all)
        self.ui.menuFile.aboutToShow.connect(self._handle_menu_about_to_show)
        self.ui.menuEdit.aboutToShow.connect(self._handle_menu_about_to_show)
        self.ui.menuView.aboutToShow.connect(self._handle_menu_about_to_show)
        self.resources_model.resource_dirty_changed.connect(self._handle_resource_dirty_changed)
        self.resource_data_model.resource_data_changed.connect(self.resources_model.update_dirty)
        self.fields_model.dataChanged.connect(self._handle_fields_data_changed)
        self.undo_stack.cleanChanged.connect(self.update_window_modified)
        checkbox_delegate = CheckBoxDelegate(self)
        checkbox_delegate.data_committed.connect(self.fields_model.setData)
        self.ui.tableView_fields.setItemDelegateForColumn(2, checkbox_delegate)
        foreign_keys_delegate = ForeignKeysDelegate(self)
        foreign_keys_delegate.data_committed.connect(self.foreign_keys_model.setData)
        self.ui.tableView_foreign_keys.setItemDelegate(foreign_keys_delegate)
        self.ui.tableView_resources.selectionModel().currentChanged.connect(self._handle_current_resource_changed)

    @Slot(bool)
    def update_window_modified(self, clean):
        """Updates window modified status and save actions depending on the state of the undo stack."""
        try:
            self.setWindowModified(not clean)
        except RuntimeError:
            pass
        self.ui.actionSave_datapackage.setDisabled(clean)
        self.ui.actionSave_All.setDisabled(clean)

    def showEvent(self, e):
        """Called when the form shows. Init datapackage
        (either from existing datapackage.json or by inferring a new one from sources)
        and update ui."""
        super().showEvent(e)
        self.load_datapackage()

    def load_datapackage(self):
        self.datapackage.infer(os.path.join(self._data_connection.data_dir, '*.csv'))
        if not self.datapackage.resources:
            self.msg_error.emit(
                "No resources found. Please add some CSV files to <b>{0}</b>. ".format(self._data_connection.data_dir)
            )
            return
        self.datapackage.update_descriptor(os.path.join(self._data_connection.data_dir, "datapackage.json"))
        self.resources_model.refresh_model()
        self.append_save_resource_actions()
        first_index = self.resources_model.index(0, 0)
        if not first_index.isValid():
            return
        self.ui.tableView_resources.selectionModel().setCurrentIndex(first_index, QItemSelectionModel.Select)

    @Slot(str)
    def refresh_datapackage(self, _path):
        if not self.datapackage.resources:
            self.load_datapackage()
            return
        self.datapackage.difference_infer(os.path.join(self._data_connection.data_dir, '*.csv'))
        self.append_save_resource_actions()
        self.resources_model.refresh_model()
        self.refresh_models()
        # TODO: Mark resources corresponding to removed files as dirty (*)

    def append_save_resource_actions(self):
        before = self.ui.actionSave_datapackage
        new_actions = []
        for resource_index in range(len(self._save_resource_actions), len(self.datapackage.resources)):
            resource = self.datapackage.resources[resource_index]
            action = QAction(f"Save '{os.path.basename(resource.source)}'")
            action.setEnabled(False)
            action.triggered.connect(
                lambda checked=False, resource_index=resource_index: self.save_resource(resource_index)
            )
            new_actions.append(action)
        self.ui.menuFile.insertActions(before, new_actions)
        self._save_resource_actions += new_actions

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("dataPackageWidget/windowSize")
        window_pos = self.qsettings.value("dataPackageWidget/windowPosition")
        window_maximized = self.qsettings.value("dataPackageWidget/windowMaximized", defaultValue='false')
        window_state = self.qsettings.value("dataPackageWidget/windowState")
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)
        original_size = self.size()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions

    @Slot()
    def _handle_menu_about_to_show(self):
        """Called when a menu from the menubar is about to show.
        Adjust infer action depending on whether or not we have a datapackage.
        Adjust copy paste actions depending on which widget has the focus.
        """
        # TODO Enable/disable action to save datapackage depending on status.
        self.ui.actionCopy.setText("Copy")
        self.ui.actionPaste.setText("Paste")
        self.ui.actionCopy.setEnabled(False)
        self.ui.actionPaste.setEnabled(False)
        if self.focusWidget() != self.ui.menubar:
            self.focus_widget = self.focusWidget()
        if self.focus_widget == self.ui.tableView_resources:
            focus_widget_name = "resources"
        elif self.focus_widget == self.ui.tableView_resource_data:
            focus_widget_name = "data"
        elif self.focus_widget == self.ui.tableView_fields:
            focus_widget_name = "fields"
        elif self.focus_widget == self.ui.tableView_foreign_keys:
            focus_widget_name = "foreign keys"
        else:
            return
        if not self.focus_widget.selectionModel().selection().isEmpty():
            self.ui.actionCopy.setText("Copy from {}".format(focus_widget_name))
            self.ui.actionCopy.setEnabled(True)
        if self.focus_widget.canPaste():
            self.ui.actionPaste.setText("Paste to {}".format(focus_widget_name))
            self.ui.actionPaste.setEnabled(True)

    @Slot(str)
    def add_message(self, msg):
        """Prepend regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        msg += "\t" + self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(msg, 5000)

    @Slot(str)
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show
        """
        self.err_msg.showMessage(msg)

    @Slot(bool)
    def save_all(self, checked=False):
        resource_paths = {
            k: r.source for k, r in enumerate(self.datapackage.resources) if self.datapackage.is_resource_dirty(k)
        }
        datapackage_path = os.path.join(self._data_connection.data_dir, "datapackage.json")
        all_paths = list(resource_paths.values()) + [datapackage_path]
        if not self.get_permission(*all_paths):
            return
        self._save_datapackage()
        for k, path in resource_paths.items():
            self._save_resource(k, path)

    @Slot(bool)
    def save_datapackage(self, checked=False):
        """Saves datapackage to file 'datapackage.json' in data directory."""
        filepath = os.path.join(self._data_connection.data_dir, "datapackage.json")
        if not self.get_permission(filepath):
            return
        self._save_datapackage()

    def _save_datapackage(self):
        if self.datapackage.save(os.path.join(self._data_connection.data_dir, 'datapackage.json')):
            msg = '"datapackage.json" saved in {}'.format(self._data_connection.data_dir)
            self.msg.emit(msg)
            self.undo_stack.setClean()
            return
        msg = 'Failed to save "datapackage.json" in {}'.format(self._data_connection.data_dir)
        self.msg_error.emit(msg)

    def save_resource(self, resource_index):
        resource = self.datapackage.resources[resource_index]
        filepath = resource.source
        if not self.get_permission(filepath):
            return
        self._save_resource(resource_index, filepath)

    def _save_resource(self, resource_index, filepath):
        headers = self.datapackage.resources[resource_index].schema.field_names
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for row in self.datapackage.resource_data(resource_index):
                writer.writerow(row)
        self.datapackage.clear_resource_data_backup(resource_index)
        self.resources_model.update_dirty(resource_index)

    def get_permission(self, *filepaths):
        start_dir = self._data_connection.data_dir
        filepaths = [os.path.relpath(path, start_dir) for path in filepaths if os.path.isfile(path)]
        pathlist = "".join([f"<li>{path}</li>" for path in filepaths])
        msg = f"Replacing file(s): <ul>{pathlist}</ul> in <b>{start_dir}</b>. <p>Are you sure?</p>"
        message_box = QMessageBox(
            QMessageBox.Question, "Replace file(s)", msg, QMessageBox.Ok | QMessageBox.Cancel, parent=self
        )
        message_box.button(QMessageBox.Ok).setText("Replace file(s)")
        return message_box.exec_() != QMessageBox.Cancel

    @Slot(bool)
    def copy(self, checked=False):
        """Copy data to clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.copy()
        except AttributeError:
            pass

    @Slot(bool)
    def paste(self, checked=False):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste()
        except AttributeError:
            pass

    @Slot("QModelIndex", "QModelIndex")
    def _handle_current_resource_changed(self, current, _previous):
        """Resets resource data and schema models whenever a new resource is selected."""
        self.refresh_models(current)

    def refresh_models(self, current=None):
        if current is None:
            current = self.ui.tableView_resources.selectionModel().currentIndex()
        if current.column() != 0 or current.row() == self.selected_resource_index:
            return
        self.selected_resource_index = current.row()
        self.resource_data_model.refresh_model(self.selected_resource_index)
        self.fields_model.refresh_model(self.selected_resource_index)
        self.foreign_keys_model.refresh_model(self.selected_resource_index)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.ui.tableView_fields.resizeColumnsToContents()
        self.ui.tableView_foreign_keys.resizeColumnsToContents()

    @Slot(int, bool)
    def _handle_resource_dirty_changed(self, resource_index, dirty):
        self._save_resource_actions[resource_index].setEnabled(dirty)

    @Slot("QModelIndex", "QModelIndex", list)
    def _handle_fields_data_changed(self, top_left, bottom_right, roles=()):
        top, left = top_left.row(), top_left.column()
        bottom, right = bottom_right.row(), bottom_right.column()
        if left <= 0 <= right:
            # Fields name changed
            self.resource_data_model.headerDataChanged.emit(Qt.Horizontal, top, bottom)
            self.ui.tableView_resource_data.resizeColumnsToContents()
            self.foreign_keys_model.emit_data_changed()

    def closeEvent(self, event=None):
        """Handle close event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("dataPackageWidget/windowSize", self.size())
        self.qsettings.setValue("dataPackageWidget/windowPosition", self.pos())
        self.qsettings.setValue("dataPackageWidget/windowState", self.saveState(version=1))
        self.qsettings.setValue("dataPackageWidget/windowMaximized", self.windowState() == Qt.WindowMaximized)
        self.qsettings.setValue("dataPackageWidget/n_screens", len(QGuiApplication.screens()))
        if event:
            event.accept()


class CustomPackage(Package):
    """Custom datapackage class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resource_data = [resource.read(cast=False) for resource in self.resources]
        self._resource_data_backup = {}

    def set_resource_data(self, resource_index, row, column, value):
        data_backup = self._resource_data_backup.setdefault(resource_index, {})
        if (row, column) not in data_backup:
            data_backup[row, column] = self._resource_data[resource_index][row][column]
        self._resource_data[resource_index][row][column] = value

    def resource_data(self, resource_index):
        return self._resource_data[resource_index]

    def is_resource_dirty(self, resource_index):
        return any(
            self._resource_data[resource_index][row][column] != value
            for (row, column), value in self._resource_data_backup.get(resource_index, {}).items()
        )

    def clear_resource_data_backup(self, resource_index):
        self._resource_data_backup.pop(resource_index, None)

    def add_resource(self, descriptor):
        resource = super().add_resource(descriptor)
        self._resource_data.append(resource.read(cast=False))
        return resource

    def difference_infer(self, path):
        current_resources = {r.source: r.name for r in self.resources}
        current_csv_files = set(glob.glob(path))
        old_resource_count = len(self.resources)
        new_resources = [
            self.add_resource({"path": csv_file}) for csv_file in current_csv_files - current_resources.keys()
        ]
        if not new_resources:
            return
        for k, resource in enumerate(new_resources):
            self.descriptor['resources'][old_resource_count + k] = resource.infer()
        self.commit()

    def rename_resource(self, index, new):
        self.descriptor['resources'][index]['name'] = new
        self.commit()

    def rename_field(self, resource_index, field_index, old, new):
        """Rename a field.
        """
        resource_dict = self.descriptor['resources'][resource_index]
        resource_dict['schema']['fields'][field_index]['name'] = new
        resource = self.resources[resource_index]
        for i, field in enumerate(resource.schema.primary_key):
            if field == old:
                resource_dict['schema']['primaryKey'][i] = new
        for i, foreign_key in enumerate(resource.schema.foreign_keys):
            for j, field in enumerate(foreign_key["fields"]):
                if field == old:
                    resource_dict['schema']['foreignKeys'][i]['fields'][j] = new
            for j, field in enumerate(foreign_key['reference']['fields']):
                if field == old:
                    resource_dict['schema']['foreignKeys'][i]['reference']['fields'][j] = new
        self.commit()

    def append_to_primary_key(self, resource_index, field_index):
        """Append field to resources's primary key."""
        schema = self.descriptor['resources'][resource_index]['schema']
        primary_key = schema.setdefault('primaryKey', [])
        field_name = schema["fields"][field_index]["name"]
        if field_name not in primary_key:
            primary_key.append(field_name)
        self.commit()

    def remove_from_primary_key(self, resource_index, field_index):
        """Remove field from resources's primary key."""
        schema = self.descriptor['resources'][resource_index]['schema']
        primary_key = schema.get('primaryKey')
        if not primary_key:
            return
        field_name = schema["fields"][field_index]["name"]
        if field_name in primary_key:
            primary_key.remove(field_name)
        self.commit()

    def check_foreign_key(self, resource_index, foreign_key):
        """Check foreign key."""
        resource = self.resources[resource_index]
        try:
            fields = foreign_key["fields"]
            reference = foreign_key["reference"]
        except KeyError as e:
            raise DataPackageException(f"{e} missing.")
        try:
            reference_resource = reference["resource"]
            reference_fields = reference["fields"]
        except KeyError as e:
            raise DataPackageException(f"Reference {e} missing.")
        if len(fields) != len(reference_fields):
            raise DataPackageException("Both 'fields' and 'reference_fields' must have the same length.")
        missing_fields = [fn for fn in fields if fn not in resource.schema.field_names]
        if missing_fields:
            raise DataPackageException(f"Fields {missing_fields} not in {resource.name}'s schema.")
        reference_resource_obj = self.get_resource(reference_resource)
        if not reference_resource_obj:
            raise DataPackageException(f"Resource {reference_resource} not in datapackage")
        missing_ref_fields = [fn for fn in reference_fields if fn not in reference_resource_obj.schema.field_names]
        if missing_ref_fields:
            raise DataPackageException(f"Fields {missing_ref_fields} not in {reference_resource}'s schema.")
        fks = self.descriptor['resources'][resource_index]['schema'].get('foreignKeys', [])
        if foreign_key in fks:
            raise DataPackageException(f"Foreign key already in {resource.name}'s schema.")

    def add_foreign_key(self, resource_index, foreign_key):
        fks = self.descriptor['resources'][resource_index]['schema'].setdefault('foreignKeys', [])
        fks.append(foreign_key)
        self.commit()

    def update_foreign_key(self, resource_index, fk_index, foreign_key):
        fks = self.descriptor['resources'][resource_index]['schema'].get('foreignKeys', [])
        fks[fk_index] = foreign_key
        self.commit()

    def remove_foreign_key(self, resource_index, fk_index):
        self.descriptor['resources'][resource_index]['schema']['foreignKeys'].pop(fk_index)
        self.commit()

    def update_descriptor(self, descriptor_filepath):
        """Updates this package's schema from other package's."""
        if not os.path.isfile(descriptor_filepath):
            return
        other_datapackage = Package(descriptor_filepath)
        for resource in self.descriptor["resources"]:
            other_resource = other_datapackage.get_resource(resource["name"])
            if other_resource is None:
                continue
            other_schema = other_resource.schema
            resource["schema"]["primaryKey"] = other_schema.primary_key
            resource["schema"]["foreignKeys"] = other_schema.foreign_keys
        self.commit()
