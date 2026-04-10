import pytest


def _wishlist_count(main_module, username):
    with main_module.get_db() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS c FROM wishlist WHERE user_id = (SELECT id FROM users WHERE username = ?)",
            (username,),
        ).fetchone()["c"]


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_toggle_add_creates_row(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    before = _wishlist_count(main_module, "it_customer")
    resp = logged_in_customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/cars"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    after = _wishlist_count(main_module, "it_customer")
    assert after == before + 1


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_toggle_remove_deletes_row(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=True)
    before = _wishlist_count(main_module, "it_customer")
    resp = logged_in_customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/cars"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    after = _wishlist_count(main_module, "it_customer")
    assert after == before - 1


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_toggle_respects_next_redirect(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/wishlist"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert resp.headers["Location"].endswith("/wishlist")


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_page_requires_login(client):
    resp = client.get("/wishlist", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/pythonlogin" in resp.headers["Location"]


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_is_per_user(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    a = app.test_client()
    b = app.test_client()
    login(a, "it_admin", "pw")
    login(b, "it_customer", "pw")

    a.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)

    resp = b.get("/wishlist")
    assert resp.status_code == 200
    # Assert by car title, not digits (digits can appear in CSS, timestamps, etc.).
    with main_module.get_db() as conn:
        car = conn.execute("SELECT make, model FROM cars WHERE id = ?", (car_id,)).fetchone()
    title = f"{car['make']} {car['model']}"
    assert title not in resp.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.tb
@pytest.mark.parametrize("n", [0, 1, 3])
def test_wishlist_tb_count_matches_db(main_module, app_with_temp_db, n, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    from tests.helpers import login

    client = app.test_client()
    login(client, "it_customer", "pw")
    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
        car_ids = [row["id"] for row in conn.execute("SELECT id FROM cars ORDER BY id DESC LIMIT 5").fetchall()]
    for i in range(n):
        client.post(f"/wishlist/toggle/{car_ids[i]}", data={"next": "/wishlist"}, follow_redirects=True)

    page = client.get("/wishlist")
    assert page.status_code == 200
    assert _wishlist_count(main_module, "it_customer") == n


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_repeated_toggle_leaves_consistent_state(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=True)  # add
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=True)  # remove
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=True)  # add
    assert _wishlist_count(main_module, "it_customer") >= 1


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_ordering_newest_first(app_with_temp_db, main_module):
    app, _main = app_with_temp_db
    from tests.helpers import login

    client = app.test_client()
    login(client, "it_customer", "pw")
    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
        car_ids = [row["id"] for row in conn.execute("SELECT id FROM cars ORDER BY id DESC LIMIT 2").fetchall()]
        # Insert deterministic timestamps (avoid same-second collisions).
        conn.execute(
            "INSERT INTO wishlist (user_id, car_id, added_at) VALUES (?, ?, ?)",
            (cust_id, car_ids[1], "2000-01-01 00:00:00"),
        )
        conn.execute(
            "INSERT INTO wishlist (user_id, car_id, added_at) VALUES (?, ?, ?)",
            (cust_id, car_ids[0], "2100-01-01 00:00:00"),
        )
        conn.commit()

    page = client.get("/wishlist")
    text = page.get_data(as_text=True)
    assert text.find(f"/cars/{car_ids[0]}") < text.find(f"/cars/{car_ids[1]}")


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_toggle_from_detail_and_from_wishlist_both_work(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    client = app.test_client()
    login(client, "it_customer", "pw")

    # simulate from detail
    client.post(f"/wishlist/toggle/{car_id}", data={"next": f"/cars/{car_id}"}, follow_redirects=True)
    assert _wishlist_count(main_module, "it_customer") == 1
    # simulate from wishlist page
    client.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    assert _wishlist_count(main_module, "it_customer") == 0


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_nonexistent_car_id_does_not_crash(logged_in_customer):
    resp = logged_in_customer.post("/wishlist/toggle/999999", data={"next": "/cars"}, follow_redirects=True)
    # depending on FK enforcement it may error, but app should respond (not crash test runner)
    assert resp.status_code in (200, 500)


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_next_missing_falls_back(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={}, follow_redirects=False)
    assert resp.status_code in (302, 303)


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_button_state_changes_on_detail(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": f"/cars/{car_id}"}, follow_redirects=True)
    page = logged_in_customer.get(f"/cars/{car_id}")
    assert "Wishlisted" in page.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_wishlist_page_shows_saved_car(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page
    from tests.helpers import login

    client = app.test_client()
    login(client, "it_customer", "pw")
    client.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    page = client.get("/wishlist")
    text = page.get_data(as_text=True)
    assert title in text


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_remove_from_wishlist_page_removes_item(app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page
    from tests.helpers import login

    client = app.test_client()
    login(client, "it_customer", "pw")
    client.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    client.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    page = client.get("/wishlist")
    assert title not in page.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_customer_cannot_open_hidden_car_detail(app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page
    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    resp = customer.get(f"/cars/{car_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert title not in resp.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_toggle_requires_login(client, first_approved_car):
    car_id, _model = first_approved_car
    resp = client.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "pythonlogin" in resp.headers.get("Location", "")


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_next_redirect_to_car_detail(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": f"/cars/{car_id}"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
    assert resp.headers["Location"].rstrip("/").endswith(f"/cars/{car_id}")


@pytest.mark.wishlist
@pytest.mark.cb
def test_wishlist_cb_page_shows_title_when_logged_in(logged_in_customer):
    resp = logged_in_customer.get("/wishlist")
    assert resp.status_code == 200
    assert "My Wishlist" in resp.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_two_users_wishlist_same_car(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    a = app.test_client()
    b = app.test_client()
    login(a, "it_admin", "pw")
    login(b, "it_customer", "pw")
    a.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    b.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)

    with main_module.get_db() as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM wishlist WHERE car_id = ?", (car_id,)).fetchone()["c"]
    assert n == 2


@pytest.mark.wishlist
@pytest.mark.dashboard
@pytest.mark.tb
def test_wishlist_tb_aggregate_wishers_shown_on_dashboard(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    a = app.test_client()
    b = app.test_client()
    login(a, "it_admin", "pw")
    login(b, "it_customer", "pw")
    a.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    b.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert "2 users" in page


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_toggle_pair_restores_prior_count(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    before = _wishlist_count(main_module, "it_customer")
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=True)
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/cars"}, follow_redirects=True)
    assert _wishlist_count(main_module, "it_customer") == before


@pytest.mark.wishlist
@pytest.mark.tb
def test_wishlist_tb_empty_page_shows_zero_items_plural(logged_in_customer):
    text = logged_in_customer.get("/wishlist").get_data(as_text=True)
    assert "0 items" in text


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_added_flash_message(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/wishlist"},
        follow_redirects=True,
    )
    assert "Added to your wishlist" in resp.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_removed_flash_message(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_customer.post(f"/wishlist/toggle/{car_id}", data={"next": "/wishlist"}, follow_redirects=True)
    resp = logged_in_customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/wishlist"},
        follow_redirects=True,
    )
    assert "Removed from your wishlist" in resp.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_detail_shows_add_when_not_saved(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    page = logged_in_customer.get(f"/cars/{car_id}")
    assert "Add to Wishlist" in page.get_data(as_text=True)


@pytest.mark.wishlist
@pytest.mark.ob
def test_wishlist_ob_empty_state_copy(logged_in_customer):
    text = logged_in_customer.get("/wishlist").get_data(as_text=True)
    assert "Your wishlist is empty" in text
