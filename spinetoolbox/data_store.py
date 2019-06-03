######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Module for data store class.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   18.12.2017
"""

import sys
import os
import getpass
import logging
import fnmatch
from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Slot, QUrl, Qt
from PySide2.QtWidgets import QMessageBox, QFileDialog, QApplication, QCheckBox
from project_item import ProjectItem
from widgets.data_store_widgets import TreeViewForm, GraphViewForm
from widgets.tabular_view_widget import TabularViewForm
from graphics_items import DataStoreIcon
from helpers import create_dir, busy_effect
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError, DatabaseError, ArgumentError
from sqlalchemy.engine.url import make_url, URL
import qsubprocess
import spinedb_api


class DataStore(ProjectItem):
    """Data Store class.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        url (str or dict): SQLAlchemy url
        x (int): Initial X coordinate of item icon
        y (int): Initial Y coordinate of item icon
    """

    def __init__(self, toolbox, name, description, url, x, y):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project = self._toolbox.project()
        self.item_type = "Data Store"
        self._url = self.parse_url(url)
        self.tree_view_form = None
        self.graph_view_form = None
        self.tabular_view_form = None
        # Make project directory for this Data Store
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )
        self._graphics_item = DataStoreIcon(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self._sigs = self.make_signal_handler_dict()

    def parse_url(self, url):
        """Return a complete url dictionary from the given dict or string"""
        base_url = dict(dialect=None, username=None, password=None, host=None, port=None, database=None)
        if isinstance(url, dict):
            base_url.update(url)
        elif isinstance(url, str):
            sa_url = make_url(url)
            base_url["dialect"] = sa_url.get_dialect().name
            base_url.update(sa_url.translate_connect_args())
        else:
            self._toolbox.msg_error.emit(
                "Unable to parse URL for <b>{0}</b>: unsupported type '{1}'".format(self.name, type(url))
            )
        return base_url

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = dict()
        s[self._toolbox.ui.toolButton_ds_open_dir.clicked] = self.open_directory
        s[self._toolbox.ui.pushButton_ds_tree_view.clicked] = self.open_tree_view
        s[self._toolbox.ui.pushButton_ds_graph_view.clicked] = self.open_graph_view
        s[self._toolbox.ui.pushButton_ds_tabular_view.clicked] = self.open_tabular_view
        s[self._toolbox.ui.toolButton_open_sqlite_file.clicked] = self.open_sqlite_file
        s[self._toolbox.ui.pushButton_create_new_spine_db.clicked] = self.create_new_spine_database
        s[self._toolbox.ui.toolButton_copy_url.clicked] = self.copy_url
        s[self._toolbox.ui.comboBox_dialect.currentTextChanged] = self.refresh_dialect
        s[self._toolbox.ui.lineEdit_database.file_dropped] = self.set_path_to_sqlite_file
        s[self._toolbox.ui.lineEdit_username.textChanged] = self.refresh_username
        s[self._toolbox.ui.lineEdit_password.textChanged] = self.refresh_password
        s[self._toolbox.ui.lineEdit_host.textChanged] = self.refresh_host
        s[self._toolbox.ui.lineEdit_port.textChanged] = self.refresh_port
        s[self._toolbox.ui.lineEdit_database.textChanged] = self.refresh_database
        return s

    def activate(self):
        """Load url into selections and connect signals."""
        self._toolbox.ui.label_ds_name.setText(self.name)
        self.load_url_into_selections()  # Do this before connecting signals or funny things happen
        super().connect_signals()

    def deactivate(self):
        """Disconnect signals."""
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        return True

    def set_url(self, url):
        """Set url attribute. Used by Tool when passing on results."""
        self._url = self.parse_url(url)

    def url(self):
        """Return the url attribute, for saving the project."""
        return self._url

    def make_url(self, log_errors=True):
        """Return a sqlalchemy url from the current url attribute or None if not valid."""
        if not self._url:
            log_errors and self._toolbox.msg_error.emit(
                "No URL specified for <b>{0}</b>. Please specify one and try again".format(self.name)
            )
            return None
        try:
            url_copy = dict(self._url)
            dialect = url_copy.pop("dialect")
            if not dialect:
                log_errors and self._toolbox.msg_error.emit(
                    "Unable to generate URL from <b>{0}</b>: invalid dialect {1}. "
                    "Please select a new dialect and try again.".format(self._url, dialect)
                )
                return
            if dialect == 'sqlite':
                url = URL('sqlite', **url_copy)
            else:
                db_api = spinedb_api.SUPPORTED_DIALECTS[dialect]
                drivername = f"{dialect}+{db_api}"
                url = URL(drivername, **url_copy)
        except (ArgumentError, ValueError) as e:  # TODO: make sure these are the exceptions we wanna handle here
            log_errors and self._toolbox.msg_error.emit(
                "Invalid URL <b>{0}</b>: {1}. "
                "Please make new selections and try again.".format(url, e)
            )
            return None
        if not url.database:
            log_errors and self._toolbox.msg_error.emit(
                "Invalid URL <b>{0}</b>: no database specified. "
                "Please specify a database and try again.".format(url)
            )
            return None
        # Small hack to make sqlite paths relative to this DS directory
        if dialect == "sqlite" and not os.path.isabs(url.database):
            url.database = os.path.join(self.data_dir, url.database)
            self._toolbox.ui.lineEdit_database.setText(url.database)
        return url

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    def set_icon(self, icon):
        """Set the icon."""
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this Data Store on the scene."""
        return self._graphics_item

    @Slot("QString", name="set_path_to_sqlite_file")
    def set_path_to_sqlite_file(self, file_path):
        """Set path to SQLite file."""
        self._toolbox.ui.lineEdit_database.setText(file_path)

    @Slot(bool, name='open_sqlite_file')
    def open_sqlite_file(self, checked=False):
        """Open file browser where user can select the path to an SQLite
        file that they want to use."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self._toolbox, 'Select SQlite file', self.data_dir)
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        # Update UI
        self._toolbox.ui.lineEdit_database.setText(file_path)

    def load_url_into_selections(self):
        """Load url attribute into shared widget selections. 
        Used when activating the item, and creating a new Spine db."""
        # TODO: Test what happens when Tool item calls this and this item is selected.
        self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.lineEdit_host.clear()
        self._toolbox.ui.lineEdit_port.clear()
        self._toolbox.ui.lineEdit_database.clear()
        self._toolbox.ui.lineEdit_username.clear()
        self._toolbox.ui.lineEdit_password.clear()
        if not self._url:
            return
        dialect = self._url["dialect"]
        if not self.check_dialect(dialect):
            return
        self._toolbox.ui.comboBox_dialect.setCurrentText(dialect)
        if self._url["host"]:
            self._toolbox.ui.lineEdit_host.setText(self._url["host"])
        if self._url["port"]:
            self._toolbox.ui.lineEdit_port.setText(str(self._url["port"]))
        if self._url["database"]:
            self._toolbox.ui.lineEdit_database.setText(self._url["database"])
        if self._url["username"]:
            self._toolbox.ui.lineEdit_username.setText(self._url["username"])
        if self._url["password"]:
            self._toolbox.ui.lineEdit_password.setText(self._url["password"])

    @Slot("QString", name="refresh_host")
    def refresh_host(self, host=""):
        """Refresh host from selections."""
        if not host:
            host = None
        self._url["host"] = host

    @Slot("QString", name="refresh_port")
    def refresh_port(self, port=""):
        """Refresh port from selections."""
        if not port:
            port = None
        self._url["port"] = port

    @Slot("QString", name="refresh_database")
    def refresh_database(self, database=""):
        """Refresh database from selections."""
        if not database:
            database = None
        self._url["database"] = database

    @Slot("QString", name="refresh_username")
    def refresh_username(self, username=""):
        """Refresh username from selections."""
        if not username:
            username = None
        self._url["username"] = username

    @Slot("QString", name="refresh_password")
    def refresh_password(self, password=""):
        """Refresh password from selections."""
        if not password:
            password = None
        self._url["password"] = password

    @Slot("QString", name="refresh_dialect")
    def refresh_dialect(self, dialect=""):
        if self.check_dialect(dialect):
            self._url["dialect"] = dialect
        else:
            self._toolbox.msg_error.emit("Unable to use dialect '{}'.".format(dialect))
            self._url["dialect"] = None

    def enable_no_dialect(self):
        """Adjust widget enabled status to default when no dialect is selected."""
        self._toolbox.ui.comboBox_dialect.setEnabled(True)
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(False)
        self._toolbox.ui.lineEdit_password.setEnabled(False)

    def enable_mssql(self):
        """Adjust controls to mssql connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(True)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(False)
        self._toolbox.ui.lineEdit_username.setEnabled(True)
        self._toolbox.ui.lineEdit_password.setEnabled(True)

    def enable_sqlite(self):
        """Adjust controls to sqlite connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(True)
        self._toolbox.ui.lineEdit_host.setEnabled(False)
        self._toolbox.ui.lineEdit_port.setEnabled(False)
        self._toolbox.ui.lineEdit_database.setEnabled(True)
        self._toolbox.ui.lineEdit_username.setEnabled(False)
        self._toolbox.ui.lineEdit_password.setEnabled(False)

    def enable_common(self):
        """Adjust controls to 'common' connection specification."""
        self._toolbox.ui.comboBox_dsn.setEnabled(False)
        self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
        self._toolbox.ui.toolButton_open_sqlite_file.setEnabled(False)
        self._toolbox.ui.lineEdit_host.setEnabled(True)
        self._toolbox.ui.lineEdit_port.setEnabled(True)
        self._toolbox.ui.lineEdit_database.setEnabled(True)
        self._toolbox.ui.lineEdit_username.setEnabled(True)
        self._toolbox.ui.lineEdit_password.setEnabled(True)

    def check_dialect(self, dialect):
        """Check if selected dialect is supported. Offer to install DBAPI if not.

        Returns:
            True if dialect is supported, False if not.
        """
        if dialect not in spinedb_api.SUPPORTED_DIALECTS:
            self.enable_no_dialect()
            return False
        dbapi = spinedb_api.SUPPORTED_DIALECTS[dialect]
        try:
            if dialect == 'sqlite':
                create_engine('sqlite://')
                self.enable_sqlite()
            elif dialect == 'mssql':
                import pyodbc

                dsns = pyodbc.dataSources()
                # Collect dsns which use the msodbcsql driver
                mssql_dsns = list()
                for key, value in dsns.items():
                    if 'msodbcsql' in value.lower():
                        mssql_dsns.append(key)
                if mssql_dsns:
                    self._toolbox.ui.comboBox_dsn.clear()
                    self._toolbox.ui.comboBox_dsn.addItems(mssql_dsns)
                    self._toolbox.ui.comboBox_dsn.setCurrentIndex(-1)
                    self.enable_mssql()
                else:
                    msg = "Please create a SQL Server ODBC Data Source first."
                    self._toolbox.msg_warning.emit(msg)
            else:
                create_engine(f"{dialect}+{dbapi}://")
                self.enable_common()
            return True
        except ModuleNotFoundError:
            dbapi = spinedb_api.SUPPORTED_DIALECTS[dialect]
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Dialect not supported")
            msg.setText(
                "There is no DBAPI installed for dialect '{0}'. " "The default one is '{1}'.".format(dialect, dbapi)
            )
            msg.setInformativeText("Do you want to install it using pip or conda?")
            pip_button = msg.addButton("pip", QMessageBox.YesRole)
            conda_button = msg.addButton("conda", QMessageBox.NoRole)
            msg.addButton("Cancel", QMessageBox.RejectRole)
            msg.exec_()  # Show message box
            if msg.clickedButton() == pip_button:
                if not self.install_dbapi_pip(dbapi):
                    self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                    return False
            elif msg.clickedButton() == conda_button:
                if not self.install_dbapi_conda(dbapi):
                    self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                    return False
            else:
                self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                return False
            # Check dialect again to see how it went
            if not self.check_dialect(dialect):
                self._toolbox.ui.comboBox_dialect.setCurrentIndex(-1)
                return False
            return True

    @busy_effect
    def install_dbapi_pip(self, dbapi):
        """Install DBAPI using pip."""
        self._toolbox.msg.emit("Installing module <b>{0}</b> using pip".format(dbapi))
        program = sys.executable
        args = list()
        args.append("-m")
        args.append("pip")
        args.append("install")
        args.append("{0}".format(dbapi))
        pip_install = qsubprocess.QSubProcess(self._toolbox, program, args)
        pip_install.start_process()
        if pip_install.wait_for_finished():
            self._toolbox.msg_success.emit("Module <b>{0}</b> successfully installed".format(dbapi))
            return True
        self._toolbox.msg_error.emit("Installing module <b>{0}</b> failed".format(dbapi))
        return False

    @busy_effect
    def install_dbapi_conda(self, dbapi):
        """Install DBAPI using conda. Fails if conda is not installed."""
        try:
            import conda.cli
        except ImportError:
            self._toolbox.msg_error.emit("Conda not found. Installing {0} failed.".format(dbapi))
            return False
        try:
            self._toolbox.msg.emit("Installing module <b>{0}</b> using Conda".format(dbapi))
            conda.cli.main('conda', 'install', '-y', dbapi)
            self._toolbox.msg_success.emit("Module <b>{0}</b> successfully installed".format(dbapi))
            return True
        except Exception:
            self._toolbox.msg_error.emit("Installing module <b>{0}</b> failed".format(dbapi))
            return False

    @busy_effect
    def get_db_map(self, url, upgrade=False):
        """Return a DiffDatabaseMapping instance to work with.
        """
        try:
            db_map = spinedb_api.DiffDatabaseMapping(url, upgrade=upgrade)
            return db_map
        except spinedb_api.SpineDBVersionError:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Incompatible database version")
            msg.setText(
                "The database at <b>{}</b> is from an older version of Spine "
                "and needs to be upgraded in order to be used with the current version.".format(url)
            )
            msg.setInformativeText(
                "Do you want to upgrade it now?"
                "<p><b>WARNING</b>: After the upgrade, "
                "the database may no longer be used "
                "with previous versions of Spine."
            )
            msg.addButton(QMessageBox.Cancel)
            msg.addButton("Upgrade", QMessageBox.YesRole)
            ret = msg.exec_()  # Show message box
            if ret == QMessageBox.Cancel:
                return None
            return self.get_db_map(url, upgrade=True)
        except spinedb_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)
            return None

    @Slot(bool, name="open_tree_view")
    def open_tree_view(self, checked=False):
        """Open url in tree view form."""
        url = self.make_url()
        if not url:
            return
        if self.tree_view_form:
            # If the url hasn't changed, just raise the current form
            if self.tree_view_form.db_map.db_url == url:
                if self.tree_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.tree_view_form.setWindowState(
                        self.tree_view_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                    )
                    self.tree_view_form.activateWindow()
                else:
                    self.tree_view_form.raise_()
                return
            self.tree_view_form.destroyed.disconnect(self.tree_view_form_destroyed)
            self.tree_view_form.close()
        db_map = self.get_db_map(url)
        if not db_map:
            return
        self.do_open_tree_view(db_map, url.database)

    @busy_effect
    def do_open_tree_view(self, db_map, database):
        """Open url in tree view form."""
        self.tree_view_form = TreeViewForm(self, db_map, database)
        self.tree_view_form.show()
        self.tree_view_form.destroyed.connect(self.tree_view_form_destroyed)

    @Slot(name="tree_view_form_destroyed")
    def tree_view_form_destroyed(self):
        """Notify that tree view form has been destroyed."""
        self.tree_view_form = None

    @Slot(bool, name="open_graph_view")
    def open_graph_view(self, checked=False):
        """Open url in graph view form."""
        url = self.make_url()
        if not url:
            return
        if self.graph_view_form:
            # If the url hasn't changed, just raise the current form
            if self.graph_view_form.db_map.db_url == url:
                if self.graph_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.graph_view_form.setWindowState(
                        self.graph_view_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                    )
                    self.graph_view_form.activateWindow()
                else:
                    self.graph_view_form.raise_()
                return
            self.graph_view_form.destroyed.disconnect(self.graph_view_form_destroyed)
            self.graph_view_form.close()
        db_map = self.get_db_map(url)
        if not db_map:
            return
        self.do_open_graph_view(db_map, url.database)

    @busy_effect
    def do_open_graph_view(self, db_map, database):
        """Open url in graph view form."""
        self.graph_view_form = GraphViewForm(self, db_map, database, read_only=False)
        self.graph_view_form.show()
        self.graph_view_form.destroyed.connect(self.graph_view_form_destroyed)

    @Slot(name="graph_view_form_destroyed")
    def graph_view_form_destroyed(self):
        """Notify that graph view form has been destroyed."""
        self.graph_view_form = None

    @Slot(bool, name="open_tabular_view")
    def open_tabular_view(self, checked=False):
        """Open url in Data Store tabular view."""
        url = self.make_url()
        if not url:
            return
        if self.tabular_view_form:
            # If the url hasn't changed, just raise the current form
            if self.tabular_view_form.db_map.db_url == url:
                if self.tabular_view_form.windowState() & Qt.WindowMinimized:
                    # Remove minimized status and restore window with the previous state (maximized/normal state)
                    self.tabular_view_form.setWindowState(
                        self.tabular_view_form.windowState() & ~Qt.WindowMinimized | Qt.WindowActive
                    )
                    self.tabular_view_form.activateWindow()
                else:
                    self.tabular_view_form.raise_()
                return
            self.tabular_view_form.destroyed.disconnect(self.tabular_view_form_destroyed)
            self.tabular_view_form.close()
        db_map = self.get_db_map(url)
        if not db_map:
            return
        self.do_open_tabular_view(db_map, url.database)

    @busy_effect
    def do_open_tabular_view(self, db_map, database):
        """Open url in tabular view form."""
        self.tabular_view_form = TabularViewForm(self, db_map, database)
        self.tabular_view_form.destroyed.connect(self.tabular_view_form_destroyed)
        self.tabular_view_form.show()

    @Slot(name="tabular_view_form_destroyed")
    def tabular_view_form_destroyed(self):
        self.tabular_view_form = None

    @Slot(bool, name="open_directory")
    def open_directory(self, checked=False):
        """Open file explorer in this Data Store's data directory."""
        url = "file:///" + self.data_dir
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(url, QUrl.TolerantMode))
        if not res:
            self._toolbox.msg_error.emit("Failed to open directory: {0}".format(self.data_dir))

    def data_files(self):
        """Return a list of files that are in this items data directory."""
        if not os.path.isdir(self.data_dir):
            return None
        return os.listdir(self.data_dir)

    def find_file(self, fname, visited_items):
        """Search for filename in data and return the path if found."""
        # logging.debug("Looking for file {0} in DS {1}.".format(fname, self.name))
        if self in visited_items:
            self._toolbox.msg_warning.emit(
                "There seems to be an infinite loop in your project. Please fix the "
                "connections and try again. Detected at {0}.".format(self.name)
            )
            return None
        url = self.make_url()
        if not url:
            # Data Store has no valid url
            return None
        if not url.drivername.lower().startswith('sqlite'):
            return None
        file_path = os.path.abspath(url.database)
        if not os.path.exists(file_path):
            return None
        if fname == os.path.basename(file_path):
            # logging.debug("{0} found in DS {1}".format(fname, self.name))
            self._toolbox.msg.emit("\t<b>{0}</b> found in Data Store <b>{1}</b>".format(fname, self.name))
            return file_path
        visited_items.append(self)
        for input_item in self._toolbox.connection_model.input_items(self.name):
            # Find item from project model
            item_index = self._toolbox.project_item_model.find_item(input_item)
            if not item_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(item_index)
            if item.item_type in ["Data Store", "Data Connection"]:
                path = item.find_file(fname, visited_items)
                if path is not None:
                    return path
        return None

    def find_files(self, pattern, visited_items):
        """Search for files matching the given pattern (with wildcards) in data directory
        and return a list of matching paths.

        Args:
            pattern (str): File name (no path). May contain wildcards.
            visited_items (list): List of project item names that have been visited

        Returns:
            List of matching paths. List is empty if no matches found.
        """
        paths = list()
        if self in visited_items:
            self._toolbox.msg_warning.emit(
                "There seems to be an infinite loop in your project. Please fix the "
                "connections and try again. Detected at {0}.".format(self.name)
            )
            return paths
        # Check the current url. If it is an sqlite file, this is a possible match
        # If dialect is not sqlite, the url is ignored
        url = self.make_url()
        if url and url.drivername.lower().startswith('sqlite'):
            file_path = os.path.abspath(url.database)
            if os.path.exists(file_path):
                if fnmatch.fnmatch(file_path, pattern):  # fname == os.path.basename(file_path):
                    # self._toolbox.msg.emit("\t<b>{0}</b> found in Data Store <b>{1}</b>".format(fname, self.name))
                    paths.append(file_path)
        else:  # Not an SQLite url
            pass
        # Search files that match the pattern from this Data Store's data directory
        for data_file in self.data_files():  # data_file is a filename (no path)
            if fnmatch.fnmatch(data_file, pattern):
                # self._toolbox.msg.emit("\t<b>{0}</b> matches pattern <b>{1}</b> in Data Store <b>{2}</b>"
                #                        .format(data_file, pattern, self.name))
                path = os.path.join(self.data_dir, data_file)
                if path not in paths:  # Skip if the sqlite file was already added from the url
                    paths.append(path)
        visited_items.append(self)
        # Find items that are connected to this Data Connection
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if item.item_type in ["Data Store", "Data Connection"]:
                matching_paths = item.find_files(pattern, visited_items)
                if matching_paths is not None:
                    paths = paths + matching_paths
                    return paths
        return paths

    @Slot(bool, name="copy_url")
    def copy_url(self, checked=False):
        """Copy db url to clipboard."""
        url = self.make_url()
        url.password = None
        QApplication.clipboard().setText(str(url))
        self._toolbox.msg.emit("Database url '{}' successfully copied to clipboard.".format(url))

    @Slot(bool, name="create_new_spine_database")
    def create_new_spine_database(self, checked=False):
        """Create new (empty) Spine database."""
        for_spine_model = self._toolbox.ui.checkBox_for_spine_model.isChecked()
        url = self.make_url()
        if not url:
            return
        try:
            if not spinedb_api.is_empty(url):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Question)
                msg.setWindowTitle("Database not empty")
                msg.setText("The database at <b>'{0}'</b> is not empty.".format(url))
                msg.setInformativeText("Do you want to overwrite it?")
                overwrite_button = msg.addButton("Overwrite", QMessageBox.AcceptRole)
                msg.addButton("Cancel", QMessageBox.RejectRole)
                ret = msg.exec_()  # Show message box
                if ret != QMessageBox.AcceptRole:
                    return
            spinedb_api.create_new_spine_database(url, for_spine_model=for_spine_model)
            self._toolbox.msg.emit("New Spine db successfully created at '{0}'.".format(url))
        except spinedb_api.SpineDBAPIError as e:
            self._toolbox.msg_error.emit("Unable to create new Spine db at '{0}': {1}.".format(url, e))

    def update_name_label(self):
        """Update Data Store tab name label. Used only when renaming project items."""
        self._toolbox.ui.label_ds_name.setText(self.name)
