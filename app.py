import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- Ensure instance folder exists ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__, instance_relative_config=False)
app.secret_key = "supersecretkey"

# --- Database Config (absolute path) ---
db_path = os.path.join(INSTANCE_DIR, "skolarai.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    provider = db.Column(db.String(100))
    rating = db.Column(db.String(20))
    price = db.Column(db.String(80))
    url = db.Column(db.String(400))
    tags = db.Column(db.String(300))
    region = db.Column(db.String(50), default="India")
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)


class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    provider = db.Column(db.String(200))
    eligibility = db.Column(db.String(300))
    deadline = db.Column(db.String(100))
    url = db.Column(db.String(400))
    tags = db.Column(db.String(300))
    region = db.Column(db.String(50), default="India")
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)


# --- Auto-seed sample data (only runs if DB empty) ---
def seed_data():
    if Course.query.count() == 0 and Scholarship.query.count() == 0:
        print("🌱 Seeding sample data...")

        courses = [
            Course(title="Python for Data Science", provider="Coursera", rating="4.8", price="Free",
                   url="https://www.coursera.org/learn/python-for-data-science", tags="python,data,ai"),
            Course(title="AI & Machine Learning Bootcamp", provider="Udemy", rating="4.6", price="₹499",
                   url="https://www.udemy.com/course/ai-and-machine-learning-bootcamp", tags="ai,ml"),
            Course(title="Full Stack Web Development", provider="edX", rating="4.7", price="Free",
                   url="https://www.edx.org/learn/web-development", tags="web,frontend,backend"),
            Course(title="Data Structures & Algorithms", provider="Coding Ninjas", rating="4.5", price="₹2999",
                   url="https://www.codingninjas.com/courses/data-structures-algorithms", tags="dsa,algorithms"),
            Course(title="Cloud Computing Basics", provider="AWS Academy", rating="4.6", price="Free",
                   url="https://aws.amazon.com/training", tags="cloud,aws"),
            Course(title="Java Programming Masterclass", provider="Udemy", rating="4.7", price="₹449",
                   url="https://www.udemy.com/course/java-the-complete-java-developer-course", tags="java,programming"),
            Course(title="Deep Learning Specialization", provider="Coursera", rating="4.9", price="₹1299",
                   url="https://www.coursera.org/specializations/deep-learning", tags="deep-learning,ai"),
            Course(title="React - The Complete Guide", provider="Udemy", rating="4.7", price="₹599",
                   url="https://www.udemy.com/course/react-the-complete-guide", tags="react,frontend"),
            Course(title="Introduction to SQL", provider="Codecademy", rating="4.5", price="Free",
                   url="https://www.codecademy.com/learn/learn-sql", tags="sql,database"),
            Course(title="Kotlin for Android Development", provider="Udacity", rating="4.4", price="₹799",
                   url="https://www.udacity.com/course/kotlin-android", tags="android,kotlin")
        ]

        scholarships = [
            Scholarship(title="Central Sector Scholarship", provider="Govt. of India", eligibility="UG Students",
                        deadline="31-12-2024", url="https://scholarships.gov.in", tags="government,india"),
            Scholarship(title="Tata Trust Scholarship", provider="Tata Trust", eligibility="Engineering UG",
                        deadline="30-09-2024", url="https://www.tatatrusts.org", tags="private,india"),
            Scholarship(title="Sahu Jain Trust Scholarship", provider="Sahu Jain Trust", eligibility="UG & PG Students",
                        deadline="15-08-2024", url="http://sahujaintrust.timesofindia.com/", tags="private,india")
        ]

        db.session.add_all(courses + scholarships)
        db.session.commit()
        print("✅ Seed complete.")


# --- Routes ---
@app.route("/")
def home():
    # Always show landing page
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please fill all required fields.", "warning")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match ❌", "danger")
            return redirect(url_for("register"))

        hashed = generate_password_hash(password)
        try:
            new_user = User(username=username, email=email, password=hashed)
            db.session.add(new_user)
            db.session.commit()
            flash("Account created! Please sign in.", "success")
            return redirect(url_for("signin"))
        except Exception:
            db.session.rollback()
            flash("Username or email already exists ❌", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user"] = username
            session["user_id"] = user.id
            flash("Signed in successfully ✅", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password ❌", "danger")
            return redirect(url_for("signin"))

    return render_template("signin.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "user" not in session:
        flash("Please sign in to access the dashboard ⚠️", "warning")
        return redirect(url_for("signin"))

    query = request.args.get("q", "").strip()
    filter_type = request.args.get("filter", "top")  # default: top 3

    courses_q = Course.query.filter_by(region="India").order_by(Course.id.asc())

    if query:
        like = f"%{query}%"
        courses_q = courses_q.filter(or_(Course.title.ilike(like), Course.tags.ilike(like)))

    if filter_type == "free":
        courses_q = courses_q.filter(Course.price.ilike("%free%"))
    elif filter_type == "paid":
        courses_q = courses_q.filter(~Course.price.ilike("%free%"))

    if filter_type == "top":
        courses = courses_q.limit(3).all()
    else:
        courses = courses_q.all()

    scholarships = Scholarship.query.filter_by(region="India").order_by(Scholarship.id.asc()).limit(6).all()

    return render_template("dashboard.html",
                           user=session.get("user"),
                           courses=courses,
                           scholarships=scholarships,
                           query=query,
                           filter_type=filter_type)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out ✅", "info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()
    app.run(debug=True)
