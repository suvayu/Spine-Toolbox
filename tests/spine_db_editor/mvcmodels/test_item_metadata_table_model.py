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
Unit tests for the item metadata table model.

:author: A. Soininen (VTT)
:date:   29.4.2022
"""
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from PySide2.QtCore import QModelIndex, Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    DatabaseMapping,
    import_object_classes,
    import_object_metadata,
    import_object_parameter_value_metadata,
    import_object_parameter_values,
    import_object_parameters,
    import_objects,
    import_metadata,
    import_relationship_classes,
    import_relationship_metadata,
    import_relationship_parameter_value_metadata,
    import_relationship_parameter_values,
    import_relationship_parameters,
    import_relationships,
)
from spinetoolbox.helpers import separate_metadata_and_item_metadata, signal_waiter
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.mvcmodels.item_metadata_table_model import ItemMetadataTableModel
from spinetoolbox.spine_db_editor.mvcmodels.metadata_table_model_base import Column


class TestItemMetadataTableModelWithExistingData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self._url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
        db_map = DatabaseMapping(self._url, create=True)
        import_object_classes(db_map, ("my_class",))
        import_objects(db_map, (("my_class", "my_object"),))
        import_object_parameters(db_map, (("my_class", "object_parameter"),))
        import_object_parameter_values(db_map, (("my_class", "my_object", "object_parameter", 2.3),))
        import_relationship_classes(db_map, (("relationship_class", ("my_class",)),))
        import_relationships(db_map, (("relationship_class", ("my_object",)),))
        import_relationship_parameters(db_map, (("relationship_class", "relationship_parameter"),))
        import_relationship_parameter_values(
            db_map, (("relationship_class", ("my_object",), "relationship_parameter", 5.0),)
        )
        import_metadata(db_map, ('{"source": "Fountain of objects"}',))
        import_object_metadata(db_map, (("my_class", "my_object", '{"source": "Fountain of objects"}'),))
        import_metadata(db_map, ('{"source": "Fountain of relationships"}',))
        import_relationship_metadata(
            db_map, (("relationship_class", ("my_object",), '{"source": "Fountain of relationships"}'),)
        )
        import_metadata(db_map, ('{"source": "Fountain of object values"}',))
        import_object_parameter_value_metadata(
            db_map, (("my_class", "my_object", "object_parameter", '{"source": "Fountain of object values"}'),)
        )
        import_metadata(db_map, ('{"source": "Fountain of relationship values"}',))
        import_relationship_parameter_value_metadata(
            db_map,
            (
                (
                    "relationship_class",
                    ("my_object",),
                    "relationship_parameter",
                    '{"source": "Fountain of relationship values"}',
                ),
            ),
        )
        db_map.commit_session("Add test data.")
        db_map.connection.close()
        mock_settings = mock.Mock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        logger = mock.MagicMock()
        self._db_map = self._db_mngr.get_db_map(self._url, logger, codename="database")
        QApplication.processEvents()
        self._db_mngr.get_db_map_cache(self._db_map, {"entity_metadata", "parameter_value_metadata"})
        self._model = ItemMetadataTableModel(self._db_mngr, [self._db_map])

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._model.deleteLater()
        self._temp_dir.cleanup()

    def test_model_is_initially_empty(self):
        self.assertEqual(self._model.rowCount(), 1)
        self.assertEqual(self._model.columnCount(), 3)
        self.assertEqual(self._model.headerData(Column.NAME, Qt.Horizontal), "name")
        self.assertEqual(self._model.headerData(Column.VALUE, Qt.Horizontal), "value")
        self.assertEqual(self._model.headerData(Column.DB_MAP, Qt.Horizontal), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_object(self):
        self._model.set_entity_ids({self._db_map: 1})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of objects")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_relationship(self):
        self._model.set_entity_ids({self._db_map: 2})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationships")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_object_parameter_value(self):
        self._model.set_parameter_value_ids({self._db_map: 1})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of object values")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def test_get_metadata_for_relationship_parameter_value(self):
        self._model.set_parameter_value_ids({self._db_map: 2})
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationship values")
        self.assertEqual(self._model.index(0, Column.DB_MAP).data(), "database")
        self._assert_empty_last_row()

    def _assert_empty_last_row(self):
        row = self._model.rowCount() - 1
        self.assertEqual(self._model.index(row, Column.NAME).data(), "")
        self.assertEqual(self._model.index(row, Column.VALUE).data(), "")
        self.assertEqual(self._model.index(row, Column.DB_MAP).data(), "database")

    def test_roll_back_after_item_metadata_update(self):
        self._model.set_entity_ids({self._db_map: 1})
        with signal_waiter(self._db_mngr.entity_metadata_updated) as waiter:
            index = self._model.index(0, Column.VALUE)
            self.assertTrue(self._model.setData(index, "Magician's hat"))
            waiter.wait()
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Magician's hat")
        self._assert_empty_last_row()
        with signal_waiter(self._db_mngr.session_rolled_back) as waiter:
            self._db_mngr.rollback_session(self._db_map)
            waiter.wait()
        self._model.roll_back([self._db_map])
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of objects")
        self._assert_empty_last_row()

    def test_update_relationship_parameter_value_metadata(self):
        self._model.set_parameter_value_ids({self._db_map: 2})
        change_listener = _ItemMetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.parameter_value_metadata_updated) as waiter:
            index = self._model.index(0, Column.VALUE)
            self.assertTrue(self._model.setData(index, "Magician's hat"))
            waiter.wait()
        self.assertEqual(
            change_listener.updated_items, {self._db_map: [{"id": 4, "name": "source", "value": "Magician's hat"}]}
        )
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Magician's hat")
        self._assert_empty_last_row()

    def test_update_relationship_metadata(self):
        self._model.set_entity_ids({self._db_map: 2})
        change_listener = _ItemMetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.entity_metadata_updated) as waiter:
            index = self._model.index(0, Column.VALUE)
            self.assertTrue(self._model.setData(index, "Magician's hat"))
            waiter.wait()
        self.assertEqual(
            change_listener.updated_items, {self._db_map: [{"id": 2, "name": "source", "value": "Magician's hat"}]}
        )
        self.assertEqual(self._model.rowCount(), 2)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Magician's hat")
        self._assert_empty_last_row()

    def test_add_relationship_parameter_value_metadata(self):
        self._model.set_parameter_value_ids({self._db_map: 2})
        change_listener = _ItemMetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        index = self._model.index(1, Column.NAME)
        self.assertTrue(self._model.setData(index, "author"))
        with signal_waiter(self._db_mngr.parameter_value_metadata_added) as waiter:
            index = self._model.index(1, Column.VALUE)
            self.assertTrue(self._model.setData(index, "Anonymous"))
            waiter.wait()
        self.assertEqual(
            change_listener.added_items,
            {
                self._db_map: [
                    {"id": 5, "name": "author", "value": "Anonymous", "commit_id": None},
                    {
                        "id": 3,
                        "metadata_id": 5,
                        "metadata_name": "author",
                        "metadata_value": "Anonymous",
                        "parameter_value_id": 2,
                        "commit_id": None,
                    },
                ]
            },
        )
        item_metadata_items, _ = separate_metadata_and_item_metadata(change_listener.added_items)
        self._model.add_item_metadata(item_metadata_items)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationship values")
        self.assertEqual(self._model.index(1, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "Anonymous")
        self._assert_empty_last_row()

    def test_add_relationship_metadata(self):
        self._model.set_entity_ids({self._db_map: 2})
        change_listener = _ItemMetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        index = self._model.index(1, Column.NAME)
        self.assertTrue(self._model.setData(index, "author"))
        with signal_waiter(self._db_mngr.entity_metadata_added) as waiter:
            index = self._model.index(1, Column.VALUE)
            self.assertTrue(self._model.setData(index, "Anonymous"))
            waiter.wait()
        self.assertEqual(
            change_listener.added_items,
            {
                self._db_map: [
                    {"id": 5, "name": "author", "value": "Anonymous", "commit_id": None},
                    {
                        "id": 3,
                        "metadata_id": 5,
                        "metadata_name": "author",
                        "metadata_value": "Anonymous",
                        "entity_id": 2,
                        "commit_id": None,
                    },
                ]
            },
        )
        item_metadata_items, _ = separate_metadata_and_item_metadata(change_listener.added_items)
        self._model.add_item_metadata(item_metadata_items)
        self.assertEqual(self._model.rowCount(), 3)
        self.assertEqual(self._model.index(0, Column.NAME).data(), "source")
        self.assertEqual(self._model.index(0, Column.VALUE).data(), "Fountain of relationships")
        self.assertEqual(self._model.index(1, Column.NAME).data(), "author")
        self.assertEqual(self._model.index(1, Column.VALUE).data(), "Anonymous")
        self._assert_empty_last_row()

    def test_remove_object_metadata_row(self):
        self._model.set_entity_ids({self._db_map: 1})
        change_listener = _ItemMetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.entity_metadata_removed) as waiter:
            self._model.removeRows(0, 1)
            waiter.wait()
        self.assertEqual(
            change_listener.removed_items, {self._db_map: [{"entity_id": 1, "id": 1, "metadata_id": 1, "commit_id": 2}]}
        )
        self._model.remove_item_metadata(change_listener.removed_items)
        self.assertEqual(self._model.rowCount(), 1)

    def test_remove_object_parameter_value_metadata_row(self):
        self._model.set_parameter_value_ids({self._db_map: 1})
        change_listener = _ItemMetadataChangeListener()
        self._db_mngr.register_listener(change_listener, self._db_map)
        with signal_waiter(self._db_mngr.parameter_value_metadata_removed) as waiter:
            self._model.removeRows(0, 1)
            waiter.wait()
        self.assertEqual(
            change_listener.removed_items,
            {self._db_map: [{"parameter_value_id": 1, "id": 1, "metadata_id": 3, "commit_id": 2}]},
        )
        self._model.remove_item_metadata(change_listener.removed_items)
        self.assertEqual(self._model.rowCount(), 1)


class _ItemMetadataChangeListener:
    added_items = None
    updated_items = None
    removed_items = None

    def receive_entity_metadata_added(self, db_map_data):
        self.added_items = db_map_data

    def receive_parameter_value_metadata_added(self, db_map_data):
        self.added_items = db_map_data

    def receive_entity_metadata_updated(self, db_map_data):
        self.updated_items = db_map_data

    def receive_parameter_value_metadata_updated(self, db_map_data):
        self.updated_items = db_map_data

    def receive_entity_metadata_removed(self, db_map_data):
        self.removed_items = db_map_data

    def receive_parameter_value_metadata_removed(self, db_map_data):
        self.removed_items = db_map_data


if __name__ == '__main__':
    unittest.main()