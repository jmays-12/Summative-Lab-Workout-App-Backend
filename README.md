# Workout Tracker API

A simple REST API for tracking workouts and exercises.

This API lets you:

* Create and manage workouts
* Create and manage exercises
* Add exercises to workouts with reps, sets, or duration

## Setup

1. Install dependencies:

```bash
pipenv install
pipenv shell
```

2. Set up the database using the included migrations:

```bash
cd server
export FLASK_APP=app.py
flask db upgrade head
```

3. Add sample data:

```bash
python seed.py
```

4. Start the server:

```bash
python app.py
```

The API will run at `http://localhost:5555`

## Running Tests

From the project root:

```bash
pytest
```

## API Endpoints

### Workouts

* `GET /workouts` - View all workouts
* `GET /workouts/<id>` - View one workout
* `POST /workouts` - Create a workout
* `DELETE /workouts/<id>` - Delete a workout

### Exercises

* `GET /exercises` - View all exercises
* `GET /exercises/<id>` - View one exercise
* `POST /exercises` - Create an exercise
* `DELETE /exercises/<id>` - Delete an exercise

### Add Exercise to Workout

* `POST /workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` - Add an exercise to a workout with reps, sets, or duration

## Exercise Categories

* `cardio`
* `strength`
* `flexibility`
* `balance`
