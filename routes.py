from flask import render_template, request, url_for, session, flash, redirect
from models import (db, Admin, Department, Doctor, Patient, Appointment, Treatment, Doctor_Schedule)
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from functools import wraps
from datetime import datetime

def login_auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        flash('Kindly login to continue.')
        return redirect(url_for('home'))
    return inner

def logout_auth(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            return func(*args, **kwargs)
        flash('You are already logged in.')
        return redirect(url_for('home'))
    return inner

def admin_auth(func):
    @wraps(func)
    def inner2(*args, **kwargs):
        if session.get('role') == 'admin':
            return func(*args, **kwargs)
        flash('Access Denied.')
        return redirect(url_for('home'))
    return inner2

def doc_auth(func):
    @wraps(func)
    def inner2(*args, **kwargs):
        if session.get('role') == 'doctor':
            return func(*args, **kwargs)
        flash('Access Denied.')
        return redirect(url_for('home'))
    return inner2

def fetch_user_by_username(username, role):
    if role == 'admin':
        return Admin.query.filter_by(username=username).first()
    elif role == 'doctor':
        return Doctor.query.filter_by(username=username).first()
    elif role == 'patient':
        return Patient.query.filter_by(username=username).first()
    return None

def fetch_user_by_id(id, role):
    if role == 'admin':
        return Admin.query.filter_by(id=id).first()
    elif role == 'doctor':
        return Doctor.query.filter_by(id=id).first()
    elif role == 'patient':
        return Patient.query.filter_by(id=id).first()
    return None

def get_schedule_slot_name(slot_number):
    if 1 <= slot_number <= 20:
        return f'slot_{slot_number}'
    raise ValueError('Invalid slot number')

def get_slot_display_name(slot_number):
    if 1 <= slot_number <= 12:
        return f'Slot {slot_number}A'
    elif 13 <= slot_number <= 20:
        evening_slot = slot_number - 12
        return f'Slot {evening_slot}B'
    raise ValueError('Invalid slot number')

def get_slot_datetime(selected_date, slot_number):
    if 1 <= slot_number <= 12:
        slot_index = slot_number - 1
        slot_hour = 8 + (slot_index // 2)
        slot_minute = 30 if slot_index % 2 else 0

        return datetime.combine(selected_date, datetime.min.time()).replace(hour=slot_hour, minute=slot_minute)

    elif 13 <= slot_number <= 20:
        slot_index = slot_number - 13
        slot_hour = 16 + (slot_index // 2)
        slot_minute = 30 if slot_index % 2 else 0

        return datetime.combine(selected_date, datetime.min.time()).replace(hour=slot_hour, minute=slot_minute)

    raise ValueError('Invalid slot number')

def is_valid_slot(slot_number):
    return 1 <= slot_number <= 20

def remove_outdated_entities(doctor_id):
    today = datetime.now().date()
    schedules = Doctor_Schedule.query.filter(
        Doctor_Schedule.doctor_id == doctor_id,
        Doctor_Schedule.date < today
    ).all()
    for schedule in schedules:
        db.session.delete(schedule)
    appointments=Appointment.query.filter(Appointment.date < today, Appointment.status=='Booked').all()
    for appointment in appointments:
        appointment.status = 'Missed'
    db.session.commit()

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login/<role>', methods=['GET', 'POST'])
@logout_auth
def login(role):
    if request.method == 'GET':
        return render_template('login.html', role=role)
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        flash('Please fill out all the fields.')
        return redirect(url_for('login', role=role))

    user = fetch_user_by_username(username, role)

    if not user:
        flash('Invalid credentials.')
        return redirect(url_for('login', role=role))

    if user.status != 'Active':
        flash('You are not active, please contact admin')
        return redirect(url_for('login', role=role))

    if role == 'doctor':
        department = Department.query.filter_by(id=user.department_id).first()
        if not department or department.status != 'Active':
            flash('This department is inactive')
            return redirect(url_for('login', role=role))

    if not check_password_hash(user.passhash, password):
        flash('Invalid credentials.')
        return redirect(url_for('login', role=role))

    session['user_id'] = user.id
    session['role'] = role
    flash('Login successful.')
    return redirect(url_for(f'{role}_dashboard'))


@app.route('/logout')
@login_auth
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('home'))


@app.route('/profile/<role>/<id>')
@login_auth
def profile(id, role):
    if session.get('role') != 'admin' and session.get('role') != role:
        flash('Access Denied.')
        return redirect(url_for(f"{session['role']}_dashboard"))
    user = fetch_user_by_id(id, role)
    if not user:
        flash('User not found.')
        return redirect(url_for('home'))
    return render_template('profile.html', user=user, role=role)


@app.route('/profile/edit/<role>/<id>',methods=['GET', 'POST'])
@login_auth
def edit_profile(id, role):
    if request.method == 'GET':
        if (session.get('role') == 'admin' or (session.get('role') == role and session.get('user_id') == int(id))):
            user = fetch_user_by_id(id,role)
            if not user:
                flash('User not found.')
                return redirect(url_for('home'))
            if role == 'doctor':
                departments = Department.query.all()
                return render_template('edit_profile.html',user=user, role=role, departments=departments)
            return render_template('edit_profile.html', user=user, role=role)
        flash('Access Denied.')
        return redirect(url_for('home'))

    if session.get('role') != 'admin' and (session.get('role') != role or session.get('user_id') != int(id)):
        flash('Access Denied.')
        return redirect(url_for(f"{session['role']}_dashboard"))

    user = fetch_user_by_id(id,role)

    if not user:
        flash('User not found.')
        return redirect(url_for('home'))

    username = request.form.get('username')
    name = request.form.get('name')
    address = request.form.get('address')
    contact = request.form.get('contact')
    previous_password = request.form.get('previous_password')
    new_password = request.form.get('new_password')
    confirm_new_password = request.form.get('confirm_new_password')

    if not username:
        username = user.username
    if not name or not address or not contact:
        flash('Please fill out all the details.')
        return redirect(url_for('edit_profile', id=id, role=role))
    if username != user.username:
        new_username = fetch_user_by_username(username, role)
        if new_username:
            flash('Username already exists.')
            return redirect(url_for('edit_profile', id=id, role=role))
    if previous_password or new_password or confirm_new_password:
        if not previous_password or not new_password or not confirm_new_password:
            flash('Please fill out all password fields.')
            return redirect(url_for('edit_profile', id=id, role=role))
        if not check_password_hash(user.passhash, previous_password):
            flash('Previous password is incorrect.')
            return redirect(url_for('edit_profile', id=id, role=role))
        if new_password != confirm_new_password:
            flash('New passwords do not match.')
            return redirect(url_for('edit_profile', id=id, role=role))
        user.passhash = generate_password_hash(new_password)
    if role == 'doctor':
        department_id = request.form.get('department_id')
        description = request.form.get('description')
        if department_id:
            user.department_id = department_id
        if description:
            user.description = description
    user.username = username
    user.name = name
    user.address = address
    user.contact = contact
    db.session.commit()
    flash('Profile updated successfully.')

    return redirect(url_for('profile', id=user.id, role=role))


@app.route('/search', methods=['GET'])
@login_auth
def search():
    query = request.args.get('query')
    category = request.args.get('category')
    if category == 'doctor':
        if session.get('role') == 'patient':
            results = Doctor.query.join(
                Department,
                Doctor.department_id == Department.id
            ).filter(
                Doctor.name.ilike(f'%{query}%'),
                Doctor.status == 'Active',
                Department.status == 'Active'
            ).all()
        else:
            results = Doctor.query.filter(Doctor.name.ilike(f'%{query}%')).all()
        return render_template('doctor/doctors.html', doctors=results)
    elif category == 'patient':
        results = Patient.query.filter(Patient.name.ilike(f'%{query}%')).all()
        return render_template('patient/patients.html', patients=results)
    elif category == 'admin':
        results = Admin.query.filter(Admin.name.ilike(f'%{query}%')).all()
        return render_template('admin/admins.html', admins=results)
    elif category == 'department':
        if session.get('role') == 'patient':
            results = Department.query.filter(
                Department.name.ilike(f'%{query}%'),
                Department.status == 'Active'
            ).all()
        else:
            results = Department.query.filter(Department.name.ilike(f'%{query}%')).all()

        return render_template('department/departments.html',departments=results)


@app.route('/department/add', methods=['GET', 'POST'])
@login_auth
@admin_auth
def add_department():
    if request.method == 'GET':
        return render_template('department/add_department.html')
    name = request.form.get('name')
    description = request.form.get('description')
    department = Department.query.filter_by(name=name).first()
    if department:
        flash('This department already exists.')
        return redirect(url_for('add_department'))

    new_department = Department(name=name,description=description)
    db.session.add(new_department)
    db.session.commit()
    flash('Department added successfully.')

    return redirect(url_for('admin_dashboard'))


@app.route('/department/view/<int:id>')
@login_auth
def view_department(id):
    department = Department.query.filter_by(id=id).first()
    if not department:
        flash('Department not found.')
        return redirect(url_for('departments'))
    if session.get('role') == 'patient':
        if department.status != 'Active':
            flash('This department is inactive')
            return redirect(url_for('departments'))
        doctors = Doctor.query.filter_by(department_id=id,status='Active').all()
    else:
        doctors = Doctor.query.filter_by( department_id=id).all()
    return render_template('department/view_department.html',department=department,doctors=doctors)


@app.route('/department/edit/<int:id>', methods=['GET', 'POST'])
@login_auth
@admin_auth
def edit_department(id):
    department=Department.query.filter_by(id=id).first()
    if not department:
        flash('Department not found.')
        return redirect(url_for('departments'))

    if request.method == 'GET':
        return render_template('department/edit_department.html', department=department)

    name=request.form.get('name')
    description=request.form.get('description')
    if not name or not description:
        flash('Please fill out all the details.')
        return redirect(url_for('edit_department', id=id))

    if name != department.name:
        existing_department=Department.query.filter_by(name=name).first()
        if existing_department:
            flash('Department name already exists.')
            return redirect(url_for('edit_department', id=id))

    department.name = name
    department.description = description
    db.session.commit()
    flash('Department updated successfully.')
    return redirect(url_for('view_department', id=id))


@app.route('/departments', methods=['GET', 'POST'])
@login_auth
def departments():
    if request.method == 'GET':
        if session.get('role') == 'patient':
            departments = Department.query.filter_by(status='Active').all()
        else:
            departments = Department.query.all()
        return render_template('department/departments.html', departments=departments)

    department_id=request.form.get('department_id')

    if not department_id:
        flash('Please select a department.')
        return redirect(url_for('departments'))
    department=Department.query.filter_by(id=department_id).first()
    if not department:
        flash('Department not found.')
        return redirect(url_for('departments'))
    if session.get('role') == 'patient' and department.status != 'Active':
        flash('This department is inactive')
        return redirect(url_for('departments'))
    if session.get('role') == 'patient':
        doctors=Doctor.query.filter_by(department_id=department_id, status='Active').all()
    else:
        doctors=Doctor.query.filter_by(department_id=department_id, status='Active').all()
    return render_template('department/departments.html', doctors=doctors, department=department)


@app.route('/department/<int:id>/status_change', methods=['GET', 'POST'])
@login_auth
@admin_auth
def change_department_status(id):
    department=Department.query.filter_by(id=id).first()
    if not department:
        flash('Department not found.')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'GET':
        return render_template('department/department_status.html', department=department)

    if department.status == 'Active':
        department.status = 'Inactive'
    else:
        department.status = 'Active'
    db.session.commit()
    flash('Department status changed successfully.')
    return redirect(url_for('admin_dashboard'))


@app.route('/doctor_dashboard')
@login_auth
def doctor_dashboard():
    doctor=fetch_user_by_id(session['user_id'], 'doctor')
    if not doctor:
        flash('Doctor not found.')
        return redirect(url_for('home'))

    today = datetime.now().date()

    appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'Booked',
        Appointment.date >= today
    ).order_by(
        Appointment.date.asc(),
        Appointment.slot.asc()
    ).all()
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'Booked',
        Appointment.date == today
    ).count()
    completed_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'Completed'
    ).count()
    treated_patients = Patient.query.join(
        Appointment,
        Appointment.patient_id == Patient.id
    ).filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == 'Completed'
    ).distinct().all()
    return render_template(
        'doctor/doctor_dashboard.html',
        doctor=doctor,
        appointments=appointments,
        treated_patients=treated_patients,
        today_appointments=today_appointments,
        completed_appointments=completed_appointments
    )

@app.route('/<int:id>/doctor/add', methods=['GET', 'POST'])
@login_auth
@admin_auth
def add_doctor(id):
    if request.method == 'GET':
        departments = Department.query.all()
        return render_template('doctor/add_doctor.html', departments=departments, id=id)

    username=request.form.get('username')
    password=request.form.get('password')
    name=request.form.get('name')
    address=request.form.get('address')
    contact=request.form.get('contact')
    department_id=request.form.get('department_id')
    description=request.form.get('description')
    doctor=Doctor.query.filter_by(username=username).first()

    if doctor:
        flash('This Doctor is already registered.')
        return redirect(url_for('add_doctor', id=id))

    new_doctor = Doctor( username=username, passhash=generate_password_hash(password),  name=name, address=address, contact=contact, department_id=department_id, description=description)
    db.session.add(new_doctor)
    db.session.commit()
    flash('Doctor added successfully.')
    return redirect(url_for('admin_dashboard'))


@app.route('/doctors', methods=['GET', 'POST'])
@login_auth
def doctors():
    if request.method == 'GET':
        if session.get('role') == 'patient':
            doctors=Doctor.query.join(
                Department,
                Doctor.department_id == Department.id
            ).filter(
                Doctor.status == 'Active',
                Department.status == 'Active'
            ).all()
        else:
            doctors = Doctor.query.all()
        return render_template('doctor/doctors.html', doctors=doctors)


@app.route('/doctor/<int:id>/status_change', methods=['GET', 'POST'])
@login_auth
@admin_auth
def change_doctor_status(id):
    doctor=Doctor.query.filter_by(id=id).first()
    if not doctor:
        flash('Doctor not found.')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'GET':
        return render_template('doctor/doctor_status.html', doctor=doctor)

    if doctor.status == 'Active':
        doctor.status = 'Inactive'
        appointments=Appointment.query.filter_by(doctor_id=id, status='Booked').all()
        for appointment in appointments:
            appointment.status = 'Cancelled'
    else:
        doctor.status = 'Active'
    db.session.commit()
    flash('Doctor status changed successfully.')
    return redirect(url_for('admin_dashboard'))


@app.route('/doctor_id=<int:id>/availability', methods=['GET', 'POST'])
@login_auth
def doctor_availability(id):
    if session.get('role') not in ['doctor','admin']:
        flash('Access Denied.')
        return redirect(url_for('home'))
    if session.get('role') == 'doctor' and session.get('user_id') != id:
        flash('Access Denied.')
        return redirect(url_for('doctor_dashboard'))
    doctor=fetch_user_by_id(id, 'doctor')
    if not doctor:
        flash('Doctor not found.')
        return redirect(url_for('home'))

    today = datetime.now().date()
    if request.method == 'GET':
        remove_outdated_entities(id)
        schedules = Doctor_Schedule.query.filter(
            Doctor_Schedule.doctor_id == id,
            Doctor_Schedule.date >= today,
            Doctor_Schedule.status == True
        ).order_by(Doctor_Schedule.date.asc()).all()
        return render_template('doctor/availability.html', schedules=schedules, doctor=doctor)

    if session.get('role') == 'admin':
        flash('Admin can only view doctor availability.')
        return redirect(url_for('doctor_availability', id=id))

    selected_date=request.form.get('available_date')
    if not selected_date:
        flash('Please select an availability date.')
        return redirect(url_for('doctor_availability', id=id))

    try:
        selected_date=datetime.strptime(selected_date, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date selected.')
        return redirect(url_for('doctor_availability', id=id))

    if selected_date < today:
        flash('You cannot set availability for a past date.')
        return redirect(url_for('doctor_availability', id=id))

    schedule=Doctor_Schedule.query.filter_by(doctor_id=id, date=selected_date).first()

    if not schedule:
        schedule=Doctor_Schedule(doctor_id=id, date=selected_date, status=True)
        db.session.add(schedule)
        db.session.flush()
    for slot_number in range(1, 21):
        slot_name=get_schedule_slot_name(slot_number)
        booked_appointment = Appointment.query.filter_by(doctor_id=id, date=selected_date, slot=slot_number, status='Booked').first()
        if booked_appointment:
            setattr(schedule, slot_name, False)
            continue
        setattr(schedule, slot_name, slot_name in request.form)
    schedule.status = True
    db.session.commit()
    flash(f'Availability updated successfully for ' f'{selected_date.strftime("%d %B %Y")}.')

    return redirect(url_for('doctor_availability', id=id))


@app.route('/patient_dashboard')
@login_auth
def patient_dashboard():
    patient=fetch_user_by_id(session['user_id'], 'patient')
    if not patient:
        flash('Patient not found.')
        return redirect(url_for('home'))

    departments=Department.query.filter_by(status='Active').order_by(Department.id.asc()).limit(3).all()
    total_departments=Department.query.filter_by(status='Active').count()
    appointments = Appointment.query.filter_by(
        patient_id=patient.id,
        status='Booked'
    ).order_by(
        Appointment.date.asc(),
        Appointment.slot.asc()).all()

    return render_template('patient/patient_dashboard.html', patient=patient, appointments=appointments, departments=departments, total_departments=total_departments)


@app.route('/patients', methods=['GET', 'POST'])
@login_auth
def patients():
    if request.method == 'GET':
        patients = Patient.query.all()
        return render_template('patient/patients.html', patients=patients)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    username=request.form.get('username')
    password=request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    name=request.form.get('name')
    address=request.form.get('address')
    contact=request.form.get('contact')

    if (not username or not password or not confirm_password or not name or not address or not contact):
        flash('Please fill out all the fields.')
        return redirect(url_for('register'))

    if password != confirm_password:
        flash('Passwords do not match.')
        return redirect(url_for('register'))
    
    user=fetch_user_by_username(username, 'patient')
    if user:
        flash('This username already exists, kindly use a different username.')
        return redirect(url_for('register'))

    new_user = Patient( username=username, passhash=generate_password_hash(password),  name=name, address=address, contact=contact)
    db.session.add(new_user)
    db.session.commit()
    flash('Registration complete. Kindly login.')
    return redirect(url_for('login', role='patient'))


@app.route('/patient/history/<int:id>', methods=['GET', 'POST'])
@login_auth
def treatment_history(id):
    if session.get('role') == 'patient' and session.get('user_id') != id:
        flash('Access Denied.')
        return redirect(url_for('patient_dashboard'))
    patient=fetch_user_by_id(id, 'patient')
    if not patient:
        flash('Patient not found.')
        return redirect(url_for('home'))

    treatments=Treatment.query.filter_by(patient_id=id).all()
    return render_template('patient/history.html', treatments=treatments, id=id)


@app.route('/patient/treatment/add/<appointment_id>', methods=['GET', 'POST'])
@login_auth
@doc_auth
def add_treatment(appointment_id):
    appointment=Appointment.query.filter_by(id=appointment_id).first()
    if not appointment:
        flash('Appointment not found.')

        return redirect(url_for('doctor_dashboard'))

    if appointment.doctor_id != session.get('user_id'):
        flash('You can only diagnose your own appointments.')

        return redirect(url_for('doctor_dashboard'))

    if request.method == 'GET':
        patient=fetch_user_by_id(appointment.patient_id, 'patient')

        return render_template('patient/add_treatment.html', patient=patient)

    diagnosis=request.form.get('diagnosis')
    treatment=request.form.get('treatment')
    instruction=request.form.get('instruction')

    if (not diagnosis or not treatment or not instruction):
        flash('Please fill out all the fields.')
        return redirect(url_for('add_treatment', appointment_id=appointment_id))

    appointment.status = 'Completed'
    new_treatment = Treatment( appointment_id=appointment_id, doctor_id=appointment.doctor_id, patient_id=appointment.patient_id, diagnosis=diagnosis, treatment=treatment, instruction=instruction)
    db.session.add(new_treatment)
    db.session.commit()
    flash('Patient records updated successfully.')

    return redirect(url_for('doctor_dashboard'))


@app.route('/patient/treatment/view/treatment_id=<int:id>', methods=['GET', 'POST'])
@login_auth
def view_treatment(id):
    treatment=Treatment.query.filter_by(id=id).first()
    if not treatment:
        flash('Treatment not found.')
        return redirect(url_for('home'))
    if session.get('role') == 'patient' and treatment.patient_id != session.get('user_id'):
        flash('Access Denied.')
        return redirect(url_for('patient_dashboard'))
    if not treatment:
        flash('Treatment record not found.')
        return redirect(url_for('patient_dashboard'))
    appointment=Appointment.query.filter_by(id=treatment.appointment_id).first()
    patient=fetch_user_by_id(treatment.patient_id, 'patient')

    return render_template('patient/view_treatment.html',treatment=treatment,patient=patient,appointment=appointment)


@app.route('/patient/<int:id>/status_change', methods=['GET', 'POST'])
@login_auth
@admin_auth
def change_patient_status(id):
    patient=Patient.query.filter_by(id=id).first()
    if not patient:
        flash('Patient not found.')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'GET':
        return render_template('patient/patient_status.html', patient=patient)
    if patient.status == 'Active':
        patient.status = 'Inactive'
    else:
        patient.status = 'Active'
    db.session.commit()
    flash("Patient's status changed successfully.")

    return redirect(url_for('admin_dashboard'))

@app.route('/appointment/book/<doctor_id>', methods=['GET', 'POST'])
@login_auth
def book_appointment(doctor_id):
    if session.get('role') != 'patient':
        flash('Only patients can book appointments.')
        return redirect(url_for(f"{session['role']}_dashboard"))
    today = datetime.now().date()
    now = datetime.now()

    if request.method == 'GET':
        doctor=fetch_user_by_id(doctor_id, 'doctor')
        if not doctor:
            flash('Doctor not found.')
            return redirect(url_for('doctors'))
        department=Department.query.filter_by(id=doctor.department_id).first()
        if doctor.status != 'Active':
            flash('You are not active, please contact admin')
            return redirect(url_for('doctors'))
        if not department or department.status != 'Active':
            flash('This department is inactive')
            return redirect(url_for('doctors'))
        remove_outdated_entities(doctor.id)

        schedules = Doctor_Schedule.query.filter(
            Doctor_Schedule.doctor_id == doctor.id,
            Doctor_Schedule.date >= today,
            Doctor_Schedule.status == True
        ).order_by(
            Doctor_Schedule.date.asc()).all()
        return render_template('appointment/book_appointment.html', doctor=doctor, schedules=schedules)

    patient_id = session.get('user_id')
    if not patient_id:
        flash('Patient session not found. Please login again.')
        return redirect(url_for('login', role='patient'))
    
    doctor=fetch_user_by_id(doctor_id, 'doctor')
    if not doctor:
        flash('Doctor not found.')
        return redirect(url_for('doctors'))
    
    department=Department.query.filter_by(id=doctor.department_id).first()
    if doctor.status != 'Active':
        flash('You are not active, please contact admin')
        return redirect(url_for('doctors'))
    if not department or department.status != 'Active':
        flash('This department is inactive')
        return redirect(url_for('doctors'))

    selected_slot=request.form.get('selected_slot')
    if not selected_slot:
        flash('Please select an available slot.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    try:
        slot_id, slot_number=map(int, selected_slot.split('_'))
    except (ValueError, AttributeError):
        flash('Invalid slot selected.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))
    
    if not is_valid_slot(slot_number):
        flash('Invalid slot selected.')
        
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    visit_type=request.form.get('visit_type')
    if not visit_type:
        flash('Please select a visit type.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    schedule=Doctor_Schedule.query.filter_by(id=slot_id, doctor_id=doctor.id).first()
    if not schedule:
        flash('Selected date is no longer available.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    if schedule.date < today:
        flash('You cannot book an appointment for a past date.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    slot_datetime=get_slot_datetime(schedule.date, slot_number)
    if (schedule.date==today and slot_datetime <=now):
        flash('This time slot has already passed. ' 'Please select another slot.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    slot_name=get_schedule_slot_name(slot_number)
    is_available=getattr(schedule, slot_name, False)

    if not is_available:
        flash('Selected slot is no longer available. ' 'Please choose another slot.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))

    existing_appointment = Appointment.query.filter_by(doctor_id=doctor.id, date=schedule.date,slot=slot_number).first()

    if existing_appointment:
        if existing_appointment.status == 'Booked':
            flash('This slot has already been booked. ' 'Please choose another slot.')
            return redirect(url_for('book_appointment', doctor_id=doctor_id))

        elif existing_appointment.status == 'Cancelled':
            existing_appointment.patient_id = patient_id
            existing_appointment.visit_type = visit_type
            existing_appointment.status = 'Booked'
            setattr(schedule, slot_name, False)
            db.session.commit()
            flash('Appointment booked successfully.')
            return redirect(url_for('patient_dashboard'))

    new_appointment = Appointment( patient_id=patient_id, doctor_id=doctor.id, visit_type=visit_type, date=schedule.date, slot=slot_number, status='Booked')
    setattr(schedule, slot_name, False)
    db.session.add(new_appointment)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Unable to book the selected slot. ' 'Please try again.')
        return redirect(url_for('book_appointment', doctor_id=doctor_id))
    flash('Appointment booked successfully.')
    return redirect(url_for('patient_dashboard'))


@app.route('/appointment/reschedule/<int:id>', methods=['GET', 'POST'])
@login_auth
def reschedule_appointment(id):
    role = session.get('role')
    if role not in ['patient','doctor','admin']:
        flash('Access Denied.')
        return redirect(url_for('home'))
    appointment=Appointment.query.filter_by(id=id).first()
    if not appointment:
        flash('Appointment not found.')
        return redirect(url_for(f'{role}_dashboard'))

    if role == 'patient':
        if appointment.patient_id != session.get('user_id'):
            flash('You can only reschedule your own appointments.')
            return redirect(url_for('patient_dashboard'))

    elif role == 'doctor':
        if appointment.doctor_id != session.get('user_id'):
            flash('You can only reschedule your own appointments.')
            return redirect(url_for('doctor_dashboard'))

    doctor=Doctor.query.filter_by(id=appointment.doctor_id).first()
    department=Department.query.filter_by(id=doctor.department_id).first() if doctor else None
    if role == 'patient':
        if not doctor or doctor.status != 'Active':
            flash('This doctor is not active.')
            return redirect(url_for('patient_dashboard'))
        if not department or department.status != 'Active':
            flash('This department is inactive')
            return redirect(url_for('patient_dashboard'))

    today = datetime.now().date()
    now = datetime.now()

    if request.method == 'GET':
        if appointment.status != 'Booked':
            flash('That appointment is not currently booked.')
            return redirect(url_for(f'{role}_dashboard'))
        remove_outdated_entities(appointment.doctor_id)
        schedules = Doctor_Schedule.query.filter(
            Doctor_Schedule.doctor_id == appointment.doctor_id,
            Doctor_Schedule.date >= today,
            Doctor_Schedule.status == True
        ).order_by(
            Doctor_Schedule.date.asc()
        ).all()
        return render_template('appointment/reschedule_appointment.html', appointment=appointment, schedules=schedules)
    
    selected_slot=request.form.get('selected_slot')
    if not selected_slot:
        flash('Please select a slot from the available options.')
        return redirect(url_for('reschedule_appointment', id=id))
    try:
        slot_id, slot_number=map(int, selected_slot.split('_'))
    except (ValueError, AttributeError):
        flash('Invalid slot selected.')
        return redirect(url_for('reschedule_appointment', id=id))

    if not is_valid_slot(slot_number):
        flash('Invalid slot selected.')
        return redirect(url_for('reschedule_appointment', id=id))

    new_schedule=Doctor_Schedule.query.filter_by(id=slot_id, doctor_id=appointment.doctor_id).first()
    if not new_schedule:
        flash('Selected date is no longer available.')
        return redirect(url_for('reschedule_appointment', id=id))

    if new_schedule.date < today:
        flash('You cannot reschedule to a past date.')
        return redirect(url_for('reschedule_appointment', id=id))

    new_slot_datetime=get_slot_datetime(new_schedule.date, slot_number)
    if (new_schedule.date==today and new_slot_datetime <=now):
        flash('This time slot has already passed. ' 'Please select another slot.')
        return redirect(url_for('reschedule_appointment', id=id))

    slot_name=get_schedule_slot_name(slot_number)
    if not getattr(new_schedule, slot_name, False):
        flash('Selected slot is no longer available.')
        return redirect(url_for('reschedule_appointment', id=id))

    if (appointment.date==new_schedule.date and appointment.slot==slot_number):
        flash('You are already booked for this slot.')
        return redirect(url_for('reschedule_appointment', id=id))

    existing_appointment = Appointment.query.filter_by(
        doctor_id=appointment.doctor_id,
        date=new_schedule.date,
        slot=slot_number,
        status='Booked'
    ).filter(
        Appointment.id != appointment.id
    ).first()

    if existing_appointment:
        flash('Selected slot has already been booked.')
        return redirect(url_for('reschedule_appointment', id=id))

    old_schedule = Doctor_Schedule.query.filter_by(doctor_id=appointment.doctor_id,date=appointment.date).first()
    if old_schedule:
        old_slot_name=get_schedule_slot_name(appointment.slot)
        setattr(old_schedule, old_slot_name, True)
    setattr(new_schedule, slot_name, False)
    appointment.date = new_schedule.date
    appointment.slot = slot_number
    appointment.status = 'Booked'
    db.session.commit()
    flash('Appointment rescheduled successfully.')

    return redirect(url_for(f'{role}_dashboard'))


@app.route('/appointment/cancel/<int:id>')
@login_auth
def cancel_appointment(id):
    role = session.get('role')
    if role not in [ 'patient', 'doctor', 'admin']:
        flash('Access Denied.')
        return redirect(url_for('home'))
    
    appointment=Appointment.query.filter_by(id=id).first()

    if not appointment:
        flash('Appointment not found.')
        return redirect(url_for(f'{role}_dashboard'))

    if role == 'patient':
        if appointment.patient_id != session.get('user_id'):
            flash('You can only cancel your own appointments.')
            return redirect(url_for('patient_dashboard'))
        
    elif role == 'doctor':
        if appointment.doctor_id != session.get('user_id'):
            flash('You can only cancel your own appointments.')
            return redirect(url_for('doctor_dashboard'))

    if appointment.status != 'Booked':
        flash('This appointment cannot be cancelled.')
        return redirect(url_for(f'{role}_dashboard'))

    schedule=Doctor_Schedule.query.filter_by(doctor_id=appointment.doctor_id, date=appointment.date).first()
    if schedule:
        slot_name=get_schedule_slot_name(appointment.slot)
        setattr(schedule, slot_name, True)
    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled successfully.')

    return redirect(url_for(f'{role}_dashboard'))


@app.route('/<role>/<int:id>/appointments', methods=['GET', 'POST'])
@login_auth
def appointments(role, id):
    if role not in ['patient','doctor','admin']:
        flash('Invalid role.')
        return redirect(url_for('home'))
    if role != 'admin' and (session.get('role') != role or session.get('user_id') != id):
        flash('Access Denied.')
        return redirect(url_for(f"{session['role']}_dashboard"))
    if request.method == 'GET':
        str_date=request.args.get('date')

        if not str_date:
            if role == 'doctor':
                appointments = Appointment.query.filter_by(doctor_id=id).order_by(Appointment.date.asc(), Appointment.slot.asc()).all()
            elif role == 'patient':
                appointments = Appointment.query.filter_by(patient_id=id).order_by( Appointment.date.asc(), Appointment.slot.asc()).all()
            elif role == 'admin':
                appointments=Appointment.query.order_by(Appointment.date.asc(), Appointment.slot.asc()).all()
            else:
                flash('Invalid role.')
                return redirect(url_for('home'))
            return render_template('appointment/appointments.html', appointments=appointments, role=role, id=id)

        try:
            date=datetime.strptime(str_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date.')
            return redirect(url_for('appointments', role=role, id=id))

        if role == 'doctor':
            appointments=Appointment.query.filter_by(doctor_id=id, date=date).all()
        elif role == 'patient':
            appointments=Appointment.query.filter_by(patient_id=id, date=date).all()
        elif role == 'admin':
            appointments=Appointment.query.filter_by(date=date).all()
        else:
            flash('Invalid role.')
            return redirect(url_for('home'))
        
        return render_template('appointment/appointments.html', appointments=appointments, role=role, id=id)


@app.route('/admin_dashboard')
@login_auth
@admin_auth
def admin_dashboard():
    departments=Department.query.filter_by(status='Active').order_by(Department.id.asc()).limit(3).all()
    doctors=Doctor.query.filter_by(status='Active').order_by(Doctor.id.asc()).limit(3).all()
    patients=Patient.query.filter_by(status='Active').order_by(Patient.id.asc()).limit(3).all()
    appointments=Appointment.query.filter_by(status='Booked').order_by(Appointment.id.asc()).limit(3).all()
    total_patients = Patient.query.count()
    total_doctors = Doctor.query.count()
    total_appointments = Appointment.query.count()
    total_departments = Department.query.count()
    booked_appointments=Appointment.query.filter_by(status='Booked').count()
    completed_appointments=Appointment.query.filter_by(status='Completed').count()
    cancelled_appointments=Appointment.query.filter_by(status='Cancelled').count()
    today = datetime.now().date()
    today_appointments=Appointment.query.filter(Appointment.date==today).count()
    today_completed = Appointment.query.filter(Appointment.date == today,Appointment.status == 'Completed').count()

    today_cancelled = Appointment.query.filter(
        Appointment.date == today,
        Appointment.status == 'Cancelled'
    ).count()
    active_doctors=Doctor.query.filter_by(status='Active').count()
    recent_appointments=Appointment.query.order_by(Appointment.id.desc()).limit(3).all()
    recent_patients=Patient.query.order_by(Patient.id.desc()).limit(3).all()
    recent_doctors=Doctor.query.order_by(Doctor.id.desc()).limit(3).all()

    return render_template(
        'admin/admin_dashboard.html',
        departments=departments,
        doctors=doctors,
        patients=patients,
        appointments=appointments,
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        total_departments=total_departments,
        booked_appointments=booked_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        today_appointments=today_appointments,
        today_completed=today_completed,
        today_cancelled=today_cancelled,
        active_doctors=active_doctors,
        recent_appointments=recent_appointments,
        recent_patients=recent_patients,
        recent_doctors=recent_doctors
    )

@app.route('/admins', methods=['GET', 'POST'])
@login_auth
@admin_auth
def admins():
    if request.method == 'GET':
        admins = Admin.query.all()

        return render_template('admin/admins.html', admins=admins)


@app.route('/admin/add', methods=['GET', 'POST'])
@login_auth
@admin_auth
def add_admin():
    if request.method == 'GET':
        return render_template('admin/add_admin.html')
    username=request.form.get('username')
    password=request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    name=request.form.get('name')
    address=request.form.get('address')
    contact=request.form.get('contact')
    if (not username or not password or not confirm_password or not name or not address or not contact):
        flash('Please fill out all the fields.')
        return redirect(url_for('add_admin'))
    if password != confirm_password:
        flash('Passwords do not match.')
        return redirect(url_for('add_admin'))
    user=fetch_user_by_username(username, 'admin')

    if user:
        flash('This username already exists, kindly use a different username.')
        return redirect(url_for('add_admin'))
    
    new_admin = Admin( username=username, passhash=generate_password_hash(password),  name=name, address=address, contact=contact)
    db.session.add(new_admin)
    db.session.commit()
    flash('Admin added successfully.')

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/<int:id>/status_change', methods=['GET', 'POST'])
@login_auth
@admin_auth
def change_admin_status(id):
    admin=Admin.query.filter_by(id=id).first()
    if not admin:
        flash('Admin not found.')
        return redirect(url_for('admin_dashboard'))
    if request.method == 'GET':
        return render_template('admin/blacklist_admin.html', admin=admin)
    if admin.status == 'Active':
        admin.status = 'Inactive'
    else:
        admin.status = 'Active'
    db.session.commit()
    flash('Admin status changed successfully.')

    return redirect(url_for('admin_dashboard'))
