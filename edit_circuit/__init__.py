'''
    This script defines the EditCircuit view class, which is associated with the edit_circuit pyui file. The EditCircuit view is used to create and edit circuit definitions. Using the EditCircuit view,
    - circuits can be renamed or duplicated
    - the default number of reps for exercises in the circuit can be specified
    - exercises can be added to or removed from a circuit
    - exercises in a circuit can be reordered
    - exercises in a circuit can be duplicated
'''
from dataclasses import asdict
import ui  # type: ignore
import os
from pathlib import Path
import math
import json
from data import Circuit, CIRCUITS_PATH, get_exercises
'''
    From the data package, import:
    - the Circuit dataclass
    - the path to the Circuits folder
    - function get_exercises, which return a list of exercises
'''
from modals import ALREADY_EXISTS_PATH, NAME_CHANGED_PATH, UNSAVED_PATH
'''
    From the modals package, import:
    - the path to the already_exists_view definition file (already_exists.pyui)
    - the path to the name_changed_view definition file (name_changed.pyui)
    - the path to the unsaved_view definition file (unsaved.pyui)
'''

EDIT_CIRCUIT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
EDIT_CIRCUIT_PYUI_PATH = os.path.join(EDIT_CIRCUIT_PATH, 'edit_circuit')

# The delegate class for the circuit name TextField
class TextFieldDelegate:

    def __init__(self, textfield):
        # Make a note of the TextField instance that this delegate is associated with for the is_name_specified function
        self.textfield = textfield

    # Handle changes to the circuit name
    def textfield_did_change(self, sender):
        # Enable the save button if the circuit name is not empty, otherwise disable it
        if sender.text:
            sender.superview['save_button'].enabled = True
        else:
            sender.superview['save_button'].enabled = False

    # A function to check if the circuit name is specified
    def is_name_specified(self):
        return self.textfield.text != ''

# The data source and delegate for the TableView in the edit_circuit view.
class TableviewDataSource (object):

    def __init__(self, circuit_exercises):
        self.circuit_exercises = circuit_exercises # A list of exercises in the circuit
        self.exercises = get_exercises() # A list of all defined exercises

        # A list of exercises not in the circuit and so available to be added
        self.available_exercises = self.get_available_exercises(self.circuit_exercises)

    # A function to get the exercises that are not in the circuit (used internally)
    def get_available_exercises(self, circuit_exercises):
        exercises = get_exercises()
        available_exercises = [e for e in exercises if e not in circuit_exercises]
        return available_exercises

    # --- Data source methods ---

    # Define 2 sections in the TableView
    '''
        Section 0: exercises in the circut
        Section 1: defined exercises not in the circuit 
    '''
    def tableview_number_of_sections(self, tableview):
        return 2

    # Return the number of rows in each section of the TableView
    def tableview_number_of_rows(self, tableview, section):
        if section == 0:
            return len(self.circuit_exercises)
        else:
            return len(self.available_exercises)

    # Create and return a cell for the given section/row
    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        if section == 0:
            cell.text_label.text = self.circuit_exercises[row]
        else:
            cell.text_label.text = self.available_exercises[row]
        return cell

    
    # Return a title for each section.
    def tableview_title_for_header(self, tableview, section):
        if section == 0:
            return 'Selected exercises'
        elif section == 1:
            return 'Available exercises'

    # Define which rows can be deleted
    def tableview_can_delete(self, tableview, section, row):
        # Allow deletion of exercises in the circuit only
        if section == 0:
            return True
        return False

    # Define which rows can be moved
    def tableview_can_move(self, tableview, section, row):
        # Allow moving of exercises in the circuit only
        if section == 0:
            return True
        return False
    
    # End editing of the name TextField
    def endEditing(self, view):
        '''
            When TableViewCells are deleted, moved or selected, 
            - end editing of the name TextField, which dismisses the keyboard and invokes the textfield_did_change function of the TextField delegate
            - enable the save button if the name TextField is not empty
        '''
        view['name_field'].end_editing()
        view['save_button'].enabled = True and view['name_field'].delegate.is_name_specified()

    # Handle deletion of a row
    def tableview_delete(self, tableview, section, row):
        '''
            - end editing of the name TextField
            - remove the deleted exercise from the circuit exercises list
            - regenerate the available exercises list
            - reload the TableView to reflect the changes
            '''
        self.endEditing(tableview.superview)
        self.circuit_exercises.pop(row) 
        self.available_exercises = self.get_available_exercises(self.circuit_exercises)
        tableview.reload()

    # Handle moving a row
    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        '''
            - end editing of the name TextField
            - extract the moved exercise from the circuit exercises list
            - insert the moved exercise into its new position in the list
        '''
        self.endEditing(tableview.superview)
        moved_exercise = self.circuit_exercises.pop(from_row)
        self.circuit_exercises.insert(to_row, moved_exercise)

    # --- Delegate methods ---
    
    # Handle selection of a row
    def tableview_did_select(self, tableview, section, row):
        self.endEditing(tableview.superview) # end editing of the name TextField
        if section == 0:
            '''
                In the Selected exercises section, make a copy of the selected exercise and insert it into the circuit exercises list after the selected exercise.
            '''
            exercise = self.circuit_exercises[row]
            self.circuit_exercises.insert(row + 1, exercise)
        else:
            '''
                In the Available exercises section, add the sselected exercise to the end of the circuit exercises list and remove it from the available exercises list.
            '''
            exercise = self.available_exercises[row]    		
            self.circuit_exercises.append(exercise)       		
            self.available_exercises.remove(exercise)
        
        # In either case, reload the TableView to reflect the changes
        tableview.reload()
        

# The custom view class for the edit_circuit view
class EditCircuit(ui.View):

    # Initialize internal variables
    def __init__(self):
        self.default_reps = 1
        self.mode = '' # 'add' or 'edit', set in function fill_circuit

    # Handle the back button
    def back_button_tapped(self, sender):

        # Check for unsaved changes
        new_circuit = Circuit( # Create a Circuit dataclass instance from the current values
            circuit_name=self['name_field'].text.strip(),
            default_reps=int(self['def_reps'].text),
            exercises=self['tableview1'].data_source.circuit_exercises
        )
        if new_circuit != self.input_circuit:
            # If the new circuit values differ from the initial values, present a modal to ask if the new values should be discarded or not.
            self.choice = ''

            # Handle button taps in the modal
            def choice_made(sender):
                # Note which button was tapped and close the modal
                self.choice = sender.name
                unsaved_view.close()
            
            # Present the modal and wait for a button to be tapped
            unsaved_view = ui.load_view(UNSAVED_PATH)
            unsaved_view['un_cancel'].action = choice_made # Set button handlers
            unsaved_view['un_discard'].action = choice_made
            unsaved_view.present(style='sheet', hide_title_bar=True)
            unsaved_view.wait_modal() # Wait for the modal to be closed

            if self.choice == 'un_discard':
                # If the discard button was tapped, go back; else stay
                sender.navigation_view.pop_view()
        else:
            # If there are no changes, pop the edit_circuit view to go back 
            sender.navigation_view.pop_view()

    # Handle the 'Dismiss kb' button
    def dismiss_keyboard(self, sender):
        # When editing the name TextField, the keyboard covers the Cancel and Save buttons. If only the name TextField is changed, a button is needed to end editing of the TextField, which dismisses the keyboard, exposing the buttons.
        self['name_field'].end_editing()

    # Handle the default reps slider
    def reps_slider_changed(self, sender):
        # First, end editing of the name TextField and enable the save button
        self['name_field'].end_editing()
        sender.superview['save_button'].enabled = True and self['name_field'].delegate.is_name_specified()
        # Calculate the default reps value from the slider value:
        #  - scale the slider value (0 -> 1), multiplying by 20 (0 -> 20) 
        #  - and rounding up to the next integer, 
        #  - but to make the default reps range 1 -> 20,  first add 0.01 to the slider value for slider values < 0.5
        this_value = math.ceil(sender.value * 20 + 0.01 if sender.value < 0.5 else sender.value * 20)
        # When the resulting integer value changes, note the new integer value and update the def_reps label text in the edit_circuit view
        if this_value != self.default_reps:
          self.default_reps = this_value
          self['def_reps'].text = str(this_value)

    # Handle the Cancel button
    def cancel_button_tapped(self, sender):
        sender.navigation_view.pop_view() # Return to the previous view

    # Handle the Save button
    def save_button_tapped(self, sender):
        self.choice = False
        circuit_name = self['name_field'].text.strip()
        save_path = os.path.join(CIRCUITS_PATH, f"{circuit_name}.circuit")
        
        # See if the circuit name was changed
        name_change = False
        if self.mode != 'add' and self.input_circuit.circuit_name != circuit_name:
            print('Circuit name changed')
            name_change = True

        if (self.mode == 'add' or name_change) and Path(save_path).is_file():
            ''' 
                If a new circuit's name or the changed name of an existing circuit matches an existing circuit's name, present a modal asking if the existing circuit should be replaced or the save should be canceled.
            '''
            print('File already exists')

            def choice_made(sender):
                self.choice = sender.name
                already_exists_view.close()

            already_exists_view = ui.load_view(ALREADY_EXISTS_PATH)
            already_exists_view['label1'].text = f"{self['name_field'].text} already exists"
            already_exists_view['ae_cancel'].action = choice_made
            already_exists_view['ae_replace'].action = choice_made
            already_exists_view.present(style='sheet', hide_title_bar=True)
            already_exists_view.wait_modal()

            if self.choice == 'ae_cancel':
                return

        if name_change:
            ''' 
                If an existing circuit's name was changed, present a modal asking if the existing circuit should be renamed, if the circuit should be saved as a new circuit or if the save should be canceled.
            '''

            def choice_made(sender):
                print('Choice made: ', sender.name)
                self.choice = sender.name
                name_changed_view.close()
            
            name_changed_view = ui.load_view(NAME_CHANGED_PATH)
            name_changed_view['r_cancel'].action = choice_made
            name_changed_view['r_rename'].action = choice_made
            name_changed_view['r_new'].action = choice_made
            if self.choice == 'ae_replace':
                name_changed_view['replace_explanation'].text = 'Replace\nSave as new'
            name_changed_view.present(style='sheet', hide_title_bar=True)
            name_changed_view.wait_modal()

            if self.choice == 'r_cancel':
                return
            elif self.choice == 'r_rename':
                print('old file deleted')
                os.remove(os.path.join(CIRCUITS_PATH, f"{self.input_circuit.circuit_name}.circuit"))
        
        # Create a Circuit dataclass instance
        new_circuit = Circuit(
            circuit_name = circuit_name,
            default_reps = int(self['def_reps'].text),
            exercises = self['tableview1'].data_source.circuit_exercises
        )

        # Serialize the dataclass instance and write it to the data folder
        with open(save_path, 'w') as f:
            json.dump(asdict(new_circuit), f, indent=4)
        
        # For a new or renamed circuit, invoke the edit_selection view's callback refresh method to update its list of circuit names
        if self.mode == 'add' or self.choice:
            self.callback()
        
        # Return to the edit_selection view
        sender.navigation_view.pop_view()

    # Handle the edit_circuit view loaded event
    def did_load(self):
        # Connect action handlers to their view elements
        self['back_button'].action = self.back_button_tapped
        self['dkb_button'].action = self.dismiss_keyboard
        self['reps_slider'].action = self.reps_slider_changed
        self['cancel_button'].action = self.cancel_button_tapped
        self['save_button'].action = self.save_button_tapped
        # Set the name TextField's delegate object
        self['name_field'].delegate = TextFieldDelegate(self['name_field'])
        # Disable the Save button initially
        self['save_button'].enabled = False

    # A function to fill the edit_circuit view with values, either from the circuit being edited or defaults for adding a circuit. This method is called by the edit_selection view.
    def fill_circuit(self, circuit, mode, callback):
        '''
            self - a reference to the edit_circuit view
            circuit - a Circuit dataclass instance
            mode -  'add' or 'edit'
            callback - a method in the edit_selection view to refresh its TableView 
        ''' 
        # Note the inputs
        self.input_circuit = circuit 
        self.mode = mode
        self.callback = callback

        # Set the view's values
        self['name_field'].text = circuit.circuit_name
        self['def_reps'].text = str(circuit.default_reps)
        self['reps_slider'].value = circuit.default_reps / 20

        # Establish the TableView's data source and delegate. Note that the chained assignment allows both the data source and delegate methods to share the same  instance of the TableviewDataSource class, i.e 'self' is the same for both. This is necessary because the delegate methods depend on values defined by the data source methods.
        self['tableview1'].data_source = self['tableview1'].delegate = TableviewDataSource(circuit.exercises)

        self['tableview1'].allows_selection_during_editing = True
        

        
