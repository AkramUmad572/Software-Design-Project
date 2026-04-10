"""
Integration tests: Flask routes + SQLite + session for listing status (moderation).
"""

from tests.helpers import login


def test_moderate_hide_updates_row_in_database(
    logged_in_admin, main_module, first_approved_car
):
    car_id, _model = first_approved_car
    resp = logged_in_admin.post(
        f"/cars/{car_id}/moderate",
        data={"action": "hide"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT status FROM cars WHERE id = ?", (car_id,)
        ).fetchone()
    assert row["status"] == "hidden"


def test_moderate_approve_updates_row_in_database(
    logged_in_admin, main_module, first_approved_car
):
    car_id, _model = first_approved_car
    with main_module.get_db() as conn:
        conn.execute(
            "UPDATE cars SET status = 'hidden' WHERE id = ?", (car_id,)
        )
        conn.commit()
    logged_in_admin.post(
        f"/cars/{car_id}/moderate",
        data={"action": "approve"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT status FROM cars WHERE id = ?", (car_id,)
        ).fetchone()
    assert row["status"] == "approved"


def test_customer_catalog_excludes_hidden_car(app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    resp = customer.get("/cars")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert title not in text


def test_admin_catalog_includes_hidden_car(app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)

    resp = admin.get("/cars")
    assert resp.status_code == 200
    assert title in resp.get_data(as_text=True)
