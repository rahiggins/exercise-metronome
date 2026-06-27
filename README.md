Exercise Metronome, a Pythonista3 app, is a simple exercise timer for circuits of exercises. 

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

The entry point for the Exercise Metronome is ExerciseMetronome.py. It presents a view with a segmented control that has two segments: Run and Edit. Initially, the Run segment is selected and a list of circuits is displayed. When the Edit segment is selected, a list comprising Circuits and Exercises is displayed.

When a circuit is selected from the Run list, the function run_circuit, which was imported from the run_circuit package, is called to run the selected circuit.

When Circuits or Exercises is selected from the Edit list, an instance of the EditSelection class, which was imported from the edit_selection package, is created and presented. The EditSelection view displays a list of the selected items, circuits or exercises.
