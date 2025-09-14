import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change this in production!


# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()


# --- Dummy Data ---
courses_data = [
    {"title": "Python for Beginners", "provider": "Coursera", "rating": "4.7", "price": "Free", "url": "https://www.coursera.org"},
    {"title": "AI & Machine Learning Bootcamp", "provider": "Udemy", "rating": "4.6", "price": "$19.99", "url": "https://www.udemy.com"},
    {"title": "Data Science Fundamentals", "provider": "edX", "rating": "4.8", "price": "Free", "url": "https://www.edx.org"},
    {"title": "Full Stack Web Development", "provider": "Udemy", "rating": "4.5", "price": "$14.99", "url": "https://www.udemy.com"},
    {"title": "Deep Learning Specialization", "provider": "Coursera", "rating": "4.9", "price": "$49/month", "url": "https://www.coursera.org"},
    {"title": "Frontend Development with React", "provider": "Udacity", "rating": "4.7", "price": "Free", "url": "https://www.udacity.com"}
]

scholarships_data = [
    {"title": "Pre-Matric Scholarship for Minorities", "provider": "Ministry of Minority Affairs, Govt. of India", "eligibility": "Minority students, Class 1-10", "url": "https://scholarships.gov.in/pre-matric-minorities"},
    {"title": "Merit-cum-Means Scholarship for Professional & Technical Courses", "provider": "Ministry of Minority Affairs, Govt. of India", "eligibility": "UG / PG in professional & technical education", "url": "https://scholarships.gov.in/mcm-professional-technical"},
    {"title": "Foundation For Excellence (FFE) Scholarship", "provider": "FFE", "eligibility": "Low-income, academically gifted UG/PG students", "url": "https://www.ffe.org/"},
    {"title": "Central Sector Scheme of Scholarships", "provider": "Government of India", "eligibility": "College / University students", "url": "https://scholarships.gov.in/central-sector"},
    {"title": "Sahu Jain Trust Educational Scholarships", "provider": "Sahu Jain Trust", "eligibility": "Meritorious students, UG/PG courses", "url": "http://sahujaintrust.timesofindia.com/"},
    {"title": "Tata Scholarship for Engineering Students", "provider": "Tata Group", "eligibility": "UG Engineering students in India", "url": "https://www.tatatrusts.org/"}
]


# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html", title="SKOLARAI", current_year=datetime.now().year)


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user"] = username
            flash("Signed in successfully ✅", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password ❌", "danger")
            return redirect(url_for("signin"))

    return render_template("signin.html", title="Sign In - SKOLARAI", current_year=datetime.now().year)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match ❌", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, hashed_password))
            conn.commit()
            conn.close()
            flash("Account created successfully 🎉 Please sign in.", "success")
            return redirect(url_for("signin"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists ❌", "danger")
            return redirect(url_for("register"))

    return render_template("register.html", title="Register - SKOLARAI", current_year=datetime.now().year)


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        flash("Please sign in to access the dashboard ⚠️", "warning")
        return redirect(url_for("signin"))

    course_results = []
    scholarship_results = scholarships_data[:]  # show all by default

    if request.method == "POST":
        section = request.form.get("section")
        query = request.form.get("query", "").lower()
        filter_option = request.form.get("filter")

        if section == "courses":
            filtered = courses_data
            if filter_option == "free":
                filtered = [c for c in filtered if c["price"].lower() == "free"]
            elif filter_option == "paid":
                filtered = [c for c in filtered if c["price"].lower() != "free"]

            course_results = [c for c in filtered if query in c["title"].lower() or query in c["provider"].lower()]

        elif section == "scholarships":
            scholarship_results = [s for s in scholarships_data if query in s["title"].lower() or query in s["provider"].lower()]

    featured_courses = courses_data[:4]

    return render_template(
        "dashboard.html",
        title="Dashboard - SKOLARAI",
        user=session["user"],
        courses=course_results,
        scholarships=scholarship_results,
        featured_courses=featured_courses,
        current_year=datetime.now().year
    )


# Suggestions only for courses
@app.route("/suggest", methods=["GET"])
def suggest():
    query = request.args.get("q", "").lower()
    section = request.args.get("section", "")

    suggestions = []
    if section == "courses":
        suggestions = [c["title"] for c in courses_data if query in c["title"].lower()]

    return jsonify(suggestions)


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out ✅", "info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
