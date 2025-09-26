from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
from pose_left import left_curl
from pose_right import right_curl
from pose_pushup import pushup
from pose_squat import squat
from PoseModule import poseDetector
import cv2
import mediapipe as mp
import numpy as np
import time
import logging
from models import db, User
from flask_bcrypt import Bcrypt
from functools import wraps
from forms import LoginForm, RegistrationForm
import json
import os
import matplotlib.pyplot as plt
import io
import base64

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necesario para session
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))


# Variable global para marcar el estado de finalización de cada ejercicio por sesión
exercise_finished_flag = {}
# Variable global para guardar errores por sesión y ejercicio
last_errors = {}

# --- Funciones para manejo de errores en JSON ---
def get_error_json_path(user_id, session_id):
    return os.path.join(os.path.dirname(__file__), f"errors_{user_id}_{session_id}.json")

def save_exercise_error(user_id, session_id, exercise, errors):
    path = get_error_json_path(user_id, session_id)
    data = {}
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    data[exercise] = errors
    with open(path, 'w') as f:
        json.dump(data, f)

def read_all_errors(user_id, session_id):
    path = get_error_json_path(user_id, session_id)
    if os.path.exists(path):
        with open(path, 'r') as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def clear_error_json(user_id, session_id):
    path = get_error_json_path(user_id, session_id)
    if os.path.exists(path):
        os.remove(path)

@app.route('/historial')
def historial():
    from models import ExerciseHistory, User
    data = ExerciseHistory.query.order_by(ExerciseHistory.timestamp.desc()).all()
    users = {u.id: u.username for u in User.query.all()}
    return render_template('historial.html', data=data, users=users)

@app.route('/grafica_historial')
@login_required
def grafica_historial():
    from models import ExerciseHistory
    user_id = session.get('user_id')
    data = ExerciseHistory.query.filter_by(user_id=user_id).order_by(ExerciseHistory.timestamp.asc()).all()
    if not data:
        return render_template('grafica_historial.html', img_data=None)
    import pandas as pd
    df = pd.DataFrame([{
        'Ejercicio': row.exercise,
        'Errores': row.errors,
        'Fecha': row.timestamp
    } for row in data])
    plt.figure(figsize=(10,5))
    for ejercicio in df['Ejercicio'].unique():
        sub = df[df['Ejercicio']==ejercicio]
        plt.plot(sub['Fecha'], sub['Errores'], marker='o', label=ejercicio)
    plt.xlabel('Fecha')
    plt.ylabel('Errores')
    plt.title('Curva de aprendizaje por ejercicio')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template('grafica_historial.html', img_data=img_data)

@app.route('/', methods = ['GET'])
def root():
    if 'user_id' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))
    
@app.route('/home', methods=['GET'])
@login_required
def home():
    return render_template('request_page.html')

@app.route('/show', methods=['POST', 'GET'])
@login_required
def show():
    if request.method == 'POST':
        exercises = request.form.getlist('exercise[]')
        reps = request.form.getlist('reps[]')
        series = list(zip(exercises, reps))
        session['series'] = series
        session['current'] = 0
        return redirect(url_for('run_series'))
    else:
        return redirect('/')

@app.route('/run_series')
@login_required
def run_series():
    global exercise_finished_flag
    series = session.get('series', [])
    current = session.get('current', 0)
    # Limpiar el estado de ejercicio terminado al iniciar uno nuevo
    exercise_finished_flag[current] = False
    if not series or current >= len(series):
        return render_template('video_page.html', finished=True)
    exercise, reps = series[current]
    # Forzar nuevo stream con parámetro único para evitar caché
    stream_url = url_for(f'video_feed_{exercise}', reps=reps) + f"&t={int(time.time()*1000)}"
    return render_template('video_page.html', exercise=exercise, reps=reps, stream_url=stream_url, finished=False)

@app.route('/video_feed_left')
@login_required
def video_feed_left():
    global exercise_finished_flag
    reps = int(request.args.get('reps', 0))
    session_id = session.get('current', 0)
    user_id = session.get('user_id')
    def gen():
        errors = 0
        for frame, err in left_curl(reps):  # Modifica left_curl para yield (frame, errores)
            errors = err
            yield frame
        save_exercise_error(user_id, session_id, 'left', errors)
        exercise_finished_flag[session_id] = True
        logging.info(f"Ejercicio terminado: session_id={session_id}, user_id={user_id}, errores={errors}")
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_right')
@login_required
def video_feed_right():
    global exercise_finished_flag
    reps = int(request.args.get('reps', 0))
    session_id = session.get('current', 0)
    def gen():
        for frame in right_curl(reps):
            yield frame
        exercise_finished_flag[session_id] = True
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_pushup')
@login_required
def video_feed_pushup():
    global exercise_finished_flag
    reps = int(request.args.get('reps', 0))
    session_id = session.get('current', 0)
    def gen():
        for frame in pushup(reps):
            yield frame
        exercise_finished_flag[session_id] = True
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_squat')
@login_required
def video_feed_squat():
    global exercise_finished_flag
    reps = int(request.args.get('reps', 0))
    session_id = session.get('current', 0)
    def gen():
        for frame in squat(reps):
            yield frame
        exercise_finished_flag[session_id] = True
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/exercise_status')
@login_required
def exercise_status():
    global exercise_finished_flag
    session_id = session.get('current', 0)
    user_id = session.get('user_id')
    finished = exercise_finished_flag.get(session_id, False)
    series = session.get('series', [])
    current = session.get('current', 0)
    exercise = series[current][0] if series and current < len(series) else 'left'
    errors = read_all_errors(user_id, session_id).get(exercise, 0)
    logging.info(f"Status: session_id={session_id}, user_id={user_id}, finished={finished}, exercise={exercise}, errores={errors}")
    return jsonify({'finished': finished, 'errors': errors})

@app.route('/next_exercise')
@login_required
def next_exercise():
    series = session.get('series', [])
    current = session.get('current', 0)
    user_id = session.get('user_id')
    errors_dict = read_all_errors(user_id, current)
    logging.info(f"Avanzando a next_exercise: session_id={current}, user_id={user_id}, errores_dict={errors_dict}")
    if series and current < len(series):
        exercise, reps = series[current]
        errors = errors_dict.get(exercise, 0)
        from models import ExerciseHistory, db
        import datetime
        history = ExerciseHistory(
            user_id=user_id,
            exercise=exercise,
            reps=reps,
            errors=errors,
            timestamp=datetime.datetime.now().date()  # Solo la fecha
        )
        db.session.add(history)
        # --- Reintento de commit si la base de datos está bloqueada ---
        max_retries = 5
        for attempt in range(max_retries):
            try:
                db.session.commit()
                logging.info(f"Guardado en BD: user_id={user_id}, exercise={exercise}, reps={reps}, errores={errors}")
                break
            except Exception as e:
                logging.error(f"Error al guardar en BD: {e}")
                if 'database is locked' in str(e):
                    db.session.rollback()
                    time.sleep(0.5)
                else:
                    db.session.rollback()
                    raise
        db.session.remove()
    if current + 1 < len(series):
        session['current'] = current + 1
        return redirect(url_for('run_series'))
    else:
        # Limpiar el archivo JSON al terminar la serie
        clear_error_json(user_id, current)
        return render_template('video_page.html', finished=True)

@app.route('/fin_ejercicio')
@login_required
def fin_ejercicio():
    return render_template('fin_ejercicio.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        name = form.name.data
        age = form.age.data
        email = form.email.data
        gender = form.gender.data
        password = form.password.data
        if User.query.filter_by(username=username).first():
            form.username.errors.append('Usuario ya existe')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=email).first():
            form.email.errors.append('El correo ya está registrado')
            return render_template('register.html', form=form)
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            name=name,
            age=age,
            email=email,
            gender=gender,
            password=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('home'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            form.password.errors.append('Usuario o contraseña incorrectos')
            return render_template('login.html', form=form)
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/cuenta', methods=['GET', 'POST'])
@login_required
def cuenta():
    from models import User
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        email = request.form.get('email')
        gender = request.form.get('gender')
        password = request.form.get('password')
        user.name = name
        user.age = int(age)
        user.email = email
        user.gender = gender
        if password:
            from flask_bcrypt import Bcrypt
            bcrypt = Bcrypt(app)
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        from models import db
        db.session.commit()
        return render_template('cuenta.html', user=user, msg='Datos actualizados correctamente')
    return render_template('cuenta.html', user=user)

@app.route('/exportar_excel')
@login_required
def exportar_excel():
    from models import ExerciseHistory
    user_id = session.get('user_id')
    data = ExerciseHistory.query.filter_by(user_id=user_id).order_by(ExerciseHistory.timestamp.asc()).all()
    rows = []
    for row in data:
        rows.append({
            'Ejercicio': row.exercise,
            'Repeticiones': row.reps,
            'Errores': row.errors,
            'Fecha': row.timestamp.strftime('%Y-%m-%d')
        })
    import pandas as pd
    df = pd.DataFrame(rows)
    file_path = f"historial_{user_id}.xlsx"
    df.to_excel(file_path, index=False, sheet_name='Historial')
    from flask import send_file
    return send_file(file_path, as_attachment=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:admin@localhost/fitter'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host = "0.0.0.0", debug=True)