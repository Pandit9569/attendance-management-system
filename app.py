from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key ="attendance_secret_key"
@app.route("/")
def main_page():
    return render_template("index.html")
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin_logged_in"] = True
            return redirect("/admin_dashboard")

        return "Invalid Admin Username or Password"

    return render_template("admin_login.html")
@app.route("/admin_dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    return render_template("admin_dashboard.html")
@app.route("/add_teacher", methods=["GET", "POST"])
def add_teacher():

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        subject = request.form["subject"]

        conn = get_db()

        try:
            conn.execute(
                """
                INSERT INTO teachers (username, password, subject)
                VALUES (?, ?, ?)
                """,
                (username, password, subject)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Teacher username already exists"

        conn.close()

        return redirect("/admin_dashboard")

    return render_template("add_teacher.html")
@app.route("/teachers")
def teachers():

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db()

    teachers = conn.execute(
        "SELECT id, username, subject FROM teachers ORDER BY id"
    ).fetchall()

    conn.close()

    return render_template(
        "teachers.html",
        teachers=teachers
    )

def get_db():
    conn = sqlite3.connect("attendance.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            date TEXT,
        status TEXT
    )
""")    
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            course TEXT NOT NULL
        )
    """)
    try:
        conn.execute("ALTER TABLE students ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute("ALTER TABLE students ADD COLUMN password TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE attendance ADD COLUMN subject TEXT")
    except sqlite3.OperationalError:
     pass 
    conn.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        subject TEXT NOT NULL
    )
""")
    conn.execute("""
    INSERT OR IGNORE INTO teachers (username, password, subject)
    VALUES (?, ?, ?)
""", ("teacher_coa", "1234", "COA"))   
    conn.commit()
    conn.close()

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username == "admin" and password == "1234":
        return redirect("/dashboard")

    return """
    <h2>Invalid Username or Password</h2>
    <a href="/">Go Back</a>
    """


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/students")
def students():
    conn = get_db()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students
    )
@app.route("/add_student", methods=["POST"])
def add_student():

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    name = request.form["name"]
    roll_no = request.form["roll_no"]
    course = request.form["course"]
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db()

    try:
        conn.execute(
            """
            INSERT INTO students
            (name, roll_no, course, username, password)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, roll_no, course, username, password)
        )

        conn.commit()

    except sqlite3.IntegrityError:
        conn.close()
        return "Student username already exists"

    conn.close()

    return redirect("/students")

@app.route("/delete_student_attendance/<int:student_id>")
def delete_student_attendance(student_id):

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db()

    conn.execute(
        "DELETE FROM attendance WHERE student_id = ?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/students")
@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    conn = get_db()

    conn.execute(
        "DELETE FROM attendance WHERE student_id = ?",
        (student_id,)
    )

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/students")
@app.route("/teacher_login", methods=["GET", "POST"])
def teacher_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        teacher = conn.execute(
            "SELECT * FROM teachers WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()

        conn.close()

        if teacher:
            session["teacher_username"] = teacher["username"]
            return redirect("/teacher_dashboard")

        return "Invalid username or password"

    return render_template("teacher_login.html")
@app.route("/teacher_dashboard")
def teacher_dashboard():

    username = session.get("teacher_username")

    if not username:
        return redirect("/teacher_login")

    conn = get_db()

    teacher = conn.execute(
        "SELECT * FROM teachers WHERE username = ?",
        (username,)
    ).fetchone()

    conn.close()

    if not teacher:
        return redirect("/teacher_login")

    return render_template(
        "teacher_dashboard.html",
        teacher=teacher
    )
@app.route("/student_login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        student = conn.execute(
            """
            SELECT * FROM students
            WHERE username = ? AND password = ?
            """,
            (username, password)
        ).fetchone()

        conn.close()

        if student:
            session["student_id"] = student["id"]
            return redirect("/student_dashboard")

        return "Invalid Student Username or Password"

    return render_template("student_login.html")
@app.route("/student_dashboard")
def student_dashboard():

    student_id = session.get("student_id")

    if not student_id:
        return redirect("/student_login")

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    conn.close()

    if not student:
        return redirect("/student_login")

    return render_template(
        "student_dashboard.html",
        student=student
    )
@app.route("/student_report")
def student_report():

    student_id = session.get("student_id")

    if not student_id:
        return redirect("/student_login")

    conn = get_db()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if not student:
        conn.close()
        return redirect("/student_login")

    rows = conn.execute(
        """
        SELECT
            subject,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent
        FROM attendance
        WHERE student_id = ?
        GROUP BY subject
        ORDER BY subject
        """,
        (student_id,)
    ).fetchall()

    reports = []

    for row in rows:

        total = row["total"] or 0
        present = row["present"] or 0
        absent = row["absent"] or 0

        percentage = round(
            (present / total) * 100, 2
        ) if total > 0 else 0

        reports.append({
            "subject": row["subject"] or "No Subject",
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage
        })

    conn.close()

    return render_template(
        "student_report.html",
        student=student,
        reports=reports
    )
@app.route("/teacher_attendance")
def teacher_attendance():
    username = session.get("teacher_username")

    if not username:
        return redirect("/teacher_login")

    conn = get_db()

    teacher = conn.execute(
        "SELECT * FROM teachers WHERE username = ?",
        (username,)
    ).fetchone()

    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    if not teacher:
        return redirect("/teacher_login")

    return render_template(
        "teacher_attendance.html",
        teacher=teacher,
        students=students
    )
@app.route("/teacher_mark_attendance", methods=["POST"])
def teacher_mark_attendance():

    username = session.get("teacher_username")

    if not username:
        return redirect("/teacher_login")

    student_id = request.form["student_id"]
    status = request.form["status"]

    conn = get_db()

    teacher = conn.execute(
        "SELECT * FROM teachers WHERE username = ?",
        (username,)
    ).fetchone()

    if not teacher:
        conn.close()
        return redirect("/teacher_login")

    from datetime import date
    today = date.today().isoformat()

    # Check if attendance already exists for today
    existing = conn.execute(
        """
        SELECT id FROM attendance
        WHERE student_id = ?
        AND date = ?
        AND subject = ?
        """,
        (student_id, today, teacher["subject"])
    ).fetchone()

    if existing:
        conn.execute(
            """
            UPDATE attendance
            SET status = ?
            WHERE id = ?
            """,
            (status, existing["id"])
        )
    else:
        conn.execute(
            """
            INSERT INTO attendance
            (student_id, date, status, subject)
            VALUES (?, ?, ?, ?)
            """,
            (student_id, today, status, teacher["subject"])
        )

    conn.commit()
    conn.close()

    return redirect("/teacher_attendance")
@app.route("/teacher_report")
def teacher_report():

    username = session.get("teacher_username")

    if not username:
        return redirect("/teacher_login")

    conn = get_db()

    teacher = conn.execute(
        "SELECT * FROM teachers WHERE username = ?",
        (username,)
    ).fetchone()

    if not teacher:
        conn.close()
        return redirect("/teacher_login")

    students = conn.execute("""
        SELECT
            students.id,
            students.name,
            students.roll_no,
            students.course,
            COUNT(attendance.id) AS total,
            SUM(CASE WHEN attendance.status = 'Present' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN attendance.status = 'Absent' THEN 1 ELSE 0 END) AS absent
        FROM students
        LEFT JOIN attendance
        ON students.id = attendance.student_id
        AND attendance.subject = ?
        GROUP BY students.id
        ORDER BY students.roll_no
    """, (teacher["subject"],)).fetchall()

    report_data = []

    for student in students:

        total = student["total"] or 0
        present = student["present"] or 0
        absent = student["absent"] or 0

        percentage = round(
            (present / total) * 100, 2
        ) if total > 0 else 0

        report_data.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "course": student["course"],
            "subject": teacher["subject"],
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage
        })

    conn.close()

    return render_template(
        "teacher_report.html",
        teacher=teacher,
        students=report_data
    )
@app.route("/attendance")
def attendance():
    conn = get_db()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()

    return render_template("attendance.html", students=students)
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    student_id = request.form["student_id"]
    status = request.form["status"]
    subject = request.form["subject"]

    conn = get_db()

    from datetime import date
    today = date.today().isoformat()

    conn.execute(
        "INSERT INTO attendance (student_id, date, status, subject) VALUES (?, ?, ?, ?)",
        (student_id, today, status, subject)
    )

    conn.commit()
    conn.close()

    return redirect("/attendance") 
@app.route("/report")
def report():

    if not session.get("admin_logged_in"):
        return redirect("/admin_login")

    conn = get_db()

    search = request.args.get("search", "").strip()

    if search:
        students = conn.execute("""
            SELECT id, name, roll_no, course
            FROM students
            WHERE name LIKE ? OR roll_no LIKE ?
            ORDER BY roll_no
        """, (f"%{search}%", f"%{search}%")).fetchall()
    else:
        students = conn.execute("""
            SELECT id, name, roll_no, course
            FROM students
            ORDER BY roll_no
        """).fetchall()

    subjects = [
        "COA",
        "Data Structures",
        "DSDL",
        "Digital Electronics",
        "Technical Communication",
        "Python Programming"
    ]

    report_data = []

    for student in students:

        subject_data = {}

        for subject in subjects:

            row = conn.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) AS present,
                    SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) AS absent
                FROM attendance
                WHERE student_id = ?
                AND subject = ?
            """, (student["id"], subject)).fetchone()

            total = row["total"] or 0
            present = row["present"] or 0
            absent = row["absent"] or 0

            percentage = round(
                (present / total) * 100, 2
            ) if total > 0 else 0

            subject_data[subject] = {
                "total": total,
                "present": present,
                "absent": absent,
                "percentage": percentage
            }

        report_data.append({
            "roll_no": student["roll_no"],
            "name": student["name"],
            "course": student["course"],
            "subjects": subject_data
        })

    conn.close()

    return render_template(
        "report.html",
        students=report_data,
        subjects=subjects,
        search=search
    )
if __name__ == "__main__":
    create_database()
    app.run(debug=True)