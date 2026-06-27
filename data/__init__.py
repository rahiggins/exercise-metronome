'''
   This script creates some data items associated with the contents of the folder named data, which is where the definitions of circuits and exercises are stored.
'''
import os
from dataclasses import dataclass, field
from typing import List

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))
CIRCUITS_PATH = os.path.join(DATA_PATH, 'Circuits')
EXERCISES_PATH = os.path.join(DATA_PATH, 'Exercises')

# A list of folders within the data folder.
folders = []
with os.scandir(DATA_PATH) as entries:
  for entry in entries:
    if entry.is_dir():
      folders.append(entry.name)

# Functions that return lists of circuit and exercise names. These are called here and in other views.
def get_exercises():
   return sorted(list(map(lambda x: x.split('.')[0], os.listdir(EXERCISES_PATH))))

def get_circuits():
   return sorted(list(map(lambda x: x.split('.')[0], os.listdir(CIRCUITS_PATH))))

exercises = get_exercises()
circuits = get_circuits()

# Dataclasses for exercises and circuits
@dataclass
class Exercise:
    exercise_name: str = ''
    start_delay: str = '0'
    rep_switch: bool = False
    reps: str = ''
    hold: str = '0'
    cadence: str = '0'

@dataclass
class Circuit:
    circuit_name: str = ''
    default_reps: int = 1
    exercises: List[Exercise] = field(default_factory=list)  # Default to an empty list


