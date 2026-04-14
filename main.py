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
# Use environment override in production (Render), fallback for local dev.
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Gunicorn/Render imports the module but doesn't run the __main__ block.
# Ensure the schema exists before the first request.
_db_initialized = False


@app.before_request
def _ensure_db_initialized():
    global _db_initialized
    if _db_initialized:
        return
    init_db()
    _db_initialized = True


def init_db():
    """Create tables if needed, migrate older `cars` rows, seed demo listings when empty."""
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
                comment TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS wishlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                car_id INTEGER NOT NULL,
                added_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
                UNIQUE(user_id, car_id)
            )
            """
        )
        # Older DBs may lack columns added after first deploy — add them without resetting data.
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
    """Require a logged-in user; otherwise redirect to login with a flash."""

    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("pythonlogin"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    """Require login plus role admin; customers get bounced to the car list."""

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

        reviews = conn.execute(
            """SELECT r.*, u.username FROM reviews r
               JOIN users u ON r.user_id = u.id
               WHERE r.car_id = ? ORDER BY r.created_at DESC""",
            (car_id,),
        ).fetchall()

        avg_row = conn.execute(
            "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE car_id = ?",
            (car_id,),
        ).fetchone()
        avg_rating = round(avg_row["avg_rating"], 1) if avg_row["avg_rating"] else None
        review_count = avg_row["count"]

        edit_review = None
        edit_review_id = (request.args.get("edit_review") or "").strip()
        if edit_review_id:
            if session.get("role") == "admin":
                edit_review = conn.execute(
                    "SELECT * FROM reviews WHERE id = ? AND car_id = ?",
                    (int(edit_review_id), car_id),
                ).fetchone()
            else:
                edit_review = conn.execute(
                    "SELECT * FROM reviews WHERE id = ? AND car_id = ? AND user_id = ?",
                    (int(edit_review_id), car_id, session["user_id"]),
                ).fetchone()

        in_wishlist = conn.execute(
            "SELECT 1 FROM wishlist WHERE user_id = ? AND car_id = ?",
            (session["user_id"], car_id),
        ).fetchone() is not None

    return render_template(
        "car_detail.html",
        car=car,
        role=session.get("role"),
        reviews=reviews,
        avg_rating=avg_rating,
        review_count=review_count,
        edit_review=edit_review,
        in_wishlist=in_wishlist,
    )


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


@app.route("/cars/<int:car_id>/review", methods=["POST"])
@login_required
def submit_review(car_id):
    """Create a review, or update if ``review_id`` is posted (admins: any review; customers: own only)."""
    rating_raw = (request.form.get("rating", "") or "").strip()
    comment = (request.form.get("comment", "") or "").strip()
    review_id_raw = (request.form.get("review_id", "") or "").strip()

    try:
        rating = int(rating_raw)
    except ValueError:
        rating = None

    if rating is None or rating < 1 or rating > 5:
        flash("Please select a rating between 1 and 5.", "error")
        return redirect(url_for("car_detail", car_id=car_id))

    with get_db() as conn:
        if review_id_raw:
            if session.get("role") == "admin":
                updated = conn.execute(
                    "UPDATE reviews SET rating = ?, comment = ?, created_at = datetime('now') WHERE id = ? AND car_id = ?",
                    (rating, comment, int(review_id_raw), car_id),
                ).rowcount
            else:
                updated = conn.execute(
                    "UPDATE reviews SET rating = ?, comment = ?, created_at = datetime('now') WHERE id = ? AND car_id = ? AND user_id = ?",
                    (rating, comment, int(review_id_raw), car_id, session["user_id"]),
                ).rowcount
            conn.commit()
            if updated:
                flash("Your review has been updated.", "success")
            else:
                flash("Could not update that review.", "error")
            return redirect(url_for("car_detail", car_id=car_id))

        else:
            conn.execute(
                "INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
                (car_id, session["user_id"], rating, comment),
            )
            flash("Your review has been submitted.", "success")
        conn.commit()

    return redirect(url_for("car_detail", car_id=car_id))


@app.route("/cars/<int:car_id>/review/delete", methods=["POST"])
@login_required
def delete_review(car_id):
    """Delete by ``review_id``; admins any review on this car, customers only their own."""
    with get_db() as conn:
        review_id_raw = (request.form.get("review_id") or "").strip()
        if not review_id_raw:
            flash("Missing review id.", "error")
            return redirect(url_for("car_detail", car_id=car_id))

        if session.get("role") == "admin":
            conn.execute(
                "DELETE FROM reviews WHERE id = ? AND car_id = ?",
                (int(review_id_raw), car_id),
            )
        else:
            conn.execute(
                "DELETE FROM reviews WHERE id = ? AND car_id = ? AND user_id = ?",
                (int(review_id_raw), car_id, session["user_id"]),
            )
        conn.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("car_detail", car_id=car_id))


@app.route("/wishlist/toggle/<int:car_id>", methods=["POST"])
@login_required
def toggle_wishlist(car_id):
    """Add or remove this car for the current user; optional form field ``next`` for redirect."""
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM wishlist WHERE user_id = ? AND car_id = ?",
            (session["user_id"], car_id),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM wishlist WHERE id = ?", (existing["id"],))
            flash("Removed from your wishlist.", "success")
        else:
            conn.execute(
                "INSERT INTO wishlist (user_id, car_id) VALUES (?, ?)",
                (session["user_id"], car_id),
            )
            flash("Added to your wishlist!", "success")
        conn.commit()

    referrer = request.form.get("next") or request.referrer
    return redirect(referrer or url_for("list_cars"))


@app.route("/wishlist")
@login_required
def view_wishlist():
    with get_db() as conn:
        cars = conn.execute(
            """SELECT c.*, w.added_at FROM wishlist w
               JOIN cars c ON w.car_id = c.id
               WHERE w.user_id = ?
               ORDER BY w.added_at DESC""",
            (session["user_id"],),
        ).fetchall()
    return render_template("wishlist.html", cars=cars, role=session.get("role"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Aggregate stats, user list, reviews, and ranking tables for admins only."""
    with get_db() as conn:
        total_cars = conn.execute("SELECT COUNT(*) as c FROM cars").fetchone()["c"]
        approved_cars = conn.execute(
            "SELECT COUNT(*) as c FROM cars WHERE status = 'approved'"
        ).fetchone()["c"]
        hidden_cars = conn.execute(
            "SELECT COUNT(*) as c FROM cars WHERE status = 'hidden'"
        ).fetchone()["c"]

        total_users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        admin_count = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE role = 'admin'"
        ).fetchone()["c"]
        customer_count = conn.execute(
            "SELECT COUNT(*) as c FROM users WHERE role = 'customer'"
        ).fetchone()["c"]

        total_reviews = conn.execute("SELECT COUNT(*) as c FROM reviews").fetchone()["c"]

        users = conn.execute(
            "SELECT id, username, role FROM users ORDER BY id DESC"
        ).fetchall()

        recent_reviews = conn.execute(
            """SELECT r.*, u.username, c.make, c.model
               FROM reviews r
               JOIN users u ON r.user_id = u.id
               JOIN cars c ON r.car_id = c.id
               ORDER BY r.created_at DESC LIMIT 20"""
        ).fetchall()

        top_rated = conn.execute(
            """SELECT c.*, AVG(r.rating) as avg_rating, COUNT(r.id) as review_count
               FROM cars c
               JOIN reviews r ON r.car_id = c.id
               GROUP BY c.id
               HAVING review_count >= 1
               ORDER BY avg_rating DESC LIMIT 5"""
        ).fetchall()

        wishlist_stats = conn.execute(
            """SELECT c.id, c.make, c.model, COUNT(w.id) as wish_count
               FROM cars c
               JOIN wishlist w ON w.car_id = c.id
               GROUP BY c.id
               ORDER BY wish_count DESC LIMIT 5"""
        ).fetchall()

    return render_template(
        "admin_dashboard.html",
        total_cars=total_cars,
        approved_cars=approved_cars,
        hidden_cars=hidden_cars,
        total_users=total_users,
        admin_count=admin_count,
        customer_count=customer_count,
        total_reviews=total_reviews,
        users=users,
        recent_reviews=recent_reviews,
        top_rated=top_rated,
        wishlist_stats=wishlist_stats,
    )


@app.route("/admin/users/<int:user_id>/promote", methods=["POST"])
@admin_required
def promote_user_to_admin(user_id):
    """Promote a customer to admin. Only reachable by admins; UI only on dashboard."""
    if user_id == session.get("user_id"):
        flash("You are already an admin.", "error")
        return redirect(url_for("admin_dashboard"))

    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            flash("User not found.", "error")
            return redirect(url_for("admin_dashboard"))
        if row["role"] != "customer":
            flash("Only customer accounts can be promoted to admin.", "error")
            return redirect(url_for("admin_dashboard"))
        conn.execute(
            "UPDATE users SET role = 'admin' WHERE id = ? AND role = 'customer'",
            (user_id,),
        )
        conn.commit()
    flash(f"{row['username']} is now an admin.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/users/<int:user_id>/demote", methods=["POST"])
@admin_required
def demote_admin_to_customer(user_id):
    """Demote an admin to customer. Only reachable by admins; UI only on dashboard."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, username, role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            flash("User not found.", "error")
            return redirect(url_for("admin_dashboard"))
        if row["role"] != "admin":
            flash("Only admin accounts can be demoted to customer.", "error")
            return redirect(url_for("admin_dashboard"))

        admin_total = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role = 'admin'"
        ).fetchone()["c"]
        if admin_total <= 1:
            flash("There must be at least one admin. Cannot demote the only admin.", "error")
            return redirect(url_for("admin_dashboard"))

        conn.execute(
            "UPDATE users SET role = 'customer' WHERE id = ? AND role = 'admin'",
            (user_id,),
        )
        conn.commit()
    flash(f"{row['username']} is now a customer.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)