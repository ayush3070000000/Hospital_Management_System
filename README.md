# Hospital Management System

## Introduction

The Hospital Management System is a multi-role web application built with Flask, SQLite, SQLAlchemy, Jinja2, and Bootstrap. It provides separate functionality for Admins, Doctors, and Patients.

The Admin can oversee departments, doctors, patients, and appointments. Doctors can manage their availability, view appointments, and record patient treatments. Patients can register an account, manage their profile, search and browse active departments and doctors, and book, reschedule, or cancel appointments.

The system also includes role-based access control and Active/Inactive account and department management to restrict access and improve security.

## Technologies Used

- **Python & Flask**: Backend web framework and routing.
- **SQLite & SQLAlchemy**: Database and ORM for data storage and queries.
- **HTML/CSS & Bootstrap**: Frontend structure, styling, and responsive design.
- **Jinja2**: Template engine for rendering dynamic pages.
- **Werkzeug**: Password hashing and authentication-related security utilities.
- **python-dotenv**: Loading environment variables such as the secret key and database URI.

## Core Features

### Admin Role

- **Automatic Admin Creation**: On first launch, the system automatically creates a default admin account if no admin exists in the database (see `models.py`).
- **Dashboard**: View summary information including departments, doctors, patients, appointments, active doctors, and recent records.
- **Manage Departments**: Add, edit, view, and change department status between Active and Inactive.
- **Manage Doctors**: Add doctors, assign them to departments, view doctor details, and change individual doctor status between Active and Inactive.
- **Manage Patients**: View registered patients and change patient status between Active and Inactive.
- **Manage Appointments**: View appointments across the system and manage appointments on behalf of patients or doctors.
- **Reschedule / Cancel Appointments**: The Admin can reschedule or cancel any appointment regardless of the patient or doctor associated with it.
- **Manage Admins**: View existing administrator accounts, add administrators, and change admin account status.
- **View Doctor Availability**: Admins can view doctor availability without modifying it.
- **No Diagnosis Access**: Admins cannot diagnose patients or create doctor treatment records.

### Doctor Role

- **Doctor Login**: Doctors can log in only when their own account is Active and their assigned department is Active.
- **Update Availability**: Doctors can create and update their own availability using 30-minute appointment slots.
- **20 Daily Slots**: The schedule contains 20 bookable slots divided into morning and evening shifts.
- **Morning Shift A**: 08:00 AM to 02:00 PM with 12 slots.
- **Break**: 02:00 PM to 04:00 PM with no bookable slots.
- **Evening Shift B**: 04:00 PM to 08:00 PM with 8 slots.
- **Doctor Dashboard**: View upcoming booked appointments and treated patients.
- **Treat Patients**: Record diagnosis, treatment, and instructions for booked appointments. Saving treatment marks the appointment as Completed.
- **Appointments**: Doctors can view and manage their own appointments.
- **Reschedule / Cancel**: Doctors can reschedule or cancel their own appointments.
- **Profile**: View and manage personal profile information and department details.

### Patient Role

- **Registration & Login**: New patients can register and log in to their accounts.
- **Active Account Requirement**: Inactive patients cannot log in and are instructed to contact the admin.
- **Browse Departments**: Patients can see only Active departments.
- **Browse Doctors**: Patients can see only doctors whose individual status is Active and whose department is Active.
- **Doctor Details**: Patients can view doctor name, department, and contact information without access to private account details.
- **Search**: Patients can search active departments and active doctors.
- **Book Appointments**: Patients can select a doctor and an available slot from the doctor's schedule.
- **Past Slot Protection**: A slot cannot be booked once its scheduled start time has passed.
- **Reschedule Appointments**: Patients can reschedule their own booked appointments to another available slot.
- **Cancel Appointments**: Patients can cancel their own booked appointments.
- **Treatment History**: Patients can view their own treatment history recorded by doctors.
- **Appointment History**: Patients can view their own appointments and their statuses.

## Department and Account Status Logic

The system uses separate Active/Inactive status controls for departments, doctors, patients, and admins.

### Department Status

When a department is set to **Inactive**:

- The department is hidden from patients.
- Doctors belonging to that department are unavailable to patients.
- Those doctors cannot log in while the department remains inactive.
- The individual doctor status stored in the database is not automatically changed.

When the department becomes **Active** again:

- Doctors who are individually Active become available again.
- Doctors who are individually Inactive remain Inactive until the admin activates them.

### Doctor Status

A doctor is effectively available only when both conditions are satisfied:

```text
Doctor Status = Active
AND
Department Status = Active
```

An inactive doctor cannot log in or accept new patient bookings.

### Patient Status

An inactive patient cannot log in and receives a message asking them to contact the admin.

## Appointment System

HMS Royal uses fixed 30-minute appointment slots.

### Morning Shift A — 08:00 AM to 02:00 PM

| Slot | Display Name | Time |
|---|---|---|
| 1 | Slot 1A | 08:00 AM |
| 2 | Slot 2A | 08:30 AM |
| 3 | Slot 3A | 09:00 AM |
| 4 | Slot 4A | 09:30 AM |
| 5 | Slot 5A | 10:00 AM |
| 6 | Slot 6A | 10:30 AM |
| 7 | Slot 7A | 11:00 AM |
| 8 | Slot 8A | 11:30 AM |
| 9 | Slot 9A | 12:00 PM |
| 10 | Slot 10A | 12:30 PM |
| 11 | Slot 11A | 01:00 PM |
| 12 | Slot 12A | 01:30 PM |

### Break — 02:00 PM to 04:00 PM

No appointments are available during the break period.

### Evening Shift B — 04:00 PM to 08:00 PM

| Database Slot | Display Name | Time |
|---|---|---|
| 13 | Slot 1B | 04:00 PM |
| 14 | Slot 2B | 04:30 PM |
| 15 | Slot 3B | 05:00 PM |
| 16 | Slot 4B | 05:30 PM |
| 17 | Slot 5B | 06:00 PM |
| 18 | Slot 6B | 06:30 PM |
| 19 | Slot 7B | 07:00 PM |
| 20 | Slot 8B | 07:30 PM |

There are **20 bookable slots per day**.

The application prevents booking past dates and prevents patients from booking time slots whose scheduled start time has already passed.

When a slot is booked, it becomes unavailable for other patients. When an appointment is cancelled, the corresponding slot becomes available again.

## Appointment Permissions

| Action | Admin | Doctor | Patient |
|---|---|---|---|
| Book appointment | Yes, through appointment management flow | No | Yes |
| Cancel any appointment | Yes | Own appointments only | Own appointments only |
| Reschedule any appointment | Yes | Own appointments only | Own appointments only |
| Diagnose / Add treatment | No | Own appointments only | No |
| View all appointments | Yes | No | No |
| View own appointments | Yes | Yes | Yes |

## Security and Authorization

The application includes role-based access controls and server-side authorization.

- Separate authentication for Admin, Doctor, and Patient roles.
- Inactive users cannot log in.
- Doctors cannot log in when their department is inactive.
- Patients cannot see inactive departments or inactive doctors.
- Direct URLs are protected by server-side authorization checks.
- Patients can access only their own appointment history and treatment history.
- Doctors can manage only their own availability.
- Doctors can access only their own appointment-management actions.
- Admins can manage appointments for any patient or doctor.
- Admins do not have access to diagnosis functionality.
- Profile and profile-editing access is restricted according to user role and ownership.
- Direct booking requests validate doctor and department status on the server.
- Past appointment slots are validated on the server.
- Browser caching protection is used for authenticated pages.
- Logged-in users are prevented from returning to the public Home page through the application flow.
- Passwords are stored using secure password hashing rather than plain text.

## Additional Features

- **Server-side Form Validation**: Required fields and password confirmation are validated before database changes are made.
- **Flash Messages**: Flask flash messages provide feedback for successful actions and validation errors.
- **Search Functionality**: Admins and patients can search supported records.
- **Responsive UI**: Bootstrap and custom CSS provide responsive layouts for different screen sizes.
- **Outdated Data Cleanup**: Outdated doctor schedule entries are removed, and older booked appointments can be marked as missed.
- **Database Initialization**: SQLAlchemy creates the required tables automatically when the application starts.
- **PostgreSQL Support**: The project includes PostgreSQL-compatible configuration handling in addition to SQLite.

## Setup Instructions

### Clone or Download

Clone the repository or download and extract the project:

```bash
git clone <your-repository-url>
cd Hospital_Management_System-main
```

### Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Requirements

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your_secret_key_here
SQLALCHEMY_DATABASE_URI=sqlite:///hms.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
```

`SECRET_KEY` is used by Flask for secure session handling.

`SQLALCHEMY_DATABASE_URI` defines the database connection. SQLite can be used for local development, while PostgreSQL can be configured for deployment.

Do not commit the `.env` file to GitHub.

### Run the Application

Start the Flask application:

```bash
python app.py
```

The application will normally be available at:

```text
http://localhost:5000
```

### Database Initialization

On first launch, the application automatically creates the database tables.

If no administrator exists, a default admin account is created automatically by `models.py`.

## Default Admin Credentials

The default admin account is created in `models.py` if no admin account exists.

```text
Username: admin
Password: admin
```

After logging in for the first time, it is strongly recommended to change the default password and create a separate administrator account.

## GitHub and Security Notes

Before pushing the project to GitHub, make sure sensitive and generated files are excluded.

Recommended `.gitignore` entries:

```gitignore
.env
venv/
.venv/
__pycache__/
*.pyc
instance/
*.db
```

Do not upload:

- Secret keys
- Database passwords
- Production credentials
- `.env` files
- Virtual environment folders
- Local database files containing real user information

## Future Improvements

Possible future improvements include:

- Email or SMS appointment notifications
- Password reset and recovery
- Prescription management
- Medical document uploads
- Advanced reporting and analytics
- Doctor and department filtering
- Automated database migrations
- Production logging and monitoring
- API endpoints for external integrations
- Improved deployment configuration

## Author

Hospital Management System

Built as a Flask-based healthcare management application with separate Admin, Doctor, and Patient portals.

## License

This project is intended for educational and development purposes. Add an appropriate open-source license if the project is distributed publicly.

## Live Link

https://hospital-management-system-h6jy.onrender.com/(Initial loading may take 2–3 minutes due to Render cold starts.)
