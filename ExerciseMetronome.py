'''
Exercise Metronome is a simple exercise timer for circuits of exercises. 

For each exercise, it produces a sound cue at the start of each rep and a sound cue at the end of the reps. For exercises with a hold interval, it also produces a sound cue at the end of the hold interval.

The definition of an exercise comprises:
- its name
- an optional number of reps
- a start delay 
- a hold interval, which may be zero
- a time interval between the end of one rep and the start of the next

Exercises are organized in circuits. The definition of a circuit comprises:
- its name
- a default number of reps for exercises that don't specify the number of reps
- a list of exercises

Circuit and exercise definitions are stored in the folders Circuits and Exercises, respectively, in the data folder.

The Exercise Metronome can run circuits and create/edit definitions of exercises and circuits.

A running circuit can be paused and resumed.

This script is the entry point for the Exercise Metronome. It presents a view with a segmented control that has two segments: Run and Edit. Initially, the Run segment is selected and a list of circuits is displayed. When the Edit segment is selected, a list comprising Circuits and Exercises is displayed.

When a circuit is selected from the Run list, the function run_circuit, which was imported from the run_circuit package, is called to run the selected circuit.

When Circuits or Exercises is selected from the Edit list, an instance of the EditSelection class, which was imported from the edit_selection package, is created and presented. The EditSelection view displays a list of the selected items, circuits or exercises.
'''

import os
import ui # type: ignore
import json

from data import circuits, folders, CIRCUITS_PATH, Circuit, get_circuits
'''
   From the data package, import:
      - a list of circuit names from the Circuits folder
      - a list of names of folders containing editable items (Circuits and Exercises)
      - the path to the Circuits folder
      - the Circuit dataclass
      - a function (get_circuits) that returns a list of circuit names in the Circuits folder
'''

from run_circuit import run_circuit # Import fuxction run_circuit``

from edit_selection import EDIT_SELECTION_PYUI_PATH, EditSelection
'''
   From the edit_selection package, import:
      - the path to the EditSelection view definition file (EditSelection.pyui)
      - the EditSelection custom view class associated with the EditSelection.pyui file 
'''

# The data source for the TableView in the run_edit_view is a ListDataSource
run_edit_datasource = ui.ListDataSource([])

# For the TableView when the Edit segment is selected, create a list of dictionaries for the run_edit_datasource that specify a folder name (in data) and a disclosure indicator as the accessory type.
folders_dicts = [{"title": folder, "accessory_type": "disclosure_indicator", "image": "none"} for folder in folders]


# The did_select function for the TableView in the Run segment must run in the background because it calls run_circuit, which contains time.sleep calls.
@ui.in_background
def did_select_circuit(sender):
   # When a circuit is selected to run, read its definition and call function run_circuit.
   row_index = sender.selected_row
   circuit_name = circuits[row_index]
   print(f"Selected circuit: {circuit_name}")
   circuit = Circuit(**json.load(open(os.path.join(CIRCUITS_PATH, circuit_name + '.circuit'))))
   run_edit_view['tableview1'].reload() # Reload the TableView to remove the selection highlight
   run_circuit(nav, circuit) # Run the circuit, passing the app's NavigationView and the selected circuit definition 

# The did_select function for the TableView in the Edit segment
def did_select_folder(sender):
   # When a folder is selected to edit, create an instance of the EditSelection view class, fill its TableView with the items in the selected folder and display the view by pushing it onto the NavigationView stack.
   row_index = sender.selected_row
   folder_name = folders[row_index]
   print(f"Selected folder: {folder_name}")
   edit_selection_view = ui.load_view(EDIT_SELECTION_PYUI_PATH)
   edit_selection_view['label1'].text = folder_name
   edit_selection_view.fill_table(folder_name)
   run_edit_view['tableview1'].reload() # Reload the TableView to remove the selection highlight
   nav.push_view(edit_selection_view)

# Function to fill the TableView and set its did_select function according to the selected segment control element
def fill_tableview(index):
  global circuits
  match index:
    case 0:
      # For the Run segment, show the circuits
      run_edit_datasource.items = circuits = get_circuits() # Get the circuits to show by listing the contents of the Circuits folder
      run_edit_datasource.action = did_select_circuit
    case 1:
      # For the Edit segments, show the folders containing editable items
      run_edit_datasource.items = folders_dicts
      run_edit_datasource.action = did_select_folder

# The segmented control changed function
def run_edit_selection_changed(sender):
   # Call function fill_tableview to fill the TableView with the appropriate items for the selected segment and set the appropriate did_select function for the TableView
	fill_tableview(sender.selected_index)
	run_edit_view['tableview1'].reload_data() # Reload the TableView <---<<

# Create and present the Run/Edit View
run_edit_view = ui.load_view('RunEditView.pyui')
run_edit_view.name = 'Exercise Metronome'
run_edit_view['segmentedcontrol1'].selected_index = 0 # Initially show the Run options
fill_tableview(run_edit_view['segmentedcontrol1'].selected_index) 
run_edit_view['tableview1'].data_source = run_edit_view['tableview1'].delegate = run_edit_datasource
nav = ui.NavigationView(run_edit_view)
nav.navigation_bar_hidden = True
nav.present('fullscreen')
