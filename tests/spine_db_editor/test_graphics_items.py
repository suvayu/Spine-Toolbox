######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for Database editor's ``graphics_items`` module.

:authors: A. Soininen (VTT)
:date:    16.4.2021
"""
import math
import unittest
from unittest import mock
from PySide2.QtCore import QPointF
from PySide2.QtWidgets import QApplication
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.graphics_items import ArcItem, ObjectItem, RelationshipItem
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor


class TestRelationshipItem(unittest.TestCase):
    _db_mngr = None

    @classmethod
    def setUpClass(cls):
        # SpineDBEditor takes long to construct hence we make only one of them for the entire suite.
        if not QApplication.instance():
            QApplication()
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"), mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.show"
        ):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            cls._db_mngr = SpineDBManager(mock_settings, None)
            cls._db_mngr.fetch_db_maps_for_listener = lambda *args: None

            logger = mock.MagicMock()
            cls._db_map = cls._db_mngr.get_db_map("sqlite://", logger, codename="database", create=True)
            cls._spine_db_editor = SpineDBEditor(cls._db_mngr, {"sqlite://": "database"})
            cls._spine_db_editor.pivot_table_model = mock.MagicMock()

    @classmethod
    def tearDownClass(cls):
        while cls._db_mngr._fetchers:
            # Wait for fetchers to finish, otherwise DB manager may try to double-delete them
            # in the clean_up() call below.
            QApplication.processEvents()
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ) as mock_save_w_s, mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            cls._spine_db_editor.close()
            mock_save_w_s.assert_called_once()
        QApplication.removePostedEvents(None)  # Clean up unfinished fetcher signals
        cls._db_mngr.close_all_sessions()
        cls._db_mngr.clean_up()
        cls._spine_db_editor.deleteLater()
        cls._spine_db_editor = None

    def setUp(self):
        self._db_mngr.cache_items(
            "relationship_class",
            {self._db_map: [{"name": "rc", "id": 2, "object_class_id_list": [1], "object_class_name_list": "oc"}]},
        )
        self._db_mngr.cache_items(
            "relationship",
            {
                self._db_map: [
                    {
                        "name": "r",
                        "id": 4,
                        "class_id": 2,
                        "class_name": "rc",
                        "object_id_list": [3],
                        "object_name_list": "o",
                    }
                ]
            },
        )
        self._item = RelationshipItem(self._spine_db_editor, 0.0, 0.0, 0, (self._db_map, 4))

    def test_entity_type(self):
        self.assertEqual(self._item.entity_type, "relationship")

    def test_entity_name(self):
        self.assertEqual(self._item.entity_name, "r")

    def test_entity_class_type(self):
        self.assertEqual(self._item.entity_class_type, "relationship_class")

    def test_entity_class_id(self):
        self.assertEqual(self._item.entity_class_id, 2)

    def test_entity_class_name(self):
        self.assertEqual(self._item.entity_class_name, "rc")

    def test_db_map(self):
        self.assertIs(self._item.db_map, self._db_map)

    def test_entity_id(self):
        self.assertEqual(self._item.entity_id, 4)

    def test_first_db_map(self):
        self.assertIs(self._item.first_db_map, self._db_map)

    def test_display_data(self):
        self.assertEqual(self._item.display_data, "r")

    def test_display_database(self):
        self.assertEqual(self._item.display_database, "database")

    def test_db_maps(self):
        self.assertEqual(self._item.db_maps, (self._db_map,))

    def test_db_map_data(self):
        self.assertEqual(
            self._item.db_map_data(self._db_map),
            {"name": "r", "id": 4, "class_id": 2, "class_name": "rc", "object_id_list": [3], "object_name_list": "o"},
        )

    def test_db_map_id_equals_entity_id(self):
        self.assertEqual(self._item.db_map_id(self._db_map), self._item.entity_id)

    def test_add_arc_item(self):
        arc = mock.MagicMock()
        self._item.add_arc_item(arc)
        self.assertEqual(self._item.arc_items, [arc])
        arc.update_line.assert_called_once()

    def test_apply_zoom(self):
        self._item.apply_zoom(0.5)
        self.assertEqual(self._item.scale(), 0.5)
        self._item.apply_zoom(1.5)
        self.assertEqual(self._item.scale(), 1.0)

    def test_apply_rotation(self):
        arc = mock.MagicMock()
        self._item.add_arc_item(arc)
        rotation_center = QPointF(100.0, 0.0)
        self._item.apply_rotation(-90.0, rotation_center)
        self.assertEqual(self._item.pos(), QPointF(100.0, -100.0))
        arc.update_line.assert_has_calls([])


if __name__ == "__main__":
    unittest.main()