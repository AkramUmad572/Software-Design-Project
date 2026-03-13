from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
import os
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('customer','admin'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
            """
        )
        # Seed some demo car listings if table is empty
        existing = conn.execute("SELECT COUNT(*) AS c FROM cars").fetchone()
        if existing["c"] == 0:
            sample_cars = [
                ("Toyota", "Camry SE", 2021, 24850, "One-owner, low mileage, full service history."),
                ("Honda", "Civic EX", 2020, 21990, "Apple CarPlay, clean interior, great on gas."),
                ("Ford", "F-150 XLT", 2019, 33950, "4x4, tow package, new all-terrain tires."),
                ("Tesla", "Model 3 Long Range", 2022, 46990, "Dual motor, Autopilot, premium interior."),
                ("BMW", "3 Series 330i", 2018, 27980, "M Sport package, sunroof, leather seats."),
                ("Hyundai", "Elantra SEL", 2021, 18990, "Balance of factory warranty, backup camera."),
                ("Mercedes-Benz", "C300", 2019, 33990, "AMG styling, panoramic roof, low miles."),
                ("Subaru", "Outback Premium", 2020, 28950, "AWD, roof rails, perfect for road trips."),
                ("Audi", "A4 Quattro", 2018, 26950, "All-wheel drive, virtual cockpit, great condition."),
                ("Chevrolet", "Tahoe LT", 2019, 45900, "7-passenger, Bose audio, heated seats."),
            ]
            conn.executemany(
                "INSERT INTO cars (make, model, year, price, description) VALUES (?, ?, ?, ?, ?)",
                sample_cars,
            )
            conn.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("pythonlogin"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("pythonlogin"))
        if session.get("role") != "admin":
            flash("You do not have permission to do that.", "error")
            return redirect(url_for("list_cars"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/")
def home():
    with get_db() as conn:
        cars = conn.execute(
            "SELECT * FROM cars ORDER BY id DESC LIMIT 8"
        ).fetchall()
    return render_template("index.html", cars=cars)


@app.route("/pythonlogin", methods=["GET", "POST"])
def pythonlogin():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        form_type = request.form.get("form_type")
        role = request.form.get("role", "customer")

        if not username or not password:
            flash("Username and password are required.", "error")
            return render_template("login.html")

        with get_db() as conn:
            if form_type == "register":
                try:
                    conn.execute(
                        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                        (username, password, role),
                    )
                    conn.commit()
                    flash("Account created. You can log in now.", "success")
                except sqlite3.IntegrityError:
                    flash("Username is already taken.", "error")
                    return render_template("login.html")
            elif form_type == "login":
                user = conn.execute(
                    "SELECT * FROM users WHERE username = ? AND password = ?",
                    (username, password),
                ).fetchone()
                if not user:
                    flash("Invalid username or password.", "error")
                    return render_template("login.html")

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for("list_cars"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/cars")
@login_required
def list_cars():
    with get_db() as conn:
        cars = conn.execute("SELECT * FROM cars").fetchall()
    return render_template("cars.html", cars=cars, role=session.get("role"))


@app.route("/cars/new", methods=["GET", "POST"])
@admin_required
def add_car():
    if request.method == "POST":
        make = request.form.get("make", "").strip()
        model = request.form.get("model", "").strip()
        year = request.form.get("year", "").strip()
        price = request.form.get("price", "").strip()
        description = request.form.get("description", "").strip()

        if not (make and model and year and price):
            flash("All fields except description are required.", "error")
            return render_template("car_form.html", mode="add")

        with get_db() as conn:
            conn.execute(
                "INSERT INTO cars (make, model, year, price, description) VALUES (?, ?, ?, ?, ?)",
                (make, model, int(year), float(price), description),
            )
            conn.commit()
        flash("Car listing added.", "success")
        return redirect(url_for("list_cars"))

    return render_template("car_form.html", mode="add")


@app.route("/cars/<int:car_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_car(car_id):
    with get_db() as conn:
        car = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
        if not car:
            flash("Car not found.", "error")
            return redirect(url_for("list_cars"))

        if request.method == "POST":
            make = request.form.get("make", "").strip()
            model = request.form.get("model", "").strip()
            year = request.form.get("year", "").strip()
            price = request.form.get("price", "").strip()
            description = request.form.get("description", "").strip()

            if not (make and model and year and price):
                flash("All fields except description are required.", "error")
                return render_template("car_form.html", mode="edit", car=car)

            conn.execute(
                """
                UPDATE cars
                SET make = ?, model = ?, year = ?, price = ?, description = ?
                WHERE id = ?
                """,
                (make, model, int(year), float(price), description, car_id),
            )
            conn.commit()
            flash("Car listing updated.", "success")
            return redirect(url_for("list_cars"))

    return render_template("car_form.html", mode="edit", car=car)


@app.route("/cars/<int:car_id>/delete", methods=["POST"])
@admin_required
def delete_car(car_id):
    with get_db() as conn:
        conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
        conn.commit()
    flash("Car listing deleted.", "success")
    return redirect(url_for("list_cars"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)