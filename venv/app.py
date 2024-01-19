from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import re
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  
db = SQLAlchemy(app)
migrate = Migrate(app, db)

def is_valid_email(email):
    email_pattern = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w+$')
    return bool(re.match(email_pattern, email))

def db_print():
    users = User.query.all()

    # Print user details
    for user in users:
        print(f"email: {user.email}, Password: {user.password}")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    name = db.Column(db.String(60), nullable=True)
    surname = db.Column(db.String(60), nullable=True)
    age = db.Column(db.Numeric(3), nullable=True)
    sex = db.Column(db.Text, nullable=True)
    height = db.Column(db.Numeric(3), nullable=True)
    weight = db.Column(db.Numeric(3), nullable=True)
    bmi = db.Column(db.Numeric(10), nullable=True)
    bmr = db.Column(db.Numeric(10), nullable=True)
    carb = db.Column(db.Numeric(10), nullable=True)
    

    

    



with app.app_context():
    db.create_all()

# Home page - Login and Register links
@app.route('/')
def home():
    return render_template('home.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    alert_message = None

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            # Login successful
            return jsonify(email)
        else:
            # Login failed
            error_response = jsonify({'error': 'User not found'})
            error_response.status_code = 404
            return error_response

    return render_template('login.html', alert_message=alert_message)

# Register page
@app.route('/register', methods=['GET', 'POST'])    
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Your email validation logic here
        if not is_valid_email(email):
            error_response = jsonify({'error': 'Invalid email address'})
            error_response.status_code = 400
            return error_response

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            error_response = jsonify({'error': 'email already exists'})
            error_response.status_code = 409
            return error_response
            
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(email)

    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        age = int(request.form['age'])
        sex = request.form['sex']
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        email = request.form['email']
        bmi = round((weight / ((height/100) * (height/100))),2)
        bmr = None
        msg = None

        if sex == "Male":
            bmr = round((66.47 + (13.75 * weight) + (5.003 * height) - (6.755 * age)),2)
        else:
            bmr = round((655.1 + (9.563 * weight) + (1.85 * height) - (4.676 * age)),2)

        if bmi < 18.5:
            msg = "Underweight"
        elif bmi >= 18.5 and bmi < 25:
            msg = "Normal"
        elif bmi >= 25 and bmi < 30:
            msg = "Overweight"
        else:
            msg = "Obese"
        
        dbuser = User.query.filter_by(email=email).first()
        if not dbuser:
            error_response = jsonify({'error': 'User not found'})
            error_response.status_code = 404
            return error_response


        dbuser.name = name
        dbuser.surname = surname
        dbuser.age = age
        dbuser.sex = sex
        dbuser.height = height
        dbuser.weight = weight
        dbuser.bmi = bmi
        dbuser.bmr = bmr
        db.session.commit()
        

        return jsonify({
            'bmi': bmi,
            'bmr': bmr,
            'msg': msg,
            'message': 'User profile updated successfully'
        }
        )


    return render_template('profile.html')

@app.route('/users/<email>')
def users(email):
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({})
    
    return jsonify({
        'name': user.name,
        'surname': user.surname,
        'age': round((user.age),0),
        'sex': user.sex,
        'height': round((user.height),2),
        'weight': round((user.weight),2),
    })

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/calorie', methods=['GET', 'POST'])
def calorie():
    if request.method == 'POST':
        exc = request.form['exercise_level']
        email = request.form['email']
        m_cal = None

        dbuser = User.query.filter_by(email=email).first()
        if not dbuser:
            error_response = jsonify({'error': 'User not found'})
            error_response.status_code = 404
            return error_response

        if exc == "no_exercise":
            m_cal = float(dbuser.bmr) * 1.2
        elif exc == "light":
            m_cal = float(dbuser.bmr) * 1.315
        elif exc == "moderate":
            m_cal = float(dbuser.bmr) * 1.55
        elif exc == "heavy":
            m_cal = float(dbuser.bmr) * 1.725
        elif exc == "very_heavy":
            m_cal = float(dbuser.bmr) * 1.9

        if dbuser.bmi < 18.5:
            m_cal = m_cal + 250
        elif dbuser.bmi > 25:
            m_cal = m_cal - 250

        dbuser.m_cal = m_cal
        db.session.commit()

        return jsonify({
            'm_cal': round((m_cal),2)
        })


    return render_template('calorie.html')

@app.route('/diet', methods=['GET', 'POST'])
def diet():
    if request.method == 'POST':
        email = request.form['email']
        dbuser = User.query.filter_by(email=email).first()
        m_cal = float(request.form['m_cal'])


        if not dbuser:
            error_response = jsonify({'error': 'User not found'})
            error_response.status_code = 404
            return error_response

        weight = float(dbuser.weight)/0.46
        p = weight * 4
        f = float(request.form['fat'])*9
        carb = (m_cal - (p + f))/4
        if carb < 0:
            carb = 0

        dbuser.carb = carb
        db.session.commit()

        
        return jsonify({
            'carb': round(carb,2)
        })


    return render_template('diet.html')


# Run the app



if __name__ == '__main__':
    app.run(debug=True)
