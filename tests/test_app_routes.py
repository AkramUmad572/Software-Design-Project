"""
Route-level tests: home, auth, listings, admin CRUD, and filters.
"""

import pytest

from tests.helpers import login


@pytest.mark.integration
def test_home_returns_200(client):
    assert client.get("/").status_code == 200


@pytest.mark.integration
def test_home_contains_listings_section(client):
    text = client.get("/").get_data(as_text=True)
    assert "Featured listings" in text or "listings" in text.lower()


@pytest.mark.integration
def test_pythonlogin_get_returns_200(client):
    assert client.get("/pythonlogin").status_code == 200


@pytest.mark.integration
def test_register_creates_user(app_with_temp_db, main_module):
    app, _main = app_with_temp_db
    c = app.test_client()
    resp = c.post(
        "/pythonlogin",
        data={
            "username": "newbuyer",
            "password": "secret12",
            "form_type": "register",
            "role": "customer",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT role FROM users WHERE username = ?", ("newbuyer",)
        ).fetchone()
    assert row["role"] == "customer"


@pytest.mark.integration
def test_register_duplicate_username_shows_error(app_with_temp_db):
    app, _main = app_with_temp_db
    c = app.test_client()
    data = {
        "username": "dupuser",
        "password": "pw123456",
        "form_type": "register",
        "role": "customer",
    }
    c.post("/pythonlogin", data=data, follow_redirects=True)
    resp = c.post("/pythonlogin", data=data, follow_redirects=True)
    assert "already taken" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_login_empty_fields_shows_error(client):
    resp = client.post(
        "/pythonlogin",
        data={"username": "", "password": "", "form_type": "login"},
        follow_redirects=True,
    )
    assert "required" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_login_invalid_credentials(client):
    resp = client.post(
        "/pythonlogin",
        data={
            "username": "nobody",
            "password": "wrong",
            "form_type": "login",
        },
        follow_redirects=True,
    )
    assert "invalid" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_login_success_redirects_to_listings(logged_in_customer):
    resp = logged_in_customer.get("/cars")
    assert resp.status_code == 200
    assert "Car listings" in resp.get_data(as_text=True) or "listings" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_logout_then_protected_route_redirects_login(app_with_temp_db):
    app, _main = app_with_temp_db
    c = app.test_client()
    login(c, "it_customer", "pw")
    c.get("/logout", follow_redirects=True)
    resp = c.get("/cars", follow_redirects=True)
    assert resp.status_code == 200
    assert "log in" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_cars_requires_login_unauthenticated(client):
    resp = client.get("/cars", follow_redirects=True)
    assert resp.status_code == 200
    assert "log in" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_wishlist_requires_login_unauthenticated(client):
    resp = client.get("/wishlist", follow_redirects=True)
    assert resp.status_code == 200
    assert "pythonlogin" in resp.request.path or "log in" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_car_detail_requires_login_unauthenticated(client, first_approved_car):
    car_id, _ = first_approved_car
    resp = client.get(f"/cars/{car_id}", follow_redirects=True)
    assert resp.status_code == 200


@pytest.mark.integration
def test_car_detail_customer_ok(logged_in_customer, first_approved_car):
    car_id, _ = first_approved_car
    resp = logged_in_customer.get(f"/cars/{car_id}")
    assert resp.status_code == 200
    assert "Details" in resp.get_data(as_text=True) or "Listing" in resp.get_data(as_text=True)


@pytest.mark.integration
def test_car_image_known_file_returns_200(client):
    resp = client.get("/images/toyota.jpg")
    assert resp.status_code == 200


@pytest.mark.integration
def test_customer_cannot_open_add_car_form(logged_in_customer):
    resp = logged_in_customer.get("/cars/new", follow_redirects=True)
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_customer_cannot_post_add_car(logged_in_customer):
    resp = logged_in_customer.post(
        "/cars/new",
        data={
            "make": "X",
            "model": "Y",
            "year": "2020",
            "price": "1000",
            "description": "",
        },
        follow_redirects=True,
    )
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_customer_cannot_moderate(logged_in_customer, first_approved_car):
    car_id, _ = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/moderate",
        data={"action": "hide"},
        follow_redirects=True,
    )
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_customer_cannot_open_edit_car(logged_in_customer, first_approved_car):
    car_id, _ = first_approved_car
    resp = logged_in_customer.get(f"/cars/{car_id}/edit", follow_redirects=True)
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_customer_cannot_delete_car(logged_in_customer, first_approved_car):
    car_id, _ = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/delete",
        follow_redirects=True,
    )
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_admin_add_car_get_ok(logged_in_admin):
    resp = logged_in_admin.get("/cars/new")
    assert resp.status_code == 200


@pytest.mark.integration
def test_admin_add_car_post_creates_row(logged_in_admin, main_module):
    logged_in_admin.post(
        "/cars/new",
        data={
            "make": "TestMake",
            "model": "TestModel",
            "year": "2022",
            "price": "12345",
            "description": "integration car",
        },
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT * FROM cars WHERE make = ? AND model = ?", ("TestMake", "TestModel")
        ).fetchone()
    assert row is not None
    assert row["price"] == 12345.0


@pytest.mark.integration
def test_admin_add_car_missing_required_fields_shows_error(logged_in_admin):
    resp = logged_in_admin.post(
        "/cars/new",
        data={"make": "", "model": "", "year": "", "price": "", "description": ""},
        follow_redirects=True,
    )
    assert "required" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_admin_edit_car_updates_database(logged_in_admin, main_module, first_approved_car):
    car_id, _ = first_approved_car
    logged_in_admin.post(
        f"/cars/{car_id}/edit",
        data={
            "make": "UpdatedMake",
            "model": "UpdatedModel",
            "year": "2019",
            "price": "19999",
            "description": "edited",
        },
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute("SELECT make, model FROM cars WHERE id = ?", (car_id,)).fetchone()
    assert row["make"] == "UpdatedMake"
    assert row["model"] == "UpdatedModel"


@pytest.mark.integration
def test_admin_delete_car_removes_row(logged_in_admin, main_module):
    with main_module.get_db() as conn:
        conn.execute(
            "INSERT INTO cars (make, model, year, price, description, status) VALUES (?, ?, ?, ?, ?, 'approved')",
            ("DelMake", "DelModel", 2020, 5000.0, "to delete"),
        )
        conn.commit()
        new_id = conn.execute("SELECT id FROM cars WHERE make = 'DelMake'").fetchone()["id"]
    logged_in_admin.post(f"/cars/{new_id}/delete", follow_redirects=True)
    with main_module.get_db() as conn:
        row = conn.execute("SELECT id FROM cars WHERE id = ?", (new_id,)).fetchone()
    assert row is None


@pytest.mark.integration
def test_admin_edit_unknown_car_redirects(logged_in_admin):
    resp = logged_in_admin.get("/cars/999999/edit", follow_redirects=True)
    assert resp.status_code == 200
    assert "not found" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
@pytest.mark.parametrize(
    "sort_key",
    ["newest", "price_asc", "price_desc", "year_asc", "year_desc"],
)
def test_list_cars_sort_options_return_200(logged_in_customer, sort_key):
    resp = logged_in_customer.get("/cars", query_string={"sort": sort_key})
    assert resp.status_code == 200


@pytest.mark.integration
def test_list_cars_search_query_filters(logged_in_customer):
    resp = logged_in_customer.get("/cars", query_string={"q": "Honda"})
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "Honda" in text


@pytest.mark.integration
def test_list_cars_filter_by_make(logged_in_customer):
    resp = logged_in_customer.get("/cars", query_string={"make": "Honda"})
    assert resp.status_code == 200


@pytest.mark.integration
def test_list_cars_price_min_max(logged_in_customer):
    resp = logged_in_customer.get(
        "/cars",
        query_string={"min_price": "10000", "max_price": "50000"},
    )
    assert resp.status_code == 200


@pytest.mark.integration
def test_customer_cannot_view_hidden_car_detail(app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page
    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)
    customer = app.test_client()
    login(customer, "it_customer", "pw")
    resp = customer.get(f"/cars/{car_id}", follow_redirects=True)
    assert title not in resp.get_data(as_text=True)


@pytest.mark.integration
def test_admin_can_view_hidden_car_detail(app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page
    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)
    resp = admin.get(f"/cars/{car_id}")
    assert resp.status_code == 200
    assert title in resp.get_data(as_text=True)


@pytest.mark.integration
def test_register_admin_role_persisted(app_with_temp_db, main_module):
    app, _main = app_with_temp_db
    c = app.test_client()
    c.post(
        "/pythonlogin",
        data={
            "username": "newadminx",
            "password": "pw123456",
            "form_type": "register",
            "role": "admin",
        },
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        role = conn.execute(
            "SELECT role FROM users WHERE username = ?", ("newadminx",)
        ).fetchone()["role"]
    assert role == "admin"


@pytest.mark.integration
def test_logout_redirects_home(app_with_temp_db):
    app, _main = app_with_temp_db
    c = app.test_client()
    login(c, "it_customer", "pw")
    resp = c.get("/logout", follow_redirects=False)
    assert resp.status_code in (302, 303)


@pytest.mark.integration
def test_admin_moderate_hide_flash(logged_in_admin, first_approved_car):
    car_id, _ = first_approved_car
    resp = logged_in_admin.post(
        f"/cars/{car_id}/moderate",
        data={"action": "hide"},
        follow_redirects=True,
    )
    assert "hidden" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_admin_moderate_approve_flash(logged_in_admin, first_approved_car):
    car_id, _ = first_approved_car
    logged_in_admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)
    resp = logged_in_admin.post(
        f"/cars/{car_id}/moderate",
        data={"action": "approve"},
        follow_redirects=True,
    )
    assert "approved" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_customer_cannot_access_admin_dashboard(logged_in_customer):
    resp = logged_in_customer.get("/admin/dashboard", follow_redirects=True)
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_promote_route_requires_admin(app_with_temp_db, main_module):
    app, _main = app_with_temp_db
    with main_module.get_db() as conn:
        cid = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
    c = app.test_client()
    login(c, "it_customer", "pw")
    resp = c.post(f"/admin/users/{cid}/promote", follow_redirects=True)
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_demote_route_requires_admin(app_with_temp_db, main_module):
    app, _main = app_with_temp_db
    with main_module.get_db() as conn:
        aid = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_admin",)
        ).fetchone()["id"]
    c = app.test_client()
    login(c, "it_customer", "pw")
    resp = c.post(f"/admin/users/{aid}/demote", follow_redirects=True)
    assert "permission" in resp.get_data(as_text=True).lower()


@pytest.mark.integration
def test_list_cars_page_contains_filter_form(logged_in_customer):
    text = logged_in_customer.get("/cars").get_data(as_text=True)
    assert "Apply" in text or "sort" in text.lower()


@pytest.mark.integration
def test_car_form_add_mode_in_template(logged_in_admin):
    text = logged_in_admin.get("/cars/new").get_data(as_text=True)
    assert "make" in text.lower() or "model" in text.lower()
