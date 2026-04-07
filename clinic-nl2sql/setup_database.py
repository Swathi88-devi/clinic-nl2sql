import sqlite3

def create_connection():
    return sqlite3.connect("clinic.db")

def create_tables(conn):
    cursor = conn.cursor()

    # Table 1: patients
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT,
        city TEXT,
        registered_date DATE
    );
    """)

    # Table 2: doctors
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        phone TEXT
    );
    """)

    # Table 3: appointments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATETIME,
        status TEXT,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id),
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
    );
    """)

    # Table 4: treatments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        treatment_name TEXT,
        cost REAL,
        duration_minutes INTEGER,
        FOREIGN KEY (appointment_id) REFERENCES appointments(id)
    );
    """)

    # Table 5: invoices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        invoice_date DATE,
        total_amount REAL,
        paid_amount REAL,
        status TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    );
    """)

    conn.commit()
    print("✅ All tables created successfully!")

def main():
    conn = create_connection()
    create_tables(conn)
    conn.close()

if __name__ == "__main__":
    main()
    """output for step 1 is clinic.db file created with 5 tables: patients, doctors, appointments, treatments, invoices"""
    """STEP 2 STARTS(Dummy Data Insertion)"""
    import sqlite3
import random
from datetime import datetime, timedelta

# -------------------- CONFIG --------------------
DB_NAME = "clinic.db"

FIRST_NAMES = ["Ravi", "Sita", "Amit", "Priya", "Kiran", "Anjali", "Rahul", "Sneha", "Vikram", "Pooja"]
LAST_NAMES = ["Sharma", "Reddy", "Kumar", "Patel", "Singh", "Das", "Nair", "Gupta"]
CITIES = ["Hyderabad", "Bangalore", "Chennai", "Mumbai", "Delhi", "Pune", "Kolkata", "Vizag", "Jaipur"]
GENDERS = ["M", "F"]

SPECIALIZATIONS = ["Dermatology", "Cardiology", "Orthopedics", "General", "Pediatrics"]
DEPARTMENTS = ["Skin", "Heart", "Bones", "General", "Child Care"]

APPOINTMENT_STATUS = ["Scheduled", "Completed", "Cancelled", "No-Show"]
INVOICE_STATUS = ["Paid", "Pending", "Overdue"]

TREATMENTS = ["Consultation", "X-Ray", "Blood Test", "MRI Scan", "Physiotherapy"]

# -------------------- DB SETUP --------------------
def connect():
    return sqlite3.connect(DB_NAME)

def create_tables(conn):
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        date_of_birth DATE,
        gender TEXT,
        city TEXT,
        registered_date DATE
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT,
        department TEXT,
        phone TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATETIME,
        status TEXT,
        notes TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id INTEGER,
        treatment_name TEXT,
        cost REAL,
        duration_minutes INTEGER
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        invoice_date DATE,
        total_amount REAL,
        paid_amount REAL,
        status TEXT
    )""")

    conn.commit()

# -------------------- HELPERS --------------------
def random_date_within_last_year():
    today = datetime.now()
    days_back = random.randint(0, 365)
    return (today - timedelta(days=days_back)).strftime("%Y-%m-%d")

def random_datetime_within_last_year():
    today = datetime.now()
    days_back = random.randint(0, 365)
    random_time = timedelta(hours=random.randint(8, 18), minutes=random.randint(0, 59))
    return (today - timedelta(days=days_back) + random_time).strftime("%Y-%m-%d %H:%M:%S")

def maybe_null(value, prob=0.2):
    return value if random.random() > prob else None

# -------------------- INSERT DATA --------------------
def insert_doctors(conn):
    cur = conn.cursor()
    doctors = []

    for i in range(15):
        name = f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        spec = random.choice(SPECIALIZATIONS)
        dept = DEPARTMENTS[SPECIALIZATIONS.index(spec)]
        phone = maybe_null(f"9{random.randint(100000000,999999999)}")

        doctors.append((name, spec, dept, phone))

    cur.executemany("INSERT INTO doctors (name, specialization, department, phone) VALUES (?, ?, ?, ?)", doctors)
    conn.commit()
    return 15

def insert_patients(conn):
    cur = conn.cursor()
    patients = []

    for _ in range(200):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        email = maybe_null(f"{fn.lower()}{random.randint(1,999)}@gmail.com")
        phone = maybe_null(f"9{random.randint(100000000,999999999)}")
        dob = (datetime.now() - timedelta(days=random.randint(18*365, 70*365))).strftime("%Y-%m-%d")
        gender = random.choice(GENDERS)
        city = random.choice(CITIES)
        reg_date = random_date_within_last_year()

        patients.append((fn, ln, email, phone, dob, gender, city, reg_date))

    cur.executemany("""
        INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, patients)

    conn.commit()
    return 200

def insert_appointments(conn):
    cur = conn.cursor()
    appointments = []

    for _ in range(500):
        patient_id = random.randint(1, 200)  # repeat patients
        doctor_id = random.randint(1, 15)
        date = random_datetime_within_last_year()
        status = random.choice(APPOINTMENT_STATUS)
        notes = maybe_null("Follow-up required")

        appointments.append((patient_id, doctor_id, date, status, notes))

    cur.executemany("""
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
    """, appointments)

    conn.commit()
    return 500

def insert_treatments(conn):
    cur = conn.cursor()

    # Only completed appointments
    cur.execute("SELECT id FROM appointments WHERE status='Completed'")
    completed_ids = [row[0] for row in cur.fetchall()]

    treatments = []
    for _ in range(350):
        if not completed_ids:
            break
        appt_id = random.choice(completed_ids)
        name = random.choice(TREATMENTS)
        cost = round(random.uniform(50, 5000), 2)
        duration = random.randint(10, 120)

        treatments.append((appt_id, name, cost, duration))

    cur.executemany("""
        INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
        VALUES (?, ?, ?, ?)
    """, treatments)

    conn.commit()
    return len(treatments)

def insert_invoices(conn):
    cur = conn.cursor()
    invoices = []

    for _ in range(300):
        patient_id = random.randint(1, 200)
        total = round(random.uniform(100, 10000), 2)
        paid = total if random.random() < 0.6 else round(random.uniform(0, total), 2)
        status = "Paid" if paid == total else random.choice(["Pending", "Overdue"])

        invoices.append((
            patient_id,
            random_date_within_last_year(),
            total,
            paid,
            status
        ))

    cur.executemany("""
        INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
        VALUES (?, ?, ?, ?, ?)
    """, invoices)

    conn.commit()
    return 300

# -------------------- MAIN --------------------
def main():
    conn = connect()
    create_tables(conn)

    d = insert_doctors(conn)
    p = insert_patients(conn)
    a = insert_appointments(conn)
    t = insert_treatments(conn)
    i = insert_invoices(conn)

    conn.close()

    print(f"✅ Created {p} patients, {d} doctors, {a} appointments, {t} treatments, {i} invoices")

if __name__ == "__main__":
    main()
    """output for step 2 is clinic.db file populated with dummy data: 200 patients, 15 doctors, 500 appointments, 350 treatments, 300 invoices"""
