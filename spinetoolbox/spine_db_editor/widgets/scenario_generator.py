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
Contains a dialog for generating scenarios from selected alternatives.

:authors: A.Soininen (VTT)
:date:    7.9.2021
"""
from enum import auto, Enum, unique
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QWidget, QMessageBox

from ...helpers import signal_waiter
from ..scenario_generation import all_combinations, unique_alternatives


@unique
class _ScenarioNameResolution(Enum):
    NO_CONFLICT = auto()
    OVERWRITE = auto()
    LEAVE_AS_IS = auto()
    CANCEL_OPERATION = auto()


class ScenarioGenerator(QWidget):
    """A dialog where users can generate scenarios from given alternatives."""

    _TYPE_LABELS = ("All combinations", "Scenario for each alternative")

    def __init__(self, parent, db_map, alternatives, spine_db_editor):
        """
        Args:
            parent (QWidget): parent widget
            db_map (DiffDatabaseMapping): database mapping that contains the alternatives
            alternatives (Iterable of CacheItem): alternatives from which the scenarios are generated
            spine_db_editor (SpineDBEditor): database editor instance
        """
        from ..ui.scenario_generator import Ui_Form

        self._db_map = db_map
        self._alternatives = alternatives
        self._db_editor = spine_db_editor
        super().__init__(parent)
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle("Generate scenarios")
        self.addAction(self._ui.accept_action)
        self.addAction(self._ui.reject_action)
        self._ui.accept_action.triggered.connect(self.accept)
        self._ui.reject_action.triggered.connect(self.close)
        self._ui.button_box.accepted.connect(self._ui.accept_action.trigger)
        self._ui.button_box.rejected.connect(self._ui.reject_action.trigger)
        self._ui.operation_combo_box.addItems(self._TYPE_LABELS)
        self._ui.alternative_list.addItems([item["name"] for item in alternatives])

    @Slot()
    def accept(self):
        """Generates scenarios and closes the dialog.

        The operation may get cancelled by user if there are conflicts in scenario names.
        """
        scenario_prefix = self._ui.scenario_prefix_edit.text().strip()
        if not scenario_prefix:
            QMessageBox.warning(self, "No scenario name prefix", "Enter a name prefix for scenarios.")
            return
        operation_label = self._ui.operation_combo_box.currentText()
        alternative_list = self._ui.alternative_list
        alternative_order = {alternative_list.item(row).text(): row for row in range(alternative_list.count())}
        alternatives = sorted(self._alternatives, key=lambda a: alternative_order[a["name"]])
        scenario_alternatives = {self._TYPE_LABELS[0]: all_combinations, self._TYPE_LABELS[1]: unique_alternatives}[
            operation_label
        ](alternatives)
        generated_scenario_names = [scenario_prefix + str(count) for count in range(1, len(scenario_alternatives) + 1)]
        scenario_items = self._db_editor.scenario_items(self._db_map)
        existing_scenario_names = {item.name for item in scenario_items}
        resolution = self._check_existing_scenarios(generated_scenario_names, existing_scenario_names)
        if resolution == _ScenarioNameResolution.CANCEL_OPERATION:
            return
        if resolution == _ScenarioNameResolution.NO_CONFLICT:
            new_scenarios = generated_scenario_names
            scenarios_to_modify = generated_scenario_names
        else:
            new_scenarios = [name for name in generated_scenario_names if name not in existing_scenario_names]
            if resolution == _ScenarioNameResolution.OVERWRITE:
                scenarios_to_modify = generated_scenario_names
            else:
                scenarios_to_modify = new_scenarios
        self._generate_scenarios(new_scenarios, scenarios_to_modify, scenario_alternatives)
        self.close()

    def _generate_scenarios(self, new_scenarios, scenarios_to_modify, scenario_alternatives):
        """Generates scenarios with all possible combinations of given alternatives.

        Args:
            new_scenarios (Iterable of str): names of new scenarios to create
            scenarios_to_modify (Iterable of str): names of scenarios to modify
            scenario_alternatives (list of list): alternative items for each scenario
        """
        if new_scenarios:
            with signal_waiter(self._db_editor.db_mngr.scenarios_added) as waiter:
                self._db_editor.db_mngr.add_scenarios({self._db_map: [{"name": name} for name in new_scenarios]})
                waiter.wait()
        searchable_scenario_names = set(scenarios_to_modify)
        scenario_definitions_by_id = dict()
        alternative_iter = iter(scenario_alternatives)
        scenario_items = self._db_editor.scenario_items(self._db_map)
        for item in scenario_items:
            if item.name not in searchable_scenario_names:
                continue
            scenario_definitions_by_id[item.id] = [a["id"] for a in next(alternative_iter)]
        scenario_alternative_data = [
            {"id": scenario_id, "alternative_id_list": ",".join(map(str, alternative_ids))}
            for scenario_id, alternative_ids in scenario_definitions_by_id.items()
        ]
        self._db_editor.db_mngr.set_scenario_alternatives({self._db_map: scenario_alternative_data})

    def _check_existing_scenarios(self, proposed_scenario_names, existing_scenario_names):
        """Checks if proposed scenarios exist, and if so, prompts users what to do.

        Args:
            proposed_scenario_names (Iterable of str): proposed scenario names
            existing_scenario_names (set of str): existing scenario names

        Returns:
             _ScenarioNameResolution: action to take
        """
        if all(name not in existing_scenario_names for name in proposed_scenario_names):
            return _ScenarioNameResolution.NO_CONFLICT
        message_box = QMessageBox(
            QMessageBox.Warning,
            "Scenarios already in database",
            "One or more scenarios that are about to be generated already exist in the database.",
            QMessageBox.NoButton,
            self,
        )
        message_box.addButton("Overwrite", QMessageBox.DestructiveRole)
        keep_button = message_box.addButton("Keep existing", QMessageBox.AcceptRole)
        cancel_button = message_box.addButton(QMessageBox.Cancel)
        message_box.exec_()
        clicked_button = message_box.clickedButton()
        if clicked_button is None or clicked_button is cancel_button:
            return _ScenarioNameResolution.CANCEL_OPERATION
        if clicked_button is keep_button:
            return _ScenarioNameResolution.LEAVE_AS_IS
        return _ScenarioNameResolution.OVERWRITE