from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- Database Config ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skolarai.db"
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
    title = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(100))
    rating = db.Column(db.String(20))
    price = db.Column(db.String(50))
    url = db.Column(db.String(300))
    tags = db.Column(db.String(200))
    region = db.Column(db.String(50), default="India")
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)


class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    provider = db.Column(db.String(100))
    eligibility = db.Column(db.String(200))
    deadline = db.Column(db.String(100))
    url = db.Column(db.String(300))
    tags = db.Column(db.String(200))
    region = db.Column(db.String(50), default="India")
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)


# --- Auto-Seed Function ---
def seed_data():
    if Course.query.count() == 0 and Scholarship.query.count() == 0:
        print("🌱 Seeding database with sample data...")

        courses = [
            Course(
                title="Python for Data Science",
                provider="Coursera",
                rating="4.8",
                price="Free",
                url="https://www.coursera.org/learn/python-for-data-science",
                tags="AI, Data Science"
            ),
            Course(
                title="AI & Machine Learning Bootcamp",
                provider="Udemy",
                rating="4.6",
                price="₹499",
                url="https://www.udemy.com/course/ai-and-machine-learning-bootcamp",
                tags="AI, ML"
            ),
            Course(
                title="Full Stack Web Development",
                provider="edX",
                rating="4.7",
                price="Free",
                url="https://www.edx.org/learn/web-development",
                tags="Web Development"
            )
        ]

        scholarships = [
            Scholarship(
                title="Central Sector Scholarship",
                provider="Govt. of India",
                eligibility="UG Students",
                deadline="31-12-2024",
                url="https://scholarships.gov.in",
                tags="Government, India"
            ),
            Scholarship(
                title="Tata Trust Scholarship",
                provider="Tata Trust",
                eligibility="Engineering UG",
                deadline="30-09-2024",
                url="https://www.tatatrusts.org",
                tags="Private, India"
            ),
            Scholarship(
                title="Sahu Jain Trust Scholarship",
                provider="Sahu Jain Trust",
                eligibility="UG & PG Students",
                deadline="15-08-2024",
                url="http://sahujaintrust.timesofindia.com/",
                tags="Private, India"
            )
        ]

        db.session.add_all(courses + scholarships)
        db.session.commit()
        print("✅ Seeding completed!")


# --- Routes ---
@app.route("/")
def home():
    # If logged in, go to dashboard directly
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match ❌", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully 🎉 Please sign in.", "success")
            return redirect(url_for("signin"))
        except:
            flash("Username or email already exists ❌", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

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


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        flash("Please sign in to access the dashboard ⚠️", "warning")
        return redirect(url_for("signin"))

    query = request.args.get("q", "")  # search term
    filter_type = request.args.get("filter", "all")  # all, free, paid

    courses_query = Course.query.filter_by(region="India")

    # Search by title or tags
    if query:
        courses_query = courses_query.filter(
            (Course.title.ilike(f"%{query}%")) | (Course.tags.ilike(f"%{query}%"))
        )

    # Apply filter
    if filter_type == "free":
        courses_query = courses_query.filter(Course.price.ilike("%free%"))
    elif filter_type == "paid":
        courses_query = courses_query.filter(Course.price.notilike("%free%"))

    courses = courses_query.all()
    scholarships = Scholarship.query.filter_by(region="India").limit(6).all()

    return render_template(
        "dashboard.html",
        user=session["user"],
        courses=courses,
        scholarships=scholarships,
        query=query,
        filter_type=filter_type
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out ✅", "info")
    return redirect(url_for("home"))  # Redirect to landing page


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_data()  # <-- Auto-seed on first run
    app.run(debug=True)
