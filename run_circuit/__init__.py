'''
    This script defines the run_circuit function, which runs a circuit of exercises. The run_circuit function is called from the run_edit view when a circuit is selected from the Run segment. The function presents a view that displays the remaining number of reps and provides a pause/play button to pause and resume the circuit. The pause/play button initially shows a pause icon. 

    To start running the circuit, the run_circuit function calls a function named circuit_loop that performs the exercises of the circuit. This function runs on the background thread because it sleeps between playing sound cues. By running circuit_loop on the background thread, the UI can remain responsive when circuit_loop is sleeping. Function circuit_loop has two parameters: the exercise list index to start at and the rep to start at. Both default to 0.
    
    When the pause/play button is tapped, the button's icon toggles between the pause icon and a play icon. When the button is tapped to pause, a boolean is set to indicate that and the text 'pausing...' is displayed. The circuit_loop function tests that boolean after each sleep. When circuit_loop detects a pause, it toggles the button icon, removes the 'pausing...' text, records the current exercise and rep, and then exits.
    
    When the button is tapped to resume after a pause, the function displays a modal with the choices: Resume, Back up and Restart with a slider to specify the number of reps to back up. When a choice is made, the modal view is closed, the pause boolean is set to False, a resuming boolean is set to True, the text 'resuming...' is displayed and the circuit_loop function is called with the index of the paused exercise and the chosen start rep as arguments. When resuming, the circuit_loop function first:
    - displays the remaining reps
    - sleeps for 5 seconds, instead of sleeping for the exercise's start delay interval
    - removes the 'resuming...' text from view
    - resets the resuming boolean
    - toggles the pause/play icon to pause
    before running the remaining portion of the circuit.
'''
import ui # type: ignore
import os
import json
import math
from data import EXERCISES_PATH, Exercise, Circuit
''' 
    From the data package, import:
    - the path to the Exercises folder
    - the Exercise and Circuit dataclasses
'''
from modals import RESUME_PATH
'''
    From the modals package, import:
    - the path to the resume_view definition file (resume.pyui)
'''

RUN_CIRCUIT_PYUI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_circuit')

# The function to run a circuit
def run_circuit(nav, circuit):
    print('run_circuit entered')
    import sound # type: ignore
    import time
    import console # type: ignore
    import shortcuts # type: ignore
    pause_displayed = True # Initially, the pause/play button show a pause icon
    paused = False # Set in function pause_play_button_tapped, tested after each sleep()
    resuming = False # Set in function pause_play_button_tapped
    exiting = False # Set in function back_button_tapped
    paused_exercise = 0 # Used for resuming after a pause
    paused_rep = 0 # Used for resuming after a pause

    # Handle the back button
    def back_button_tapped(sender):
        # Set paused and exiting to True. Function pause_detected will effect the exit.
        nonlocal paused, exiting
        print('exiting')
        paused = True
        exiting = True

    # Handle the pause/play button
    def pause_play_button_tapped(sender):
        nonlocal pause_displayed, paused, resuming, paused_exercise, paused_rep
        if pause_displayed:
            # When the pause button is tapped, the circuit_loop function, running in the background, will detect it after the completion of the currrent or next sleep()
            print("Circuit paused")
            paused = True
            run_circuit_view['resuming_label'].text = 'pausing...' # Show that the pause 
        else:
            # When the play button is tapped, a modal is presented to adjust the rep at which to resume. Then function circuit_loop is called
            print('Circuit resumed')
            print(f"Circuit paused, exercise: {str(paused_exercise)}, rep: {str(paused_rep)}")
            choice = 'resume_button'
            backup_reps = 0

            # Handle button taps in the modal
            def choice_made(sender):
                # Note which button was tapped and close the modal
                nonlocal choice
                choice = sender.name
                resume_view.close()

            # Handle the back up reps slider
            def bur_slider_changed(sender):
                nonlocal backup_reps
                # Calculate the back up reps value from the slider value:
                #  - scale the slider value (0 -> 1), multiplying by the paused rep (0 - paused rep)
                #  - and rounding down to the previous integer 
                this_value = math.floor(sender.value * paused_rep)
                if this_value != backup_reps:
                    # When the resulting integer value changes, note the new integer value and update the resume view
                    backup_reps = this_value
                    resume_view['bu_reps'].text = str(backup_reps)
                    resume_view['backup_button'].enabled = backup_reps > 0
                    resume_view['title'].text = f"Resuming {circuit.exercises[paused_exercise]}\nat rep {str(paused_rep + 1 - backup_reps)}"
            
            # Create the resume modal view
            resume_view = ui.load_view(RESUME_PATH)
            resume_view['title'].text = f"Resuming {circuit.exercises[paused_exercise]}\nat rep {str(paused_rep + 1)}"
            # Connect the view's buttons to their handlers
            resume_view['resume_button'].action = choice_made
            resume_view['backup_button'].action = choice_made
            resume_view['backup_button'].enabled = False
            resume_view['restart_button'].action = choice_made
            # Initialize the back up reps slider and connect it to its handler
            resume_view['bu_reps'].text = '0'
            resume_view['bur_slider'].value = 0
            resume_view['bur_slider'].action = bur_slider_changed
            if paused_rep == 0:
                resume_view['bur_slider'].enabled = False
                resume_view['restart_button'].enabled = False
            # Present the modal and wait for it to close
            resume_view.present(style='sheet', hide_title_bar=True)
            resume_view.wait_modal()

            # When the resume rep choice has been made, end the pause and resume the cicuit by calling function circuit_loop
            paused = False
            resuming = True
            match choice:
                case 'resume_button':
                    resume_rep = paused_rep
                case 'backup_button':
                    resume_rep = paused_rep - backup_reps
                case 'restart_button':
                    resume_rep = 0
            run_circuit_view['resuming_label'].text = 'resuming...'
            circuit_loop(paused_exercise, resume_rep)
    # End of the pause_play_button_tapped function        

    # The function to perform the exercises of a circuit
    @ui.in_background
    def circuit_loop(exercise_index=0, first_exercise_rep_index=0):
        # The parameters define the place in the circuit to start
        # - the exercise to start with
        # - the rep in that exercise to start with
        nonlocal pause_displayed, paused, resuming, paused_exercise, paused_rep
        print(f"circuit_loop entered with {str(exercise_index)} and {str(first_exercise_rep_index)}")

        # Handle the detection of a pause request
        def pause_detected(exercise, rep, location):
            # This function is called after a sleep() call when the paused boolean is true
            # Parameters:
            #   exercise - the index in the exercises list of the current exercise
            #   rep - the current rep
            #   location - an integer indicating where the pasue was detected
            nonlocal pause_displayed, paused_exercise, paused_rep
            print('Paused detected ' + location)
            if exiting:
                # If the back button was tapped ...
                print('exiting')
                console.set_idle_timer_disabled(False)  # Enable screen locking
                # Set Do Not Disturb off
                shortcuts.open_url('shortcuts://run-shortcut?name=SetDND&input=text&text=Off')
                nav.pop_view() # revert to the previous run_edit view
            
            # Assign the input arguments to global variables to make the values available to the pause_play_button_tapped function
            paused_exercise = exercise
            paused_rep = rep

            # Remove the 'pausing...' text from the view and replace the pause icon with a play icon. Set pause_displayed to false to indicate that the circut has been paused
            run_circuit_view['resuming_label'].text = ''
            run_circuit_view['pause_play_button'].image = ui.Image.named('iob:ios7_play_256')
            pause_displayed = False

        # Handle a background color change in an exercise with a non-zero hold interval
        def change_color(color):
            # Animate background to the specified color over 1.0 seconds
            def animation():
                run_circuit_view.background_color = (color)
            ui.animate(animation, duration=1.0)

        # Perform the exercises of the circuit. Loop through the exercises in the circuits.exercise list. For each exercise, loop though the designated number of reps.
        for e in range(exercise_index, len(circuit.exercises)):
            # For each exercise ...

            # Load the exercise definition into an instance of the Exercise dataclass and convert its string representations of numbers into float/int values 
            exercise = Exercise(**json.load(open(os.path.join(EXERCISES_PATH, circuit.exercises[e] +'.exercise')))) 
            start_delay = float(exercise.start_delay)
            reps = int(exercise.reps if exercise.rep_switch else circuit.default_reps)
            hold = float(exercise.hold)
            cadence = float(exercise.cadence)

            lastRep = reps - 1 # A finished noise will be made during the last rep

            # Show the exercise name in the run_circuit view
            run_circuit_view['exercise_name'].text = exercise.exercise_name

            # Prepare for performing the circuit. Check if the circuit is being resumed after a pause and check if a pause has been requested.
            if not resuming:
                # SHow the number of reps in the run_circuit view and sleep for the start delay interval or at least 1 second
                run_circuit_view['countdown'].text = str(reps)
                time.sleep(1)
                time.sleep(start_delay - 1 if start_delay >= 1 else start_delay )
            else:
                # When resuming after a pause, show the remaining reps in the run_circuit view and sleep for 5 seconds
                run_circuit_view['countdown'].text = str(reps - first_exercise_rep_index)
                time.sleep(5)
                # Remove the 'resuming...' text from the view and replace the play icon with a pause icon
                run_circuit_view['resuming_label'].text = ''
                resuming = False
                pause_displayed = True
                run_circuit_view['pause_play_button'].image = ui.Image.named('iob:ios7_pause_256')
            if paused:
                # If a pause was requested, handle it and break out of exercises loop
                pause_detected(e, 0, '1') 
                break

            # Perform the reps of the current exercise
            for r in range(first_exercise_rep_index, reps):
                if paused:
                    # If a pause was requested, handle it and break out of the reps loop
                    pause_detected(e, r, '2')
                    break
                # For each rep, show the remaining reps in the run_circuit view and play a sound cue
                run_circuit_view['countdown'].text = str(reps - (r + 1))
                #sound.play_effect('game:Beep', 0.25)  # Make a sound
                sound.play_effect('digital:ZapThreeToneUp', 0.75) # Start of the rep
                if hold > 0:
                    # For exercises with a hold duration, change the view's background color, sleep for the hold duration and then play a sound cue
                    ui.delay(lambda: change_color('#ffddcc'), 0)
                    time.sleep(hold)
                    ui.delay(lambda: change_color('#ffffff'), 0)
                    sound.play_effect('digital:ZapThreeToneDown', 0.75)  # End of duration
                    if paused:
                        # If a pause was requested, handle it and break out of the reps loop
                        pause_detected(e, r + 1, '3')
                        break
                if r != lastRep:
                    # Until the last rep, sleep for the cadence interval 
                    time.sleep(cadence)
                else:
                    # On the last rep, sleep for a second and a half, play an end of exercise sound cue, remove the remaining reps text and the exercise name from the run_circuit view and sleep for the remainder of the cadence interval 
                    time.sleep(1.5)
                    sound.play_effect('drums:Drums_14', 0.75)  # End of the reps
                    run_circuit_view['countdown'].text = ''
                    run_circuit_view['exercise_name'].text = ''
                    time.sleep(cadence - 1.5 if cadence > 1.5 else 0)
                if paused:
                    # If a pause was requested, handle it and break out of the reps loop
                    pause_detected(e, r + 1, '4')
                    break
            # end of 'for r in range(reps)'
            else:
                # If the reps loop completed, set the first exercise rep index to 0 in case it was non-zero because of a resume after a pause
                first_exercise_rep_index = 0
            # If a pause was requested, break out of the exercises loop
            if paused: break
        # end of 'for e in exerciseList'
        else:
            # If the exercises loop completed, clean up and revert to the run_edit view
            console.set_idle_timer_disabled(False)  # Enable screen locking
            # Set Do Not Disturb off
            shortcuts.open_url('shortcuts://run-shortcut?name=SetDND&input=text&text=Off')
            nav.pop_view()
    # End of the circuit_loop function

    # Create the run_circuit view
    run_circuit_view = ui.load_view(RUN_CIRCUIT_PYUI_PATH)
    # Add the circuit name to the view
    run_circuit_view['circuit_name'].text = circuit.circuit_name
    # Connect the view's button to their handlers
    run_circuit_view['pause_play_button'].action = pause_play_button_tapped
    run_circuit_view['back_button'].action = back_button_tapped
    # Present to run_circuit view
    nav.push_view(run_circuit_view)

    # Prevent the screen from locking and set Do Not Disturb on
    console.set_idle_timer_disabled(True)
    shortcuts.open_url('shortcuts://run-shortcut?name=SetDND&input=text&text=On')

    # Play a sequence of sound cues to indicate the circuit is about to start
    countdownTones = ['piano:G3', 'piano:F3', 'piano:E3', 'piano:D3', 'piano:C3']
    time.sleep(4)
    for tone in countdownTones:
        time.sleep(1)
        sound.play_effect(tone, 0.1)

    # Perform the circuit
    circuit_loop()
    if paused:
        print(f"Circuit paused, exercise: {str(paused_exercise)}, rep: {str(paused_rep)}")
# End of the run_circuit function
