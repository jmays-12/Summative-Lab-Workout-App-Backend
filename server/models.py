from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

db = SQLAlchemy()

VALID_CATEGORIES = ("cardio", "strength", "flexibility", "balance")


class Exercise(db.Model):
    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(db.Boolean, default=False, nullable=False)

    # An Exercise has many WorkoutExercises
    workout_exercises = db.relationship(
        'WorkoutExercise', back_populates='exercise', cascade='all, delete-orphan'
    )
    # An Exercise has many Workouts through WorkoutExercises
    workouts = association_proxy('workout_exercises', 'workout')

    # Table constraints (enforced by the database itself)
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0",
                        name='exercise_name_not_blank'),
        CheckConstraint(
            "category IN ('cardio', 'strength', 'flexibility', 'balance')",
            name='exercise_valid_category',
        ),
    )

    # Model validations (enforced in python before hitting the db)
    @validates('name')
    def validate_name(self, key, name):
        if not name or not name.strip():
            raise ValueError("Exercise name cannot be blank.")
        return name

    @validates('category')
    def validate_category(self, key, category):
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Category must be one of {VALID_CATEGORIES}.")
        return category

    def __repr__(self):
        return f'<Exercise {self.id}: {self.name}>'


class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    # A Workout has many WorkoutExercises
    workout_exercises = db.relationship(
        'WorkoutExercise', back_populates='workout', cascade='all, delete-orphan'
    )
    # A Workout has many Exercises through WorkoutExercises
    exercises = association_proxy('workout_exercises', 'exercise')

    __table_args__ = (
        CheckConstraint('duration_minutes > 0',
                        name='workout_positive_duration'),
    )

    @validates('duration_minutes')
    def validate_duration_minutes(self, key, value):
        if value is None or value <= 0:
            raise ValueError("Duration (minutes) must be a positive number.")
        return value

    def __repr__(self):
        return f'<Workout {self.id}: {self.date}>'


class WorkoutExercise(db.Model):
    __tablename__ = 'workout_exercises'

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey(
        'workouts.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey(
        'exercises.id'), nullable=False)
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    # A WorkoutExercise belongs to a Workout
    workout = db.relationship('Workout', back_populates='workout_exercises')
    # A WorkoutExercise belongs to an Exercise
    exercise = db.relationship('Exercise', back_populates='workout_exercises')

    __table_args__ = (
        CheckConstraint('reps IS NULL OR reps >= 0',
                        name='workout_exercise_non_negative_reps'),
        CheckConstraint('sets IS NULL OR sets >= 0',
                        name='workout_exercise_non_negative_sets'),
        CheckConstraint(
            'duration_seconds IS NULL OR duration_seconds >= 0',
            name='workout_exercise_non_negative_duration',
        ),
    )

    @validates('reps', 'sets', 'duration_seconds')
    def validate_non_negative(self, key, value):
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative.")
        return value

    def __repr__(self):
        return f'<WorkoutExercise {self.id}: workout={self.workout_id} exercise={self.exercise_id}>'
