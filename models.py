from app import app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy(app)

class Admin(db.Model):
    __tablename__ = 'Admins'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64),unique = True, nullable = False)
    passhash = db.Column(db.String(128), nullable = False)
    name = db.Column(db.String(64), nullable = False)
    address = db.Column(db.String(64), nullable = False)
    contact = db.Column(db.String(32), nullable = False)
    status = db.Column(db.String(20), nullable = False, default = 'Active')

class Department(db.Model):
    __tablename__ = 'Departments'

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64), unique = True, nullable = False)
    description = db.Column(db.String(128), nullable = False)
    status = db.Column(db.String(20), nullable = False, default = 'Active')

    doctors = db.relationship('Doctor', backref = 'department', lazy = True)    

class Doctor(db.Model):
    __tablename__ = 'Doctors'

    id = db.Column(db.Integer, primary_key = True)
    department_id = db.Column(db.Integer, db.ForeignKey('Departments.id'), nullable = True)
    username = db.Column(db.String(64), unique = True, nullable = False)
    passhash = db.Column(db.String(128), nullable = False)
    name = db.Column(db.String(64), nullable = False)
    address = db.Column(db.String(64), nullable = False)
    contact = db.Column(db.String(32), nullable = False)
    description = db.Column(db.String(256), nullable = False)
    status = db.Column(db.String(20), nullable = False, default = 'Active')

    appointments = db.relationship('Appointment', backref = 'doctor', lazy = True)
    schedule = db.relationship('Doctor_Schedule', backref = 'doctor', cascade='all, delete-orphan', lazy = True)

class Patient(db.Model):
    __tablename__ = 'Patients'

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), unique = True, nullable = False)
    passhash = db.Column(db.String(128), nullable = False)
    name = db.Column(db.String(64), nullable = False)
    address = db.Column(db.String(64), nullable = False)
    contact = db.Column(db.String(32), nullable = False)
    status = db.Column(db.String(20), nullable = False, default = 'Active')

    appointments = db.relationship('Appointment', backref = 'patient', lazy = True)

class Appointment(db.Model):
    __tablename__ = 'Appointments'

    id = db.Column(db.Integer, primary_key = True)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patients.id'), nullable = False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('Doctors.id'), nullable = False)
    visit_type = db.Column(db.String(20), nullable = False, default = 'In-Person')
    date = db.Column(db.Date, nullable = False)
    slot = db.Column(db.Integer, nullable = False)
    status = db.Column(db.String(20), nullable = False, default = 'Booked')

    __table_args__ = (db.UniqueConstraint('doctor_id', 'slot', 'date', name='unique_doctor_appointment'),)

class Doctor_Schedule(db.Model):
    __tablename__ = 'Doctor_Schedule'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('Doctors.id'), nullable=False)
    date = db.Column(db.Date, nullable = False)
    slot_1 = db.Column(db.Boolean, nullable=True)
    slot_2 = db.Column(db.Boolean, nullable=True)
    status = db.Column(db.Boolean, nullable= False, default = True)

class Treatment(db.Model):
    __tablename__ = 'Treatments'

    id = db.Column(db.Integer, primary_key = True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('Appointments.id'), nullable = False)
    patient_id = db.Column(db.Integer, db.ForeignKey('Patients.id'), nullable = False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('Doctors.id'), nullable = False)
    diagnosis = db.Column(db.String(128), nullable = False)
    treatment = db.Column(db.String(128), nullable = False)
    instruction = db.Column(db.String(128), nullable = False)

    appointment = db.relationship('Appointment', backref = 'treatment', uselist = False,  lazy = True)
    patient = db.relationship('Patient', backref = 'treatment', lazy = True)
    doctor = db.relationship('Doctor', backref = 'treatment', lazy = True)

with app.app_context():
    # db.drop_all()
    db.create_all()

    # Create a new admin programmatically if none exists
    admin = Admin.query.first()
    if not admin:
        password_hash = generate_password_hash ('admin')
        admin = Admin(username = 'admin', passhash = password_hash, name = 'admin', address = 'admin address', contact = '0000000000')
        db.session.add(admin)
        db.session.commit()