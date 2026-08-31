from flask import render_template,request, url_for, session, flash, redirect
from models import db, Admin, Department, Doctor, Patient, Appointment, Treatment, Doctor_Schedule
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from functools import wraps
from datetime import datetime, timedelta

#Functions and decorators used for efficiency
def login_auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash ('Kindly login to continue')
            return redirect(url_for('home'))
    return inner

def logout_auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            return func(*args, **kwargs)
        else:
            flash("You are already logged in.")
            return redirect(url_for('home'))
    return inner

def admin_auth(func):
    @wraps(func)
    def inner2(*args,**kwargs):
        if session['role'] == 'admin':
            return func(*args,**kwargs)
        else:
            flash("Access Denied.")
            return redirect(url_for("home"))
    return inner2

def doc_auth(func):
    @wraps(func)
    def inner2(*args,**kwargs):
        if session['role'] == 'doctor':
            return func(*args,**kwargs)
        else:
            flash("Access Denied.")
            return redirect(url_for("home"))
    return inner2

def fetch_user_by_username(username, role):
    if role == 'admin':
        user = Admin.query.filter_by(username=username).first()
    elif role == 'doctor':
        user = Doctor.query.filter_by(username=username).first()
    elif role == 'patient':
        user = Patient.query.filter_by(username=username).first()
    return user

def fetch_user_by_id(id, role):
    if role == 'admin':
        user = Admin.query.filter_by(id=id).first()
    elif role == 'doctor':
        user = Doctor.query.filter_by(id=id).first()
    elif role == 'patient':
        user = Patient.query.filter_by(id=id).first()
    return user

def remove_outdated_entities(doctor_id):
    today = datetime.now().date()
    schedules = Doctor_Schedule.query.filter(Doctor_Schedule.doctor_id == doctor_id, Doctor_Schedule.date < today).all()
    for schedule in schedules:
        db.session.delete(schedule)
    appointments = Appointment.query.filter(Appointment.date < today).all()
    for appointment in appointments:
        appointment.status = 'Missed'
    db.session.commit()

def add_new_schedules(doctor_id):
    today = datetime.now().date()
    last_schedule = Doctor_Schedule.query.filter_by(doctor_id = doctor_id).order_by(Doctor_Schedule.date.desc()).first()
    if last_schedule:
        last_date = last_schedule.date
        gap = (last_date - today).days
    
        if gap < 7:
            for i in range(7 - gap):
                date = last_date + timedelta(days = i + 1)
                new_schedule = Doctor_Schedule(doctor_id = doctor_id, date = date, status = True)
                db.session.add(new_schedule)
            db.session.commit()
    else:
        for i in range(8):
            date = today + timedelta(days = i)
            new_schedule = Doctor_Schedule(doctor_id = doctor_id, date = date, status = True)
            db.session.add(new_schedule)
        db.session.commit()

#Routes/Controllers
#common routes
@app.route('/')
def index():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login')
@logout_auth
def login_redirect():
    flash('Please use the login dropdown in the top panel.')
    return render_template('home.html')

@app.route('/logout')
@login_auth
def logout():
    session.pop('user_id')
    session.pop('role')
    session.pop('username')
    return (redirect(url_for('home')))
    
@app.route('/login/<role>', methods=['GET', 'POST'])
@logout_auth
def login(role):
    if role not in ['admin', 'doctor', 'patient']:
        flash ('Please use a valid login link')
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash ('Please fill out all the fields')
            return redirect(url_for('login', role = role))
        
        user = fetch_user_by_username(username, role)

        if not user:
            flash (f'User does not exist')
            return redirect(url_for('login', role = role))
        
        if role == 'doctor' and user.status == 'Inactive':
            flash('Your account has been deactivated. Kindly contact the admin.')
            return redirect(url_for('login', role = role))

        if user and check_password_hash(user.passhash, password):
            session['role'] = role
            session['user_id'] = user.id
            session['username'] = user.username

            if role == 'doctor':
                flash('Kindly update your availability for the coming week.')
            return redirect(url_for(f'{role}_dashboard'))

        flash('Invalid credentials')

    return render_template('login.html', role=role)

@app.route('/dashboard')
@login_auth
def dashboard():
    return redirect(url_for(f'{session['role']}_dashboard'))

@app.route('/profile/<role>/<id>')
@login_auth
def profile(id, role):
    user = fetch_user_by_id(id, role)
    return render_template('profile.html', user = user, role = role)

@app.route('/profile/edit/<role>/<id>', methods = ['GET', 'POST'])
@login_auth
def edit_profile(id, role):
    if request.method == 'GET':
        
        if session['role'] == 'admin' or session['role'] == role:
            user = fetch_user_by_id(id, role)
            if role == 'doctor':
                departments = Department.query.all()
                return render_template('edit_profile.html', user = user, role = role, departments = departments)
            else:    
                return render_template('edit_profile.html', user = user, role = role)
        else:
            flash("Access Denied.")
            return redirect(url_for("home"))
    
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        address = request.form.get('address')
        contact = request.form.get('contact')

        if not username or not name or not address or not contact:
            flash('Please fill out all the details.')
            return redirect(url_for('edit_profile'))
        
        user = fetch_user_by_id(id, role)

        if username != user.username:
            new_username = fetch_user_by_username(username, role)
            if new_username:
                flash('Username already exists.')
                return redirect(url_for('edit_profile', role = role, id = id))
        
        if role == 'doctor':
            department_id = request.form.get('department_id')
            description = request.form.get('description')

            user.department_id = department_id
            user.description = description

        user.username = username
        user.name = name
        user.contact = contact
        user.address = address
        db.session.commit()

        flash("Profile updated successfully.")
        return redirect(url_for('profile', id = user.id, role = role))

@app.route('/search', methods = ['GET'])
@login_auth

def search():
    query = request.args.get('query')
    category = request.args.get('category')

    if category == 'doctor':
        results = Doctor.query.filter(Doctor.name.ilike(f'%{query}%')).all()
        return render_template('doctor/doctors.html', doctors = results)
    elif category == 'patient':
        results = Patient.query.filter(Patient.name.ilike(f'%{query}%')).all()
        return render_template('patient/patients.html', patients = results)
    elif category == 'admin':
        results = Admin.query.filter(Admin.name.ilike(f'%{query}%')).all()
        return render_template('admin/admins.html', admins = results)
    elif category == 'department':
        results = Department.query.filter(Department.name.ilike(f'%{query}%')).all()
        return render_template('department/departments.html', departments = results)

#Department related routes  

@app.route('/department/add', methods = ["GET", "POST"])
@login_auth
@admin_auth
def add_department():
    if request.method == "GET":
        return render_template('department/add_department.html')
    
    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')

        department = Department.query.filter_by(name = name).first()

        if department:
            flash ("This department already exists.")
            return redirect(url_for("add_department"))
        else:
            new_department = Department(name = name, description = description)
            db.session.add(new_department)
            db.session.commit() 

            flash ("Department addedd successfully")
            return redirect(url_for('admin_dashboard'))
        
@app.route('/department/view/<int:id>')
def view_department(id):
    department = Department.query.filter_by(id = id).first()
    if session['role'] == 'patient':
        doctors = Doctor.query.filter_by(department_id = id, status = 'Active').all()
    else:
        doctors = Doctor.query.all()
    return render_template("department/view_department.html", department = department, doctors = doctors)
    
@app.route('/department/edit/<int:id>', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def edit_department(id):
    if request.method == 'GET':
        department = Department.query.filter_by(id = id).first()
        return render_template("department/edit_department.html", department = department)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if not name or not description:
            flash('Please fill out all the details.')
            return redirect(url_for('edit_department', id = id))
        
        department = Department.query.filter_by(id = id).first()

        if name != department.name:
            new_department = Department.query.filter_by(name = name).first()
            if new_department:
                flash('Department name already exists.')
                return redirect(url_for('edit_department', id = id))
        
        department.name = name
        department.description = description
        db.session.commit()

        flash("Department updated successfully.")
        return redirect(url_for('view_department', id = id))

@app.route('/departments', methods = ['GET', 'POST'])
@login_auth
def departments():
    if request.method == 'GET':
        departments = Department.query.all()
        return render_template('department/departments.html', departments = departments)
    
    if request.method == 'POST':
        department_id = request.form.get('department_id')
        if not department_id:
            flash('Please select a department.')
            return redirect(url_for('find_doctors'))
        
        doctors = Doctor.query.filter_by(department_id = department_id, status = 'Active').all()
        department = Department.query.filter_by(id = department_id).first()
        return render_template('department/departments.html', doctors = doctors, department = department)     

@app.route('/department/<int:id>/status_change', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def change_department_status(id):
    if request.method == 'GET':
        department = Department.query.filter_by(id = id).first()
        return render_template("department/department_status.html", department = department)

    if request.method == 'POST':
        department = Department.query.filter_by(id = id).first()
        if department.status == 'Active':
            department.status = 'Inactive'
        else:
            department.status = 'Active'
        doctors = Doctor.query.filter_by(department_id = id).all()
        for doctor in doctors:
            if department.status == 'Inactive':
                doctor.status = 'Inactive'
                appointments = Appointment.query.filter_by(doctor_id = id, status = 'Booked').all()
                for appointment in appointments:
                    appointment.status = 'Cancelled'
            else:
                doctor.status = 'Active'
        db.session.commit()
        flash('Department status changes successfully.')
        return redirect(url_for('admin_dashboard'))

#Doctor related routes

@app.route('/doctor_dashboard')
@login_auth
def doctor_dashboard():
    doctor = fetch_user_by_id(session['user_id'], 'doctor')
    appointments = Appointment.query.filter_by(doctor_id = doctor.id, status = 'Booked').all()
    treated_patients = Patient.query.join(Appointment, Appointment.patient_id == Patient.id).filter(Appointment.doctor_id == doctor.id,Appointment.status == "Completed").distinct().all()
    return render_template('doctor/doctor_dashboard.html', doctor = doctor, appointments = appointments, treated_patients= treated_patients)

@app.route('/<int:id>/doctor/add', methods = ["GET", "POST"])
@login_auth
@admin_auth
def add_doctor(id):
    if request.method == "GET":
        departments = Department.query.all()
        return render_template('doctor/add_doctor.html', departments = departments, id = id)
    
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address')
        contact = request.form.get('contact')
        department_id = request.form.get('department_id')
        description = request.form.get('description')

        doctor = Doctor.query.filter_by(username = username).first()

        if doctor:
            flash ("This Doctor is already registered.")
            return redirect(url_for("add_doctor"))
        else:
            new_doctor = Doctor(username = username, passhash = generate_password_hash(password), name = name, address = address, contact = contact, department_id = department_id, description = description)
            db.session.add(new_doctor)
            db.session.commit()

            doc = fetch_user_by_username(username, 'doctor')
            for i in range(8):
                new_schedule = Doctor_Schedule(doctor_id = doc.id, date = datetime.now().date() + timedelta(days = i), status = True)
                db.session.add(new_schedule)
                db.session.commit()

            flash ("Doctor added successfully")
            return redirect(url_for('admin_dashboard'))
        
@app.route('/doctors', methods = ['GET', 'POST'])
@login_auth
def doctors():
    if request.method == 'GET':
        if session['role'] == 'patient':
            doctors = Doctor.query.filter_by(status ='Active').all()
        else:
            doctors = Doctor.query.all()
        return render_template('doctor/doctors.html', doctors = doctors)


@app.route('/doctor/<int:id>/status_change', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def change_doctor_status(id):
    if request.method == 'GET':
        doctor = Doctor.query.filter_by(id = id).first()
        return render_template("doctor/doctor_status.html", doctor = doctor)

    if request.method == 'POST':
        doctor = Doctor.query.filter_by(id = id).first()
        if doctor.status == 'Active':
            doctor.status = 'Inactive'
            appointments = Appointment.query.filter_by(doctor_id = id, status = 'Booked').all()
            for appointment in appointments:
                appointment.status = 'Cancelled'
        else:
            doctor.status = 'Active'
        db.session.commit()
        flash('Doctor status changed successfully.')
        return redirect(url_for('admin_dashboard'))

@app.route('/doctor_id=<int:id>/availability', methods = ['GET', 'POST'])
@login_auth
def doctor_availability(id):
    if session['role'] == 'patient':
        flash('Access Denied.')
        return redirect(url_for('home'))
                        
    if request.method == 'GET':
        doctor = fetch_user_by_id(id, 'doctor')
        remove_outdated_entities(id)
        add_new_schedules(id)
        schedules = Doctor_Schedule.query.filter_by(doctor_id = id).all()
        return render_template('doctor/availability.html', schedules = schedules, doctor = doctor)
    
    if request.method == 'POST':
        schedules = Doctor_Schedule.query.filter_by(doctor_id = id).all()
        for schedule in schedules:
            slot1_key = f'slot1-{schedule.id}'
            slot2_key = f'slot2-{schedule.id}'
            schedule.slot_1 = slot1_key in request.form
            schedule.slot_2 = slot2_key in request.form
            db.session.commit()
        
        flash('Availability updated successfully.')
        return redirect(url_for('doctor_dashboard'))

#Patient related routes

@app.route('/patients', methods = ['GET', 'POST'])
@login_auth
def patients():
    if request.method == 'GET':
        patients = Patient.query.all()
        return render_template('patient/patients.html', patients = patients)

@app.route('/patient_dashboard')
@login_auth
def patient_dashboard():
    patient = fetch_user_by_id(session['user_id'], 'patient')
    departments = Department.query.filter_by(status = 'Active').order_by(Department.id.asc()).limit(3).all()
    appointments = Appointment.query.filter_by(patient_id = patient.id, status = 'Booked').all()
    return render_template('patient/patient_dashboard.html', patient = patient, appointments = appointments,departments = departments)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        address = request.form.get('address')
        contact = request.form.get('contact')

        if not username or not password or not confirm_password or not name or not address or not contact:
            flash ('Please fill out all the fields')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash ('Passwords do not match')
            return redirect(url_for('register'))
        
        # user = Patient.query.filter_by(username = username).first()
        user = fetch_user_by_username(username, 'patient')

        if user:
            flash ('This username already exists, kindly use a different username')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        new_user = Patient(username = username, passhash=password_hash, name = name, address = address, contact = contact)
        
        db.session.add(new_user)
        db.session.commit()

        flash("Registration complete. Kindly login.")
        return(redirect(url_for('login', role = 'patient')))

@app.route('/patient/history/<int:id>', methods = ['GET', 'POST'])
@login_auth
def treatment_history(id):
    if request.method == 'GET':
        patient = fetch_user_by_id(id, 'patient')
        treatments = Treatment.query.filter_by(patient_id = id).all()
        return render_template('patient/history.html', treatments = treatments, id = id)
    
@app.route('/patient/treatment/add/<appointment_id>', methods = ['GET', 'POST'])
@login_auth
@doc_auth
def add_treatment(appointment_id):
    if request.method == 'GET':
        appointment = Appointment.query.filter_by(id = appointment_id).first()
        patient = fetch_user_by_id(appointment.patient_id, 'patient')
        return render_template('patient/add_treatment.html', patient = patient)
    
    if request.method == 'POST':
        appointment = Appointment.query.filter_by(id = appointment_id).first()

        doctor_id = appointment.doctor_id
        patient_id = appointment.patient_id
        diagnosis = request.form.get('diagnosis')
        treatment = request.form.get('treatment')
        instruction = request.form.get('instruction')

        if not diagnosis or not treatment or not instruction:
            flash('Please fill out all the fields.')
            return redirect(url_for('add_treatment', appointment_id = appointment_id))
        
        appointment.status = 'Completed'

        new_treatment = Treatment(appointment_id = appointment_id, doctor_id = doctor_id, patient_id = patient_id, diagnosis = diagnosis, treatment = treatment, instruction = instruction)
        db.session.add(new_treatment)
        db.session.commit()

        flash('Patient records updated successfully.')
        return redirect(url_for('doctor_dashboard'))
    
@app.route('/patient/treatment/view/treatment_id=<int:id>', methods = ['GET', 'POST'])
@login_auth
def view_treatment(id):
    if request.method == 'GET':
        treatment = Treatment.query.filter_by(id = id).first()
        appointment = Appointment.query.filter_by(id = id).first()
        patient = fetch_user_by_id(appointment.patient_id, 'patient')
        return render_template('patient/view_treatment.html', treatment = treatment, patient = patient, appointment = appointment)
    
@app.route('/patient/<int:id>/status_change', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def change_patient_status(id):
    if request.method == 'GET':
        patient = Patient.query.filter_by(id = id).first()
        return render_template("patient/patient_status.html", patient = patient)

    if request.method == 'POST':
        patient = Patient.query.filter_by(id = id).first()
        if patient.status == 'Active':
            patient.status = 'Inactive'
        else:
            patient.status = 'Active'
        db.session.commit()
        flash("Patient's status changed successfully.")
        return redirect(url_for('admin_dashboard'))

#Admin related routes

@app.route('/admin_dashboard')
@login_auth
@admin_auth
def admin_dashboard():
    departments = Department.query.filter_by(status = 'Active').order_by(Department.id.asc()).limit(3).all()
    doctors = Doctor.query.filter_by(status = 'Active').order_by(Doctor.id.asc()).limit(3).all()
    patients = Patient.query.filter_by(status = 'Active').order_by(Patient.id.asc()).limit(3).all()
    appointments = Appointment.query.filter_by(status = 'Booked').order_by(Appointment.id.asc()).limit(3).all()
    return render_template('admin/admin_dashboard.html', departments = departments, doctors = doctors, patients = patients, appointments = appointments)

@app.route('/admins', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def admins():
    if request.method == 'GET':
        admins = Admin.query.all()
        return render_template('admin/admins.html', admins = admins)

@app.route('/admin/add', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def add_admin():
    if request.method == 'GET':
        return render_template('admin/add_admin.html')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        address = request.form.get('address')
        contact = request.form.get('contact')

        if not username or not password or not confirm_password or not name or not address or not contact:
            flash ('Please fill out all the fields')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash ('Passwords do not match')
            return redirect(url_for('register'))
        
        user = fetch_user_by_username(username, 'admin')

        if user:
            flash ('This username already exists, kindly use a different username')
            return redirect(url_for('add_admin'))

        password_hash = generate_password_hash(password)

        new_admin = Admin(username = username, passhash=password_hash, name = name, address = address, contact = contact)
        
        db.session.add(new_admin)
        db.session.commit()
        flash("Registration complete. Kindly login.")
        return(redirect(url_for('login', role = 'patient')))


@app.route('/admin/<int:id>/status_change', methods = ['GET', 'POST'])
@login_auth
@admin_auth
def change_admin_status(id):
    if request.method == 'GET':
        admin = Admin.query.filter_by(id = id).first()
        return render_template("admin/blacklist_admin.html", admin = admin)

    if request.method == 'POST':
        admin = Admin.query.filter_by(id = id).first()
        if admin.status == 'Active':
            admin.status = 'Inactive'
        else:
            admin.status = 'Active'
        db.session.commit()
        flash('Admin status changed successfully.')
        return redirect(url_for('admin_dashboard'))



#Appointment related routes

@app.route('/appointment/book/<doctor_id>', methods = ['GET', 'POST'])
@login_auth
def book_appointment(doctor_id):
    if request.method == 'GET':
        doctor = fetch_user_by_id(doctor_id, 'doctor')
        remove_outdated_entities(doctor_id)
        schedules = Doctor_Schedule.query.filter_by(doctor_id = doctor.id).all()
        return render_template('appointment/book_appointment.html', doctor = doctor, schedules = schedules)

    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        if not patient_id:
            flash('Please provide the Patient ID.')
            return redirect(url_for('book_appointment', doctor_id = doctor_id))

        selected_slot = request.form.get('selected_slot')
        if not selected_slot:
            schedules = Doctor_Schedule.query.filter_by(doctor_id = doctor_id).all()
            flash('Please select a slot from the available options.')
            return redirect(url_for('book_appointment', doctor_id = doctor_id, schedules = schedules))
        
        slot_id = int(selected_slot.split('_')[0])
        slot_number = int(selected_slot.split('_')[1])

        visit_type = request.form.get('visit_type')
        if not visit_type:
            schedules = Doctor_Schedule.query.filter_by(doctor_id = doctor_id).all()
            flash('Please select a visit type.')
            return redirect(url_for('book_appointment', doctor_id = doctor_id, schedules = schedules))

        schedule = Doctor_Schedule.query.filter_by(id = slot_id).first()

        if slot_number == 1:
            if schedule.slot_1 == False:
                schedules = Doctor_Schedule.query.filter_by(doctor_id = doctor_id).all()
                flash('Selected slot is no longer available. Please choose a different slot.')
                return redirect(url_for('book_appointment', doctor_id = doctor_id, schedules = schedules))
            else:
                schedule.slot_1 = False
        elif slot_number == 2:
            if schedule.slot_2 == False:
                schedules = Doctor_Schedule.query.filter_by(doctor_id = doctor_id).all()
                flash('Selected slot is no longer available. Please choose a different slot.')
                return redirect(url_for('book_appointment', doctor_id = doctor_id, schedules = schedules))
            else:
                schedule.slot_2 = False

        appointment_date = schedule.date
        status = 'Booked'
        new_appointment = Appointment(patient_id = patient_id, doctor_id = doctor_id, visit_type = visit_type, date = appointment_date, slot = slot_number, status = status)
        db.session.add(new_appointment)
        db.session.commit()

        flash('Appointment booked successfully.')
        return redirect(url_for('patient_dashboard'))

@app.route('/appointment/reschedule/<int:id>', methods = ['GET', 'POST'])
@login_auth
def reschedule_appointment(id):
    if request.method == 'GET':
        appointment = Appointment.query.filter_by(id = id).first()
        if appointment.status == 'Booked':
            schedules = Doctor_Schedule.query.filter_by(doctor_id = appointment.doctor.id).all()
            return render_template('appointment/reschedule_appointment.html', appointment = appointment, schedules = schedules)
        else:
            flash("That appointment is cancelled. Kindly book another appointment.")
            return redirect(url_for('patient_dashboard'))

    if request.method == 'POST':
        appointment = Appointment.query.filter_by(id = id).first()
        selected_slot = request.form.get('selected_slot')
        if not selected_slot:
            schedules = Doctor_Schedule.query.filter_by(doctor_id = appointment.doctor.id).all()
            flash('Please select a slot from the available options.')
            return redirect(url_for('reschedule_appointment', id = id))
        
        slot_id = int(selected_slot.split('_')[0])
        slot_number = int(selected_slot.split('_')[1])

        schedule = Doctor_Schedule.query.filter_by(id = slot_id).first()
        if slot_number == 1:
            schedule.slot_1 = False
        elif slot_number == 2:
            schedule.slot_2 = False

        old_schedule = Doctor_Schedule.query.filter_by(doctor_id = appointment.doctor.id, date = appointment.date)
        if old_schedule:
            if appointment.slot == 1: 
                schedule.slot_1 == True 
            elif appointment.slot == 2: 
                schedule.slot_2 = True
        else:
            pass

        appointment.date = schedule.date
        appointment.status = 'Booked'
        appointment.slot = slot_number

        db.session.commit()
        flash('Appointment rescheduled successfully.')
        return redirect(url_for('patient_dashboard'))

@app.route('/appointment/cancel/<int:id>')
@login_auth
def cancel_appointment(id):
    appointment = Appointment.query.filter_by(id = id).first()
    appointment.status = 'Cancelled'
    db.session.commit()

    flash('Appointment cancelled successfully.')
    return redirect(url_for(f'{session['role']}_dashboard'))


@app.route('/<role>/<int:id>/appointments', methods = ['GET', 'POST'])
@login_auth
def appointments(role, id):
    if request.method == 'GET':
        str_date = request.args.get('date')
        if not str_date:
            if role == 'doctor':
                appointments = Appointment.query.filter_by(doctor_id = id).all()
            elif role == 'patient':
                appointments = Appointment.query.filter_by(patient_id = id).all()
            elif role == 'admin':
                appointments = Appointment.query.all()
            return render_template('appointment/appointments.html', appointments = appointments, role = role, id = id)
        
        if str_date:
            date = datetime.strptime(str_date, "%Y-%m-%d").date()
            if role == 'doctor':
                appointments = Appointment.query.filter_by(doctor_id = id, date = date).all()
            elif role == 'patient':
                appointments = Appointment.query.filter_by(patient_id = id, date = date).all()
            elif role == 'admin':
                appointments = Appointment.query.filter_by(date = date).all()
            return render_template('appointment/appointments.html', appointments = appointments, role = role, id = id)
