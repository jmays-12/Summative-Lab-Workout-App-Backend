#!/usr/bin/env python3
from datetime import date

from app import app
from models import db, Exercise, Workout, WorkoutExercise

with app.app_context():
    print("Clearing existing data...")
    WorkoutExercise.query.delete()
    Workout.query.delete()
    Exercise.query.delete()
    db.session.commit()

    print("Seeding exercises...")
    push_up = Exercise(name="Push Up", category="strength",
                       equipment_needed=False)
    squat = Exercise(name="Barbell Squat",
                     category="strength", equipment_needed=True)
    running = Exercise(name="Running", category="cardio",
                       equipment_needed=False)
    jump_rope = Exercise(
        name="Jump Rope", category="cardio", equipment_needed=True)
    yoga = Exercise(name="Yoga Stretch", category="flexibility",
                    equipment_needed=False)
    db.session.add_all([push_up, squat, running, jump_rope, yoga])
    db.session.commit()

    print("Seeding workouts...")
    # duration_minutes = length of the whole workout session
    workout_1 = Workout(date=date(2026, 8, 1),
                        duration_minutes=45, notes="Morning strength session")
    workout_2 = Workout(date=date(2026, 8, 3),
                        duration_minutes=30, notes="Quick cardio burst")
    workout_3 = Workout(date=date(2026, 8, 5),
                        duration_minutes=60, notes="Full body + stretch")
    db.session.add_all([workout_1, workout_2, workout_3])
    db.session.commit()

    print("Seeding workout_exercises...")
    # duration_seconds = how long that one exercise took within the workout
    # (only set for exercises timed rather than counted in reps/sets)
    workout_exercises = [
        WorkoutExercise(workout=workout_1, exercise=push_up, reps=15, sets=3),
        WorkoutExercise(workout=workout_1, exercise=squat, reps=10, sets=4),
        WorkoutExercise(workout=workout_2, exercise=running,
                        duration_seconds=1200),   # 20 min run
        WorkoutExercise(workout=workout_2, exercise=jump_rope,
                        duration_seconds=600),   # 10 min
        WorkoutExercise(workout=workout_3, exercise=yoga,
                        duration_seconds=900),        # 15 min
        WorkoutExercise(workout=workout_3, exercise=push_up, reps=20, sets=3),
    ]
    db.session.add_all(workout_exercises)
    db.session.commit()

    print("Seeding complete!")
