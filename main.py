from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
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
                description TEXT,
                status TEXT NOT NULL DEFAULT 'approved' CHECK (status IN ('approved','hidden')),
                image_filename TEXT
            )
            """
        )
        # For existing databases created before 'status' existed
        cols = conn.execute("PRAGMA table_info(cars)").fetchall()
        col_names = {c["name"] for c in cols}
        if "status" not in col_names:
            conn.execute("ALTER TABLE cars ADD COLUMN status TEXT NOT NULL DEFAULT 'approved'")
        if "image_filename" not in col_names:
            conn.execute("ALTER TABLE cars ADD COLUMN image_filename TEXT")
        # Seed some demo car listings if table is empty
        existing = conn.execute("SELECT COUNT(*) AS c FROM cars").fetchone()
        if existing["c"] == 0:
            sample_cars = [
                ("Honda", "CR-V", 2026, 35990, "Spacious compact SUV with advanced safety features.", "honda_crv.jpg"),
                ("Honda", "Civic", 2020, 21990, "Apple CarPlay, clean interior, great on gas.", "civic.jpg"),
                ("BMW", "M30i", 2021, 52990, "Sport-tuned performance with premium interior.", "m30i.jpg"),
                ("Mercedes-Benz", "GLB", 2020, 38990, "Luxury compact SUV with versatile seating.", "glb.jpg"),
                ("Toyota", "Camry SE", 2021, 24850, "One-owner, low mileage, full service history.", "toyota.jpg"),
                ("Ford", "F-150 XLT", 2019, 33950, "4x4, tow package, new all-terrain tires.", "ford.jpg"),
                ("Tesla", "Model 3 Long Range", 2022, 46990, "Dual motor, Autopilot, premium interior.", "tesla.jpg"),
                ("BMW", "3 Series 330i", 2018, 27980, "M Sport package, sunroof, leather seats.", "bmw.jpg"),
            ]
            conn.executemany(
                "INSERT INTO cars (make, model, year, price, description, image_filename, status) VALUES (?, ?, ?, ?, ?, ?, 'approved')",
                sample_cars,
            )
            conn.commit()


@app.route("/images/<path:filename>")
def car_image(filename):
    images_dir = os.path.join(BASE_DIR, "images")
    return send_from_directory(images_dir, filename)


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
    q = (request.args.get("q") or "").strip()
    make = (request.args.get("make") or "").strip()
    min_price = (request.args.get("min_price") or "").strip()
    max_price = (request.args.get("max_price") or "").strip()
    sort = (request.args.get("sort") or "newest").strip()

    where = []
    params = []

    # Moderation: customers see only approved listings.
    if session.get("role") != "admin":
        where.append("status = 'approved'")
    if q:
        where.append("(make LIKE ? OR model LIKE ? OR description LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])
    if make:
        where.append("make = ?")
        params.append(make)
    if min_price:
        where.append("price >= ?")
        params.append(float(min_price))
    if max_price:
        where.append("price <= ?")
        params.append(float(max_price))

    order_by = "id DESC"
    if sort == "price_asc":
        order_by = "price ASC"
    elif sort == "price_desc":
        order_by = "price DESC"
    elif sort == "year_desc":
        order_by = "year DESC"
    elif sort == "year_asc":
        order_by = "year ASC"

    sql = "SELECT * FROM cars"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {order_by}"

    with get_db() as conn:
        cars = conn.execute(sql, params).fetchall()
        makes_sql = "SELECT DISTINCT make FROM cars"
        makes_params = []
        if session.get("role") != "admin":
            makes_sql += " WHERE status = 'approved'"
        makes_sql += " ORDER BY make ASC"
        makes = conn.execute(makes_sql, makes_params).fetchall()

    return render_template(
        "cars.html",
        cars=cars,
        role=session.get("role"),
        makes=[row["make"] for row in makes],
        filters={
            "q": q,
            "make": make,
            "min_price": min_price,
            "max_price": max_price,
            "sort": sort,
        },
    )


@app.route("/cars/<int:car_id>")
@login_required
def car_detail(car_id):
    with get_db() as conn:
        if session.get("role") == "admin":
            car = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
        else:
            car = conn.execute(
                "SELECT * FROM cars WHERE id = ? AND status = 'approved'", (car_id,)
            ).fetchone()
        if not car:
            flash("Car not found.", "error")
            return redirect(url_for("list_cars"))
    return render_template("car_detail.html", car=car, role=session.get("role"))


@app.route("/cars/<int:car_id>/moderate", methods=["POST"])
@admin_required
def moderate_car(car_id):
    action = (request.form.get("action") or "").strip()
    new_status = "approved" if action == "approve" else "hidden"
    with get_db() as conn:
        conn.execute("UPDATE cars SET status = ? WHERE id = ?", (new_status, car_id))
        conn.commit()
    flash(f"Listing marked as {new_status}.", "success")
    return redirect(url_for("list_cars"))


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