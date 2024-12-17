# Lift Optimizer
lift optimization dev

## ER Diagram:
![Data model](ER.png "ERD")

## Lift State Transitions
![Transition Diagram](StateDiagram.png "Lift State Transitions")

## Baseline model
Baseline Model
- total passenger time on lift is measured as total of time to onboard, time while lift is moving, time while lift is loading on other floors, and time to offboard
- total time for lift movement follows an acceleration model, with dynamics having a fixed constant acceleration (a = 1ms-2) to a max speed (v = 4ms-1)

Baseline Model passenger assignment to lifts for lift coordination
- no lift movement when no passenger is in lift or assigned
- assigns passengers following the immediate nearest floor along the direction of lift, subject to lift capacity
- passenger assignment with `assign_multi = True`, where the taking lift will be the first arriving lift
- passengers are onboarded with `bypass_prev_assignment = True`, bypassing all existing assignments and onboarding priority is from *earliest arrival*
- lifts are redirected from existing movement, if it has capacity and is able to fetch a passenger between current lift movement and lift target along direction of movement
- redirection frees passengers of the previous target floor from previous assignment, and assigns passengers from the redirected floor
- when a new passenger arrives, the nearest lift is searched (currently only on moving lifts), and if it has capacity, that passenger is assigned

## TODO:
- add live visualizer for multi-floor and multi-lift with passenger counts

- evaluate travel time

- setup lift assignment and coordination module
