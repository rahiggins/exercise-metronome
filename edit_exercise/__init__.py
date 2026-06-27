'''
    This script defines the edit_exercise view class, which is associated with the edit_exercise pyui file. The edit_eircuit view is used to create and edit exercise definitions. Using the edit_exercise view,
    _ new exercises can be defined
    - existing exercises can be renamed or duplicated
    - the definitions of existing exercises can be edited
'''
from dataclasses import asdict
import ui  # type: ignore
import os
from pathlib import Path
import math
import json
from data import Exercise, EXERCISES_PATH
'''
    From the data package, import:
    - the Exercise dataclass
    - the paths to the Exercises 
'''
from modals import ALREADY_EXISTS_PATH, NAME_CHANGED_PATH, UNSAVED_PATH
'''
    From the modals package, import:
    - the path to the already_exists_view definition file (already_exists.pyui)
    - the path to the name_changed_view definition file (name_changed.pyui)
    - the path to the unsaved_view definition file (unsaved.pyui)
'''

EDIT_EXERCISE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
EDIT_EXERCISE_PYUI_PATH = os.path.join(EDIT_EXERCISE_PATH, 'edit_exercise')

# The delegate class for the exercise name TextField
class TextFieldDelegate:

    def __init__(self, textfield):
        # Make a note of the TextField instance that this delegate is associated with for the is_name_specified function
        self.textfield = textfield

    # Handle changes to the exercise name
    def textfield_did_change(self, sender):
        # Enable the save button if the exercise name is not empty, otherwise disable it
        if sender.text:
            sender.superview['save_button'].enabled = True
        else:
            sender.superview['save_button'].enabled = False

    # A function to check if the exercise name is specified
    def is_name_specified(self):
        return self.textfield.text != ''
        
# The custom view class for the edit_exercise view
class EditExercise(ui.View):

    # Initialize internal variables
    def __init__(self):
        # Current values of reps and time intervals
        self.reps = 0
        self.start_delay = 0
        self.hold = 0
        self.cadence = 0

        self.mode = ''  # 'add' or 'edit', set in function fill_exercise
    
    # End editing of the name TextField
    def endEditing(self, view):
        '''
            When exercise definition values are changed, 
            - end editing of the name TextField, which dismisses the keyboard and invokes the textfield_did_change function of the TextField delegate
            - enable the save button if the name TextField is not empty
        '''
        view['name_field'].end_editing()
        view['save_button'].enabled = True and view['name_field'].delegate.is_name_specified()

    # Handle the back button
    def back_button_tapped(self, sender):

        # Check for unsaved changes
        new_exercise = Exercise( # Create an Exercise dataclass instance from the current values
            exercise_name=self['name_field'].text.strip(),
            start_delay=self['sd_interval'].text,
            rep_switch=self['switch1'].value,
            reps=self['num_reps'].text,
            hold=self['h_interval'].text,
            cadence=self['c_interval'].text
        )
        if new_exercise != self.input_exercise:
            # If the new exercise values differ from the initial values, present a modal to ask if the new values should be discarded or not.
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
            sender.navigation_view.pop_view()

    # Handle the 'Dismiss kb' button
    def dismiss_keyboard(self, sender):
        # When editing the name TextField, the keyboard covers the Cancel and Save buttons. If only the name TextField is changed, a button is needed to end editing of the TextField, which dismisses the keyboard, exposing the buttons.
        self['name_field'].end_editing()

    # Handle the Use default/Use slider switch
    def switch_toggled(self, sender):
        # First, end editing of the name TextField and enable the save button
        self.endEditing(sender.superview)
        if sender.value:
            # If 'Use slider', display the slider value (0 - 1) scaled to the number of reps (0-20) rounded down to the nearest integer
            self.reps = math.floor(self['r_slider'].value * 20)
            self['num_reps'].text = str(self.reps)
        else:
            # If 'Use default', clear the number of reps TextField
            self['num_reps'].text = ''

    # Handle the reps slider
    def rep_slider_changed(self, sender):
        # First, end editing of the name TextField and enable the save button
        self.endEditing(sender.superview)
        if self['switch1'].value:
            # Calculate the default reps value from the slider value:
            #  - scale the slider value (0 -> 1), multiplying by 20 (0 -> 20) 
            #  - and rounding down to the nearest integer
            this_value = math.floor(sender.value * 20)
            # When the resulting integer value changes, note the new integer value and update the num_reps label text in the edit_exercise view
            if this_value != self.reps:
                self.reps = this_value
                self['num_reps'].text = str(this_value)

    # Handle the time sliders - start delay, hold and cadence
    # Time intervals can be set in half second increments from 0 to 20 seconds
    def time_slider_changed(self, sender):
        # First, end editing of the name TextField and enable the save button
        self.endEditing(sender.superview)
        # Calculate the time interval value from the slider value:
        #  - scale the slider value (0 -> 1), multiplying by 200 (0 -> 200) so that intervals in tenths of seconds can be specified
        #  - and rounding down to the nearest integer
        this_value = math.floor(sender.value * 200)
        if math.fmod(this_value, 5) == 0:
            # When the value is a multiple of 5 (i.e. a full or half second value) ...
            match sender.name:
                # For the changed slider ...
                case 'sd_slider':
                    if this_value != self.start_delay:
                        # If this value differs from the value currently displayed, note the new value, scaled to tenths of a second, and update the corresponding label text, displaying zero as 0 instead of 0.0
                        self.start_delay = this_value / 10
                        self['sd_interval'].text = str(self.start_delay).replace('0.0', '0')
                case 'h_slider':
                    if this_value != self.hold:
                        self.hold = this_value / 10
                        self['h_interval'].text = str(self.hold).replace('0.0', '0')
                case 'c_slider':
                    if this_value != self.cadence:
                        self.cadence = this_value / 10
                        self['c_interval'].text = str(self.cadence).replace('0.0', '0')

    # Handle the Cancel button
    def cancel_button_tapped(self, sender):
        sender.navigation_view.pop_view() # Return to the previous view

    # Handle the Save button
    def save_button_tapped(self, sender):
        self.choice = False
        exercise_name = self['name_field'].text.strip()

        # See if the exercise name was changed
        name_change = False
        if self.mode != 'add' and self.input_exercise.exercise_name != exercise_name:
            ''' 
                If a new exercise's name or the changed name of an existing exercise matches an existing exercise's name, present a modal asking if the existing exercise should be replaced or the save should be canceled.
            '''
            print('Exercise name changed')
            name_change = True

        save_path = os.path.join(EXERCISES_PATH, f"{exercise_name}.exercise")
        if (self.mode == 'add' or name_change) and Path(save_path).is_file():
            print('File already exists')
            self.choice = False

            def choice_made(sender):
                self.choice = sender.name
                already_exists_view.close()

            already_exists_view = ui.load_view(ALREADY_EXISTS_PATH)
            already_exists_view['label1'].text = f"{exercise_name} already exists"
            already_exists_view['ae_cancel'].action = choice_made
            already_exists_view['ae_replace'].action = choice_made
            already_exists_view.present(style='sheet', hide_title_bar=True)
            already_exists_view.wait_modal()

        if self.choice == 'ae_cancel':
            return

        if name_change:
            ''' 
                If an existing exercise's name was changed, present a modal asking if the existing exercise should be renamed, if the exercise should be saved as a new exercise or if the save should be canceled.
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
                print('name changed, replace previously selected')
                name_changed_view['replace_explanation'].text = f"Rename: delete {self.input_exercise.exercise_name}.exercise and replace {exercise_name}.exercise\n\nSave as new: replace {exercise_name}.exercise without deleting {self.input_exercise.exercise_name}.exercise"
            name_changed_view.present(style='sheet', hide_title_bar=True)
            name_changed_view.wait_modal()

        if self.choice == 'r_cancel':
            return
        elif self.choice == 'r_rename':
            print('old file deleted')
            os.remove(os.path.join(EXERCISES_PATH, f"{self.input_exercise.exercise_name}.exercise"))
                
        # Create an Exercise dataclass instance
        new_exercise = Exercise(
            exercise_name = exercise_name,
            start_delay = self['sd_interval'].text,
            rep_switch = self['switch1'].value,
            reps = self['num_reps'].text,
            hold = self['h_interval'].text,
            cadence = self['c_interval'].text
        )

        # Serialize the dataclass instance and write it to the data folder
        with open(save_path, 'w') as f:
            json.dump(asdict(new_exercise), f, indent=4)
        
        # For a new or renamed exercise, invoke the edit_selection view's callback refresh method to update its list of exercise names
        if self.mode == 'add' or self.choice:
            self.callback()
        
        # Return to the edit_selection view
        sender.navigation_view.pop_view()

    # Handle the edit_exercise view loaded event
    def did_load(self):
        # Connect action handlers to their view elements
        self['back_button'].action = self.back_button_tapped
        self['dkb_button'].action = self.dismiss_keyboard
        self['switch1'].action = self.switch_toggled
        self['sd_slider'].action = self.time_slider_changed
        self['r_slider'].action = self.rep_slider_changed
        self['h_slider'].action = self.time_slider_changed
        self['c_slider'].action = self.time_slider_changed
        self['cancel_button'].action = self.cancel_button_tapped
        self['save_button'].action = self.save_button_tapped
        # Set the name TextField's delegate object
        self['name_field'].delegate = TextFieldDelegate(self['name_field'])
        # Disable the Save button initially
        self['save_button'].enabled = False

    # A function to fill the edit_exercise view with values, either from the exercise being edited or defaults for adding an exercise. This method is called by the edit_selection view.
    def fill_exercise(self, exercise, mode, callback):
        '''
            self - a reference to the edit_exercise view
            exercise - an Exercise dataclass instance
            mode -  'add' or 'edit'
            callback - a method in the edit_selection view to refresh its TableView 
        ''' 
        # Note the inputs
        self.input_exercise = exercise
        self.mode = mode
        self.callback = callback

        # Set the view's values
        self['name_field'].text = exercise.exercise_name
        self['switch1'].value = exercise.rep_switch
        if exercise.rep_switch:
            self['num_reps'].text = exercise.reps
            self['r_slider'].value = float(exercise.reps) / 20
        else:
            self['num_reps'].text = ''
            self['r_slider'].value = 0
        self['sd_interval'].text = exercise.start_delay
        self['sd_slider'].value = float(exercise.start_delay) / 20
        self['h_interval'].text = exercise.hold
        self['h_slider'].value = float(exercise.hold) / 20
        self['c_interval'].text = exercise.cadence
        self['c_slider'].value = float(exercise.cadence) / 20

        
