######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains DataInterface class.

:authors: P. Savolainen (VTT)
:date:   10.6.2019
"""

import logging
import os
from PySide2.QtCore import Qt, Slot, Signal, QUrl, QFileInfo
from PySide2.QtGui import QDesktopServices, QStandardItem, QStandardItemModel
from PySide2.QtWidgets import QFileIconProvider, QMainWindow
from project_item import ProjectItem
from graphics_items import DataInterfaceIcon
from helpers import create_dir, create_log_file_timestamp
from spine_io.importers.csv_reader import CSVConnector
from widgets.import_preview_window import ImportPreviewWindow


class DataInterface(ProjectItem):
    """DataInterface class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Project item name
        description (str): Project item description
        filepath (str): Path to file
        settings (dict): dict with mapping settings
        x (int): Initial icon scene X coordinate
        y (int): Initial icon scene Y coordinate
    """

    data_interface_refresh_signal = Signal(name="data_interface_refresh_signal")

    def __init__(self, toolbox, name, description, filepath, settings, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Data Interface"
        # Make data directory and logs subdirectory for this item
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        self.logs_dir = os.path.join(self.data_dir, "logs")
        try:
            create_dir(self.data_dir)
            create_dir(self.logs_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed. Check permissions.".format(self.data_dir)
            )
        # Variables for saving selections when item is (de)activated
        self.settings = settings
        self.file_model = QStandardItemModel()
        self._graphics_item = DataInterfaceIcon(self._toolbox, x - 35, y - 35, w=70, h=70, name=self.name)
        # NOTE: data_interface_refresh_signal is not shared with other proj. items so there's no need to disconnect it
        self.data_interface_refresh_signal.connect(self.refresh)
        self._sigs = self.make_signal_handler_dict()
        # connector class
        self._preview_widget = None

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_di_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.pushButton_import_editor.clicked] = self.open_import_editor
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Saves selections and disconnects signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed.", self.name)
            return False
        return True

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_di_name.setText(self.name)
        self._toolbox.ui.treeView_data_interface_files.setModel(self.file_model)
        self.refresh()

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""
        self._toolbox.ui.treeView_data_interface_files.setModel(None)

    def get_icon(self):
        """Returns the graphics item representing this data interface on scene."""
        return self._graphics_item

    def update_name_label(self):
        """Update Data Interface tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_di_name.setText(self.name)

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Opens file explorer in Data Interface directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    @Slot(bool, name="open_import_editor")
    def open_import_editor(self, checked=False):
        """Opens Import editor for the file selected into line edit."""
        importee = self._toolbox.ui.treeView_data_interface_files.currentIndex().data()
        if importee is None:
            self._toolbox.msg_error.emit("Please select a file from the list first.")
            return
        if not os.path.exists(importee):
            self._toolbox.msg_error.emit("Invalid path: {0}".format(importee))
            return
        self._toolbox.msg.emit("Opening Import editor for file: {0}".format(importee))

        if self._preview_widget:
            if self._preview_widget.windowState() & Qt.WindowMinimized:
                # Remove minimized status and restore window with the previous state (maximized/normal state)
                self._preview_widget.setWindowState(
                    self._preview_widget.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                )
                self._preview_widget.activateWindow()
            else:
                self._preview_widget.raise_()
            return
        self._preview_widget = ImportPreviewWindow(importee, self.settings, self._toolbox._qsettings)
        self._preview_widget.settings_updated.connect(self.save_settings)
        self._preview_widget.connection_failed.connect(self._connection_failed)
        self._preview_widget.destroyed.connect(self._preview_destroyed)
        self._preview_widget.start_ui()

    @Slot("QString", name="_connection_failed")
    def _connection_failed(self, msg):
        self._toolbox.msg.emit(msg)
        self._preview_widget.close()
        self._preview_widget = None

    @Slot(dict, name="save_settings")
    def save_settings(self, settings):
        self.settings = settings

    @Slot(name="_preview_destroyed")
    def _preview_destroyed(self):
        self._preview_widget = None

    def update_file_model(self, items):
        """Add given list of items to the file model. If None or
        an empty list given, the model is cleared."""
        self.file_model.clear()
        self.file_model.setHorizontalHeaderItem(0, QStandardItem("Files"))  # Add header
        if items is not None:
            for item in items:
                qitem = QStandardItem(item)
                qitem.setEditable(False)
                qitem.setCheckable(True)
                qitem.setData(QFileIconProvider().icon(QFileInfo(item)), Qt.DecorationRole)
                self.file_model.appendRow(qitem)

    @Slot(name="refresh")
    def refresh(self):
        """Update the list of files that this item is viewing."""
        file_list = list()
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if item.item_type != "Data Connection":
                continue
            files = item.data_files()
            file_list += files
            refs = item.file_references()
            file_list += refs
        self.update_file_model(file_list)

    def execute(self):
        """Executes this Data Interface."""
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Data Interface <b>{0}</b>".format(self.name))
        self._toolbox.msg.emit("***")

        inst = self._toolbox.project().execution_instance

        if self.settings.get("source", ""):
            connector = CSVConnector()
            connector.connect_to_source(self.settings["source"])
            data, errors = connector.get_mapped_data(
                self.settings["table_mappings"], self.settings["table_options"], max_rows=-1
            )
            self._toolbox.msg.emit(
                "<b>{0}:</b> Read {1} data with {2} errors".format(
                    self.name, sum(len(d) for d in data.values()), len(errors)
                )
            )
            if errors:
                # Log errors in a time stamped file into the logs directory
                timestamp = create_log_file_timestamp()
                logfilepath = os.path.abspath(os.path.join(self.logs_dir, timestamp + "_error.log"))
                with open(logfilepath, 'w') as f:
                    for err in errors:
                        f.write("{}\n".format(err))
                # Make error log file anchor with path as tooltip
                logfile_anchor = (
                    "<a style='color:#BB99FF;' title='"
                    + logfilepath
                    + "' href='file:///"
                    + logfilepath
                    + "'>error log</a>"
                )
                self._toolbox.msg_error.emit(
                    "There where errors while executing <b>{0}</b>. {1}".format(self.name, logfile_anchor)
                )
                self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(-1)
                return
            # Add mapped data to a dict in the execution instance.
            # If execution reaches a Data Store, the mapped data will be imported into the corresponding url
            inst.add_di_data(self.name, data)
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(0)  # 0 success

    def stop_execution(self):
        """Stops executing this Data Interface."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))
