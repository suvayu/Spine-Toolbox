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
Contains ProjectUpgrader class used in upgrading and converting projects
and project dicts from earlier versions to the latest version.

:authors: P. Savolainen (VTT)
:date:   8.11.2019
"""

import logging
import os
import shutil
import json
from PySide2.QtWidgets import QFileDialog, QMessageBox
from .config import LATEST_PROJECT_VERSION
from .helpers import recursive_overwrite, create_dir


class ProjectUpgrader:
    """Class to upgrade/convert projects from earlier versions to the current version."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): toolbox of this project
        """
        self._toolbox = toolbox

    def upgrade(self, project_dict):
        """Converts the project described in given project description file to the latest version.

        Args:
            project_dict (dict): Full path to project description file, ie. .proj or .json

        Returns:
            dict: Latest version of the project info dictionary
        """
        try:
            v = project_dict["project"]["version"]
        except KeyError:
            return self.upgrade_from_no_version_to_version_1(project_dict)
        return self.upgrade_to_latest(v, project_dict)

    @staticmethod
    def upgrade_to_latest(v, project_dict):
        """Upgrades the given project dictionary to the latest version.

        NOTE: Implement this when the structure of the project file needs
        to be changed.

        Args:
            v (int): project version
            project_dict (dict): Project JSON to be converted

        Returns:
            dict: Upgraded project information JSON
        """
        logging.debug("Implementation of upgrading project JSON from version {0}->{1} is missing"
                      .format(v, LATEST_PROJECT_VERSION))
        raise NotImplementedError

    @staticmethod
    def upgrade_from_no_version_to_version_1(old):
        """Converts project information dictionaries without 'version' to version 1.

        Args:
            old (dict): Project information JSON

        Returns:
             dict: Project information JSON upgraded to version 1
        """
        new = dict()
        new["version"] = 1
        new["name"] = old["project"]["name"]
        new["description"] = old["project"]["description"]
        new["work_dir"] = old["project"]["work_dir"]  # TODO: Make work_dir global
        new["tool_specifications"] = old["project"]["tool_specifications"]
        try:
            new["tool_specifications"] = old["project"]["tool_specifications"]
        except KeyError:
            try:
                new["tool_specifications"] = old["project"]["tool_templates"]
            except KeyError:
                new["tool_specifications"] = list()
        new["connections"] = old["project"]["connections"]
        try:
            new["connections"] = old["project"]["connections"]
        except KeyError:
            new["connections"] = list()
        new["scene_x"] = old["project"]["scene_x"]
        new["scene_y"] = old["project"]["scene_y"]
        new["scene_w"] = old["project"]["scene_w"]
        new["scene_h"] = old["project"]["scene_h"]
        return dict(project=new, objects=old["objects"])

    def open_proj_json(self, proj_file_path):
        """Opens an old style project file (.proj) for reading,

        Args:
            proj_file_path (str): Full path to the old .proj project file

        Returns:
            dict: Upgraded project information JSON or None if the operation failed
        """
        try:
            with open(proj_file_path, "r") as fh:
                try:
                    proj_info = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self._toolbox.msg_error.emit(
                        "Error in project file <b>{0}</b>. Invalid JSON. {0}".format(proj_file_path))
                    return None
        except OSError:
            self._toolbox.msg_error.emit("Opening project file <b>{0}</b> failed".format(proj_file_path))
            return None
        return proj_info

    def get_project_directory(self):
        """Asks the user to select a new project directory. If the selected directory
        is already a Spine Toolbox project directory, asks if overwrite is ok. Used
        when opening a project from an old style project file (.proj).

        Returns:
            str: Path to project directory or an empty string if operation is canceled.
        """
        msg = "Please select a directory for the upgraded project." \
              "\n\nProject item data will be copied to the new project directory." \
              "\n\nNote that you may need to manually update some project items " \
              "to accommodate for the new project structure. E.g. Data Store Database paths " \
              "are not updated automatically."
        QMessageBox.information(self._toolbox, "Project needs to be upgraded", msg)
        # Ask user for a new directory where to save the project
        answer = QFileDialog.getExistingDirectory(
            self._toolbox, "Select a project directory", os.path.abspath("C:\\")
        )
        if not answer:  # Canceled (american-english), cancelled (british-english)
            return ""
        if not os.path.isdir(answer):  # Check that it's a directory
            msg = "Selection is not a directory, please try again"
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self._toolbox, "Invalid selection", msg)
            return ""
        # Check if the selected directory is already a project directory and ask if overwrite is ok
        if os.path.isdir(os.path.join(answer, ".spinetoolbox")):
            msg = "Directory \n\n{0}\n\nalready contains a Spine Toolbox project." \
                  "\n\nWould you like to overwrite it?".format(answer)
            message_box = QMessageBox(
                QMessageBox.Question,
                "Overwrite?", msg, buttons=QMessageBox.Ok | QMessageBox.Cancel,
                parent=self._toolbox
            )
            message_box.button(QMessageBox.Ok).setText("Overwrite")
            msgbox_answer = message_box.exec_()
            if msgbox_answer != QMessageBox.Ok:
                return ""
        return answer  # New project directory

    def copy_data(self, proj_file_path, project_dir):
        """Copies project item directories from the old project to the new project directory.

        Args:
            proj_file_path (str): Path to .proj file
            project_dir (str): New project directory

        Returns:
            bool: True if copying succeeded, False if it failed
        """
        proj_info = self.open_proj_json(proj_file_path)
        if not proj_info:
            return False
        name = proj_info["project"]["name"]
        dir_name = name.lower().replace(" ", "_")
        dir, proj_file = os.path.split(proj_file_path)
        old_project_dir = os.path.join(dir, dir_name)
        if not os.path.isdir(old_project_dir):
            return False
        self._toolbox.msg.emit("Copying data to new project directory")
        # Make items directory to new project directory
        project_conf_dir = os.path.join(project_dir, ".spinetoolbox")
        project_items_dir = os.path.join(project_conf_dir, "items")
        try:
            create_dir(project_items_dir)
        except OSError:
            self._toolbox.msg_error.emit("Creating directory {0} failed".format(project_items_dir))
            return False
        src_dir = os.path.abspath(old_project_dir)
        dst_dir = os.path.abspath(project_items_dir)
        recursive_overwrite(self._toolbox, src_dir, dst_dir, ignore=None, silent=False)
        return True


