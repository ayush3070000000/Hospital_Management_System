# Hospital Management System
## Introduction

The Hospital Management System is a multi-role web application built with Flask, SQLite, SQLAlchemy, Jinja2, and Bootstrap. It provides different functionality for Admins, Doctors, and Patients. The Admin can oversee all doctors, patients, and appointments. Doctors can manage their schedules, view upcoming appointments, and record patient treatments. Patients can register an account, manage their profile, search for doctors, and book or cancel appointments.

## Technologies Used
- **Python & Flask**: Backend web framework and routing.
- **SQLite & SQLAlchemy**: Embedded database and ORM for data storage and queries.
- **HTML/CSS & Bootstrap**: Frontend templating and styling.
- **Jinja2**: Template engine for rendering dynamic pages.
- **Werkzeug**: Security for password hashing.
- **python-dotenv**: For loading environment variables (database URI, secret key).

## Core Features
### Admin Role
- **Automatic Admin Creation**: On first launch, the system auto-creates a default admin account (username: admin, password: admin) in the database (see models.py).
- **Dashboard**: View summary widgets (counts of active departments, doctors, patients, and recent booked appointments).
- **Manage Doctors**: Add new doctors (assign to a department), view all doctors, and change a doctor’s status (Active/Inactive). Inactivation automatically cancels that doctor’s future appointments.
- **Manage Patients**: View all registered patients and change a patient’s status (Active/Inactive) if needed. Patients self-register, but the admin can deactivate accounts.
- **Manage Departments**: Create and edit medical departments (e.g. Cardiology, Neurology), view department details, and change department status. Departments group doctors by specialty.
- **Manage Appointments**: Review all scheduled appointments. (A list of recent booked appointments is available on the admin dashboard.) Admin can also navigate to doctor or patient views to manage appointments.
- **Manage Admins**: View existing admin accounts and add new admin users. The admin can toggle other admin accounts active/inactive as needed.

### Doctor Role
- **Update Schedule**: Define and update the weekly availability schedule. The doctor selects available time slots for each day; outdated slots are auto-removed.
- **Doctor Dashboard**: See upcoming Booked appointments for the week, and a list of patients the doctor has treated. A reminder prompts new doctors to update their schedule on first login.
- **Treat Patients**: For each booked appointment, the doctor can enter a treatment record. This includes diagnosis, prescribed treatment, and instructions. Submitting a treatment marks the appointment as Completed and saves the treatment history.
- **View Appointments**: Doctors can view and manage their own appointments list. (They see only appointments assigned to them.)
- **Profile**: View personal details and department information.

### Patient Role
- **Registration & Login**: New patients can register an account (providing name, address, contact, etc.). Registered patients can log in to manage their information.
- **Edit Profile**: Update personal details (address, contact info, etc.) via a profile page.
- **Search & Browse Doctors**: Patients can search for doctors by name or view the list of active doctors, along with their department and status.
- **Book Appointments**: Select a doctor and pick an available time slot from that doctor’s schedule. The system checks slot availability and reserves the appointment. Upon booking, the slot is marked unavailable.
- **Reschedule / Cancel Appointments**: Patients can reschedule existing Booked appointments by choosing a new slot (if their appointment is still active). They can also cancel appointments, which frees the slot for others.
- **View Appointments**: See a list of upcoming booked appointments and their statuses on the patient dashboard.
- **Treatment History**: After appointments are completed, patients can view their treatment history (diagnosis, treatment, instructions) recorded by doctors.

## Additional Features
- **Server-side Form Validation**: All forms check for required fields. The app flashes error messages if input validation fails (e.g. missing or mismatched passwords during registration).
- **Flash Messages**: The application uses Flask’s flashing system to inform users of successes or errors (e.g. “Appointment booked successfully,” “Please fill out all the fields,” etc.).
- **Search Functionality**: Patients and admins can search doctors or patients by name using a search bar. Results display matching records.
- **Responsive UI**: The front-end uses Bootstrap for a mobile-friendly, responsive layout. Navigation bars and tables are styled for clarity.
- **Database Seeding**: Beyond the default admin, departments and initial data can be added through the app’s interface. The SQLite database file is created automatically when the app runs.

## Setup Instructions
- **Clone or Download**: Unzip or clone the project repository to your local machine.
- **Create Virtual Environment**: In the project root, run (for example):
  - python3 -m venv venv
  - source venv/bin/activate  # (or `venv\Scripts\activate` on Windows)

- Install Requirements:
  - pip install -r requirements.txt
- Environment Variables: Create a .env file in the project root with the following variables:
  - SECRET_KEY=your_secret_key_here
  - SQLALCHEMY_DATABASE_URI=sqlite:///hms.db
  - SQLALCHEMY_TRACK_MODIFICATIONS=False
    - SECRET_KEY can be any random string (used by Flask for sessions and forms).
    - SQLALCHEMY_DATABASE_URI points to the SQLite database file (default hms.db in the project directory).

- Run the Application: Start the Flask app:
  - python app.py
    - The app will run in debug mode by default. Open your web browser and go to http://localhost:5000.
- Database and Admin User: On first run, the app will automatically create the SQLite database tables and a default admin user if none exists. You can then log in as admin.

## Default Admin Credentials
The default admin account is defined in models.py. By default, the username and password are both admin. You can locate this in the file near the bottom of models.py under the app context section where the admin is created. After logging in as admin, it is strongly recommended to add more administrator accounts and disable the automatically created admin account.
