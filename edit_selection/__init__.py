'''
    This script defines the EditSelection view class, which is associated the the edit_selection pyui file. The EditSelection view is used to display a list of items, either circuits or exercises, when the user selects the Edit segment in the Run/Edit view. The EditSelection view allows the user to select an item to edit or to delete. The EditSelection view also has an Add (+) button that allows the user to add a new item.
'''

import os
import ui  # type: ignore
import json

from data import Exercise, Circuit, EXERCISES_PATH, CIRCUITS_PATH, get_exercises, get_circuits
'''
    From the data package, import:
    - the Exercise and Circuit dataclasses
    - the paths to the Exercises and Circuits folders
    - function get_exercises and get_circuits, which return lists of exercises and circuits, respectively`
'''

from edit_exercise import EDIT_EXERCISE_PYUI_PATH, EditExercise
'''
   From the edit_exercise package, import:
      - the path to the EditExercise view definition file (EditExercise.pyui)
      - the EditExercise custom view class associated with the EditExercise.pyui file 
'''

from edit_circuit import EDIT_CIRCUIT_PYUI_PATH, EditCircuit
'''
   From the edit_circuit package, import:
      - the path to the EditCircuit view definition file (EditCircuit.pyui)
      - the EditCircuit custom view class associated with the EditCircuit.pyui file 
'''

EDIT_SELECTION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
EDIT_SELECTION_PYUI_PATH = os.path.join(EDIT_SELECTION_PATH, 'edit_selection')

# The custom view class for the edit_selection view
class EditSelection(ui.View):

    # Handle the back button
    def back_button_tapped(self, sender):
        print('Back button tapped')
        sender.navigation_view.pop_view()

    # Refresh functions to update the list of items in the EditSelection view after an item is added, edited or deleted in the EditCircuit or EditExercise views. These functions will be passed as callbacks to the EditCircuit and EditExercise views.
    def refresh_exercises(self):
        print('Refreshing exercises')
        self['tableview1'].data_source.items = get_exercises()

    def refresh_circuits(self):
        print('Refreshing circuits')
        self['tableview1'].data_source.items = get_circuits()

    # Handle the add button
    def add_button_tapped(self, sender):
        print('Add button tapped')
        # Invoke the EditExercise or EditCircuit view, depending on the folder being displayed in the EditSelection view. Fill the edit view with an empty Exercise or Circuit dataclass instance.
        match self.folder:
            case 'Exercises':
                edit_exercise_view = ui.load_view(EDIT_EXERCISE_PYUI_PATH)
                edit_exercise_view.fill_exercise(Exercise(), 'add', self.refresh_exercises)
                sender.navigation_view.push_view(edit_exercise_view)
            case 'Circuits':
                edit_circuit_view = ui.load_view(EDIT_CIRCUIT_PYUI_PATH)
                edit_circuit_view.fill_circuit(Circuit(), 'add', self.refresh_circuits)
                sender.navigation_view.push_view(edit_circuit_view) 

    # Handle selection of an item in the TableView
    def tableview_did_select(self, tableview, section, row):
        print('edit_selection tableview_did_select entered')
        print(tableview.data_source.items[row])
        tableview.reload() # Reload the TableView to remove the selection highlight
        '''
            Depending on the folder being processed,
                - load the selected item from the file system and create a dataclass instance from it
                - invoke the appropriate edit view, filled with that dataclass instance
        '''
        match self.folder:
            case 'Exercises':
                selected_exercise = tableview.data_source.items[row] + '.exercise'
                exercise = Exercise(**json.load(open(os.path.join(EXERCISES_PATH, selected_exercise))))
                edit_exercise_view = ui.load_view(EDIT_EXERCISE_PYUI_PATH)
                edit_exercise_view.fill_exercise(exercise, 'edit', self.refresh_exercises)
                self.navigation_view.push_view(edit_exercise_view)
            case 'Circuits':
                selected_circuit = tableview.data_source.items[row] + '.circuit'
                circuit = Circuit(**json.load(open(os.path.join(CIRCUITS_PATH, selected_circuit))))
                edit_circuit_view = ui.load_view(EDIT_CIRCUIT_PYUI_PATH)
                edit_circuit_view.fill_circuit(circuit, 'edit', self.refresh_circuits)
                self.navigation_view.push_view(edit_circuit_view)

    # Handle deletion of an item in the TableView
    def tableview_delete(self, tableview, section, row):
        print('edit_selection tableview_delete entered')
        '''
            Depending on the folder being processed,
                - remove the selected item from the file system
                - remove the selected item from the TableView's data source
                - delete the selected row from the TableView
        '''
        match self.folder:
            case 'Exercises':
                selected_exercise = tableview.data_source.items[row] + '.exercise'
                print('Deleting exercise:', selected_exercise)
                os.remove(os.path.join(EXERCISES_PATH, selected_exercise))
                tableview.data_source.items.pop(row)
                tableview.delete_rows([row])
            case 'Circuits':
                selected_circuit = tableview.data_source.items[row] + '.circuit'
                os.remove(os.path.join(CIRCUITS_PATH, selected_circuit))
                tableview.data_source.items.pop(row)
                tableview.delete_rows([row])
    
    # On loading of the EditSelection view...
    def did_load(self):
        print("EditSelection did_load entered")
        # ...set action handlers for its buttons
        self['back_button'].action = self.back_button_tapped
        self['add_button'].action = self.add_button_tapped

    # Function to initialize the TableView in the EditSelection view
    # This function is called from ExerciseMetronome.py
    def fill_table(self, folder):
        self.folder = folder
        content_dictionary = dict(Exercises = get_exercises(), Circuits = get_circuits())
        # Create a ListDataSouce instance containing the appropriate content
        edit_selection_datasource = ui.ListDataSource(content_dictionary[folder])
        # Set action handlers for the tableview did_select and delete actions
        edit_selection_datasource.tableview_did_select = self.tableview_did_select
        edit_selection_datasource.tableview_delete = self.tableview_delete
        # Set the TableView's data_source and delegate to the ListDataSource instance
        self['tableview1'].data_source = self['tableview1'].delegate =  edit_selection_datasource
