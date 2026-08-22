from flask import Flask, make_response, request, jsonify
from flask_migrate import Migrate
from marshmallow import Schema, fields, validate, ValidationError
from sqlalchemy.exc import IntegrityError

from models import db, Exercise, Workout, WorkoutExercise, VALID_CATEGORIES

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

db.init_app(app)


# Schemas

class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, error="Name must not be blank.")
    )
    category = fields.String(
        required=True,
        validate=validate.OneOf(
            VALID_CATEGORIES, error=f"Category must be one of {VALID_CATEGORIES}.")
    )
    equipment_needed = fields.Boolean(load_default=False)


class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0, error="Reps cannot be negative.")
    )
    sets = fields.Integer(
        allow_none=True,
        validate=validate.Range(min=0, error="Sets cannot be negative.")
    )
    duration_seconds = fields.Integer(
        allow_none=True,
        validate=validate.Range(
            min=0, error="Duration (seconds) cannot be negative.")
    )


class WorkoutExerciseDetailSchema(WorkoutExerciseSchema):
    """Adds the nested exercise details (used when showing a workout's exercises)."""
    exercise = fields.Nested(ExerciseSchema)


class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(
        required=True,
        validate=validate.Range(
            min=1, error="Duration (minutes) must be positive.")
    )
    notes = fields.String(allow_none=True)


class WorkoutDetailSchema(WorkoutSchema):
    """Adds nested workout_exercises (with exercise + reps/sets/duration) for GET /workouts/<id>."""
    workout_exercises = fields.List(fields.Nested(WorkoutExerciseDetailSchema))


class ExerciseDetailSchema(ExerciseSchema):
    """Adds the associated workouts for GET /exercises/<id>."""
    workout_exercises = fields.List(fields.Nested(WorkoutExerciseSchema))


exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
exercise_detail_schema = ExerciseDetailSchema()

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_detail_schema = WorkoutDetailSchema()

workout_exercise_schema = WorkoutExerciseSchema()


# Workouts

@app.route('/workouts', methods=["GET"])
def get_all_workouts():
    workouts = Workout.query.all()
    return jsonify(workouts_schema.dump(workouts)), 200


@app.route('/workouts/<int:id>', methods=["GET"])
def get_workout_by_id(id):
    workout = db.session.get(Workout, id)
    if not workout:
        return jsonify({"error": "Workout not found"}), 404
    # Includes associated exercises with reps/sets/duration (stretch goal)
    return jsonify(workout_detail_schema.dump(workout)), 200


@app.route('/workouts', methods=["POST"])
def create_workout():
    json_data = request.get_json(silent=True) or {}

    # Schema level validation first
    try:
        data = workout_schema.load(json_data)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    # Model level validation / table constraints happen here
    try:
        workout = Workout(
            date=data['date'],
            duration_minutes=data['duration_minutes'],
            notes=data.get('notes'),
        )
        db.session.add(workout)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400

    return jsonify(workout_schema.dump(workout)), 201


@app.route('/workouts/<int:id>', methods=["DELETE"])
def delete_workout_by_id(id):
    workout = db.session.get(Workout, id)
    if not workout:
        return jsonify({"error": "Workout not found"}), 404
    # cascade='all, delete-orphan' on the relationship removes associated
    # WorkoutExercises automatically (stretch goal)
    db.session.delete(workout)
    db.session.commit()
    return make_response('', 204)


# Exercises

@app.route('/exercises', methods=["GET"])
def get_all_exercises():
    exercises = Exercise.query.all()
    return jsonify(exercises_schema.dump(exercises)), 200


@app.route('/exercises/<int:id>', methods=["GET"])
def get_exercise_by_id(id):
    exercise = db.session.get(Exercise, id)
    if not exercise:
        return jsonify({"error": "Exercise not found"}), 404
    # Includes associated workouts
    return jsonify(exercise_detail_schema.dump(exercise)), 200


@app.route('/exercises', methods=["POST"])
def create_exercise():
    json_data = request.get_json(silent=True) or {}

    try:
        data = exercise_schema.load(json_data)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        exercise = Exercise(
            name=data['name'],
            category=data['category'],
            equipment_needed=data.get('equipment_needed', False),
        )
        db.session.add(exercise)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400

    return jsonify(exercise_schema.dump(exercise)), 201


@app.route('/exercises/<int:id>', methods=["DELETE"])
def delete_exercise_by_id(id):
    exercise = db.session.get(Exercise, id)
    if not exercise:
        return jsonify({"error": "Exercise not found"}), 404
    # cascade='all, delete-orphan' removes associated WorkoutExercises too
    db.session.delete(exercise)
    db.session.commit()
    return make_response('', 204)


# WorkoutExercises

@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=["POST"],
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    exercise = db.session.get(Exercise, exercise_id)
    if not workout or not exercise:
        return jsonify({"error": "Workout or Exercise not found"}), 404

    json_data = request.get_json(silent=True) or {}

    try:
        data = workout_exercise_schema.load(json_data)
    except ValidationError as e:
        return jsonify({"errors": e.messages}), 400

    try:
        workout_exercise = WorkoutExercise(
            workout_id=workout_id,
            exercise_id=exercise_id,
            reps=data.get('reps'),
            sets=data.get('sets'),
            duration_seconds=data.get('duration_seconds'),
        )
        db.session.add(workout_exercise)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 400

    return jsonify(workout_exercise_schema.dump(workout_exercise)), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
