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
Compound models for object parameter definitions and values.
These models concatenate several 'single' models and one 'empty' model.

:authors: M. Marin (KTH)
:date:   28.6.2019
"""

from PySide2.QtCore import Qt, Signal, QModelIndex
from PySide2.QtGui import QFont, QIcon
from ..helpers import busy_effect, rows_to_row_count_tuples
from .compound_table_model import CompoundWithEmptyTableModel
from .empty_parameter_models import (
    EmptyObjectParameterDefinitionModel,
    EmptyObjectParameterValueModel,
    EmptyRelationshipParameterDefinitionModel,
    EmptyRelationshipParameterValueModel,
)
from .single_parameter_models import (
    SingleObjectParameterDefinitionModel,
    SingleObjectParameterValueModel,
    SingleRelationshipParameterDefinitionModel,
    SingleRelationshipParameterValueModel,
)
from .auto_filter_menu_model import AutoFilterMenuItem


class CompoundParameterModel(CompoundWithEmptyTableModel):
    """A model that concatenates several single parameter models
    and one empty parameter model.
    """

    remove_selection_requested = Signal()
    remove_icon = QIcon(":/icons/menu_icons/cog_minus.svg")

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model.

        Args:
            parent (TreeViewForm, GraphViewForm): the parent object
            db_mngr (SpineDBManager): the database manager
            *db_maps (DiffDatabaseMapping): the database maps included in the model
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._auto_filter = dict()
        self._selected_entity_class_ids = {}

    @property
    def entity_class_type(self):
        """Returns the entity class type, either 'object class' or 'relationship class'.

        Returns:
            str
        """
        raise NotImplementedError()

    @property
    def item_type(self):
        """Returns the parameter item type, either 'parameter definition' or 'parameter value'.

        Returns:
            str
        """
        raise NotImplementedError()

    @property
    def _single_model_type(self):
        """
        Returns a constructor for the single models.

        Returns:
            SingleParameterModel
        """
        return {
            "object class": {
                "parameter definition": SingleObjectParameterDefinitionModel,
                "parameter value": SingleObjectParameterValueModel,
            },
            "relationship class": {
                "parameter definition": SingleRelationshipParameterDefinitionModel,
                "parameter value": SingleRelationshipParameterValueModel,
            },
        }[self.entity_class_type][self.item_type]

    @property
    def _empty_model_type(self):
        """
        Returns a constructor for the empty model.

        Returns:
            EmptyParameterModel
        """
        return {
            "object class": {
                "parameter definition": EmptyObjectParameterDefinitionModel,
                "parameter value": EmptyObjectParameterValueModel,
            },
            "relationship class": {
                "parameter definition": EmptyRelationshipParameterDefinitionModel,
                "parameter value": EmptyRelationshipParameterValueModel,
            },
        }[self.entity_class_type][self.item_type]

    @property
    def _entity_class_id_key(self):
        """
        Returns the key of the entity class id in the model items (either "object_class_id" or "relationship_class_id")

        Returns:
            str
        """
        return {"object class": "object_class_id", "relationship class": "relationship_class_id"}[
            self.entity_class_type
        ]

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """Returns an italic font in case the given column has an autofilter installed."""
        italic_font = QFont()
        italic_font.setItalic(True)
        if role == Qt.FontRole and orientation == Qt.Horizontal and self._auto_filter.get(section):
            return italic_font
        return super().headerData(section, orientation, role)

    def _get_entity_classes(self, db_map):
        """Returns a list of entity classes from the given db_map.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list
        """
        raise NotImplementedError()

    def _create_single_models(self):
        """Returns a list of single models for this compound model, one for each entity class in each database.

        Returns:
            list
        """
        d = dict()
        for db_map in self.db_maps:
            for entity_class in self._get_entity_classes(db_map):
                d.setdefault(entity_class["name"], {}).setdefault(db_map, set()).add(entity_class["id"])
        models = []
        for db_map_ids in d.values():
            for db_map, entity_class_ids in db_map_ids.items():
                for entity_class_id in entity_class_ids:
                    models.append(self._single_model_type(self, self.header, self.db_mngr, db_map, entity_class_id))
        return models

    def _create_empty_model(self):
        """Returns the empty model for this compound model.

        Returns:
            EmptyParameterModel
        """
        return self._empty_model_type(self, self.header, self.db_mngr)

    def filter_accepts_model(self, model):
        """Returns a boolean indicating whether or not the given model should be included in this compound model.

        Args:
            model (SingleParameterModel, EmptyParameterModel)

        Returns:
            bool
        """
        if not model.can_be_filtered:
            return True
        if not self._selected_entity_class_ids:
            return True
        return model.entity_class_id in self._selected_entity_class_ids.get(model.db_map, set())

    def accepted_single_models(self):
        """Returns a list of accepted single models by calling filter_accepts_model
        on each of them, just for convenience.

        Returns:
            list
        """
        return [m for m in self.single_models if self.filter_accepts_model(m)]

    @staticmethod
    def _settattr_if_different(obj, attr, val):
        """Sets the given attribute of the given object to the given value if it's different
        from the one currently stored. Used for updating filters.

        Returns:
            bool: True if the attributed was set, False otherwise
        """
        curr = getattr(obj, attr)
        if curr != val:
            setattr(obj, attr, val)
            return True
        return False

    def update_filter(self):
        """Updates and applies the filter."""
        updated = self.update_compound_filter()
        for model in self.single_models:
            updated |= self.update_single_model_filter(model)
        if updated:
            self.refresh()

    def update_compound_filter(self):
        """Updates the compound filter by setting the _selected_entity_class_ids attribute.

        Returns:
            bool: True if the filter was updated, None otherwise
        """
        a = False
        if self._auto_filter:
            self._auto_filter.clear()
            a = True
        b = self._settattr_if_different(
            self, "_selected_entity_class_ids", self.parent().selected_entity_class_ids(self.entity_class_type)
        )
        return a or b

    def update_single_model_filter(self, model):
        """Updates the filter for the given single model by setting its _selected_param_def_ids attribute.

        Args:
            model (SingleParameterModel)

        Returns:
            bool: True if the filter was updated, None otherwise
        """
        a = False
        if model._auto_filter:
            model._auto_filter.clear()
            a = True
        b = self._settattr_if_different(
            model,
            "_selected_param_def_ids",
            self.parent()
            .selected_param_def_ids[self.entity_class_type]
            .get((model.db_map, model.entity_class_id), set()),
        )
        return a or b

    def update_auto_filter(self, column, auto_filter):
        """Updates the auto filter for given column.

        Args:
            column (int): the column number
            auto_filter (dict): collection of filtered values keyed by entity ids (int)
        """
        self._auto_filter[column] = auto_filter
        updated = False
        for model in self.accepted_single_models():
            updated |= self.update_single_model_auto_filter(model, column)
        if updated:
            self.refresh()

    def update_single_model_auto_filter(self, model, column):
        """Updates the auto-filtered values for given model and column.

        Args:
            model (SingleParameterModel): the model
            column (int): the column number

        Returns:
            bool: True if the auto-filtered values were updated, None otherwise
        """
        values = self._auto_filter[column].get(model.entity_class_id, {})
        if values == model._auto_filter.get(column, {}):
            return False
        model._auto_filter[column] = values
        return True

    def _row_map_for_model(self, model):
        """Returns the row map for the given model.
        Reimplemented to take filter status into account.

        Args:
            model (SingleParameterModel, EmptyParameterModel)

        Returns:
            list: tuples (model, row number) for each accepted row
        """
        if not self.filter_accepts_model(model):
            return []
        return [(model, i) for i in model.accepted_rows()]

    @busy_effect
    def auto_filter_menu_data(self, column):
        """Returns auto filter menu data for the given column.

        Returns:
            list: AutoFilterMenuItem instances to populate the auto filter menu.
        """
        auto_filter_vals = dict()
        for model in self.accepted_single_models():
            for row in model.accepted_rows(ignored_columns=[column]):
                value = model.index(row, column).data()
                auto_filter_vals.setdefault(value, set()).add(model.entity_class_id)
        column_auto_filter = self._auto_filter.get(column, {})
        filtered = [val for values in column_auto_filter.values() for val in values]
        return [
            AutoFilterMenuItem(Qt.Checked if value not in filtered else Qt.Unchecked, value, class_ids)
            for value, class_ids in auto_filter_vals.items()
        ]

    def _models_with_db_map(self, db_map):
        """Returns a collection of single models with given db_map.

        Args:
            db_map (DiffDatabaseMapping)

        Returns:
            list
        """
        return [m for m in self.single_models if m.db_map == db_map]

    def receive_entity_classes_removed(self, db_map_data):
        """Runs when entity classes are removed from the dbs.
        Removes sub-models for the given entity classes and dbs.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        self.layoutAboutToBeChanged.emit()
        for db_map, data in db_map_data.items():
            ids = {x["id"] for x in data}
            for model in self._models_with_db_map(db_map):
                if model.entity_class_id in ids:
                    self.sub_models.remove(model)
                    if not model.canFetchMore(QModelIndex()):
                        self._fetched_count -= 1
        self.do_refresh()
        self.layoutChanged.emit()

    def receive_parameter_data_updated(self, db_map_data):
        """Runs when either parameter definitions or values are updated in the dbs.
        Emits dataChanged so the parameter_name column is refreshed.

        Args:
            db_map_data (dict): list of updated dict-items keyed by DiffDatabaseMapping
        """
        self._emit_data_changed_for_column("parameter_name")
        # TODO: parameter definition names aren't refreshed unless we emit dataChanged,
        # whereas entity and class names don't need it. Why?

    def _grouped_ids(self, items):
        d = dict()
        for item in items:
            entity_class_id = item.get(self._entity_class_id_key)
            if not entity_class_id:
                continue
            d.setdefault(entity_class_id, []).append(item["id"])
        return d

    def receive_parameter_data_removed(self, db_map_data):
        """Runs when either parameter definitions or values are removed from the dbs.
        Removes the affected rows from the corresponding single models.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        self.layoutAboutToBeChanged.emit()
        for db_map, items in db_map_data.items():
            grouped_ids = self._grouped_ids(items)
            for model in self._models_with_db_map(db_map):
                removed_ids = grouped_ids.get(model.entity_class_id)
                if not removed_ids:
                    continue
                removed_rows = [row for row in range(model.rowCount()) if model._main_data[row] in removed_ids]
                for row, count in sorted(rows_to_row_count_tuples(removed_rows), reverse=True):
                    del model._main_data[row : row + count]
        self.do_refresh()
        self.layoutChanged.emit()

    def receive_parameter_data_added(self, db_map_data):
        """Runs when either parameter definitions or values are added to the dbs.
        Adds necessary sub-models and initializes them with data.
        Also notifies the empty model so it can remove rows that are already in.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        new_models = []
        for db_map, items in db_map_data.items():
            grouped_ids = self._grouped_ids(items)
            for entity_class_id, ids in grouped_ids.items():
                model = self._single_model_type(self, self.header, self.db_mngr, db_map, entity_class_id, lazy=False)
                model.reset_model(ids)
                self._handle_single_model_reset(model)
                new_models.append(model)
        pos = len(self.single_models)
        self.sub_models[pos:pos] = new_models
        self.empty_model.receive_parameter_data_added(db_map_data)

    def _emit_data_changed_for_column(self, field):
        """Lazily emits data changed for an entire column.

        Args:
            field (str): the column header
        """
        try:
            column = self.header.index(field)
        except ValueError:
            return
        self.dataChanged.emit(self.index(0, column), self.index(self.rowCount() - 1, column), [Qt.DisplayRole])


class CompoundObjectParameterMixin:
    """Implements the interface for populating and filtering a compound object parameter model."""

    @property
    def entity_class_type(self):
        return "object class"

    def _get_entity_classes(self, db_map):
        return self.db_mngr.get_object_classes(db_map)


class CompoundRelationshipParameterMixin:
    """Implements the interface for populating and filtering a compound relationship parameter model."""

    @property
    def entity_class_type(self):
        return "relationship class"

    def _get_entity_classes(self, db_map):
        return self.db_mngr.get_relationship_classes(db_map)


class CompoundParameterDefinitionMixin:
    """Handles signals from db mngr for parameter definition models."""

    @property
    def item_type(self):
        return "parameter definition"


class CompoundParameterValueMixin:
    """Handles signals from db mngr for parameter value models."""

    @property
    def item_type(self):
        return "parameter value"

    @property
    def entity_type(self):
        """Returns the entity type, either 'object' or 'relationship'
        Used by update_single_model_filter.

        Returns:
            str
        """
        raise NotImplementedError()

    def update_single_model_filter(self, model):
        """Update the filter for the given model."""
        a = super().update_single_model_filter(model)
        b = self._settattr_if_different(
            model,
            "_selected_entity_ids",
            self.parent().selected_ent_ids[self.entity_type].get((model.db_map, model.entity_class_id), set()),
        )
        return a or b


class CompoundObjectParameterDefinitionModel(
    CompoundObjectParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter definition models
    and one empty object parameter definition model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model header."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = [
            "object_class_name",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "database",
        ]


class CompoundRelationshipParameterDefinitionModel(
    CompoundRelationshipParameterMixin, CompoundParameterDefinitionMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter definition models
    and one empty relationship parameter definition model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model header."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = [
            "relationship_class_name",
            "object_class_name_list",
            "parameter_name",
            "value_list_name",
            "parameter_tag_list",
            "default_value",
            "database",
        ]


class CompoundObjectParameterValueModel(
    CompoundObjectParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single object parameter value models
    and one empty object parameter value model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model header."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = ["object_class_name", "object_name", "parameter_name", "value", "database"]

    @property
    def entity_type(self):
        return "object"


class CompoundRelationshipParameterValueModel(
    CompoundRelationshipParameterMixin, CompoundParameterValueMixin, CompoundParameterModel
):
    """A model that concatenates several single relationship parameter value models
    and one empty relationship parameter value model.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Initializes model header."""
        super().__init__(parent, db_mngr, *db_maps)
        self.header = ["relationship_class_name", "object_name_list", "parameter_name", "value", "database"]

    @property
    def entity_type(self):
        return "relationship"

    def receive_relationships_added(self, db_map_data):
        """Runs when relationships are added to the dbs.
        Notifies the empty model.

        Args:
            db_map_data (dict): list of removed dict-items keyed by DiffDatabaseMapping
        """
        self.empty_model.receive_relationships_added(db_map_data)
