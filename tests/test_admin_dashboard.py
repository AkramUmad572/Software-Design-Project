import pytest


def _seed_reviews(main_module, car_id, user_id, n):
    with main_module.get_db() as conn:
        for i in range(n):
            conn.execute(
                "INSERT INTO reviews (car_id, user_id, rating, comment, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (car_id, user_id, (i % 5) + 1, f"c{i}"),
            )
        conn.commit()


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_customer_blocked(logged_in_customer):
    resp = logged_in_customer.get("/admin/dashboard", follow_redirects=True)
    assert resp.status_code == 200
    assert "do not have permission" in resp.get_data(as_text=True).lower()


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_admin_can_access(logged_in_admin):
    resp = logged_in_admin.get("/admin/dashboard")
    assert resp.status_code == 200
    assert "Admin Dashboard" in resp.get_data(as_text=True)


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_total_cars_matches_db(logged_in_admin, main_module):
    with main_module.get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM cars").fetchone()["c"]
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert str(total) in page


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_approved_hidden_counts_correct(logged_in_admin, main_module, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)
    with main_module.get_db() as conn:
        approved = conn.execute(
            "SELECT COUNT(*) AS c FROM cars WHERE status='approved'"
        ).fetchone()["c"]
        hidden = conn.execute(
            "SELECT COUNT(*) AS c FROM cars WHERE status='hidden'"
        ).fetchone()["c"]
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert str(approved) in page
    assert str(hidden) in page


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_user_counts_match_db(logged_in_admin, main_module):
    with main_module.get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        admins = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin'").fetchone()["c"]
        customers = conn.execute("SELECT COUNT(*) AS c FROM users WHERE role='customer'").fetchone()["c"]
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert str(total_users) in page
    assert str(admins) in page
    assert str(customers) in page


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_top_rated_ordering(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    with main_module.get_db() as conn:
        other_car = conn.execute("SELECT id FROM cars WHERE id != ? ORDER BY id DESC LIMIT 1", (car_id,)).fetchone()
        admin_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_admin",)).fetchone()["id"]

    # car_id avg=5, other avg=1
    with main_module.get_db() as conn:
        conn.execute("INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, 5, 'a')", (car_id, admin_id))
        conn.execute("INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, 1, 'b')", (other_car["id"], admin_id))
        conn.commit()

    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert page.find(f"/cars/{car_id}") < page.find(f"/cars/{other_car['id']}")


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_most_wishlisted_ordering(app_with_temp_db, main_module):
    app, _main = app_with_temp_db
    with main_module.get_db() as conn:
        cars = [row["id"] for row in conn.execute("SELECT id FROM cars ORDER BY id DESC LIMIT 2").fetchall()]
        admin_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_admin",)).fetchone()["id"]
        cust_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_customer",)).fetchone()["id"]
        # cars[0] wishlisted twice, cars[1] once
        conn.execute("INSERT INTO wishlist (user_id, car_id) VALUES (?, ?)", (admin_id, cars[0]))
        conn.execute("INSERT INTO wishlist (user_id, car_id) VALUES (?, ?)", (cust_id, cars[0]))
        conn.execute("INSERT INTO wishlist (user_id, car_id) VALUES (?, ?)", (cust_id, cars[1]))
        conn.commit()

    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert page.find(f"/cars/{cars[0]}") < page.find(f"/cars/{cars[1]}")


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_recent_reviews_limited_to_20(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    with main_module.get_db() as conn:
        cust_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_customer",)).fetchone()["id"]
    _seed_reviews(main_module, car_id, cust_id, 25)

    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert page.count("c") >= 20  # at least shows many comments


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_no_reviews_state(app_with_temp_db):
    app, _main = app_with_temp_db
    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert "No reviews yet" in page or "No reviews have been submitted yet" in page


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_no_wishlist_state(app_with_temp_db):
    app, _main = app_with_temp_db
    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert "No wishlist activity yet" in page


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_mixed_data_does_not_error(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    with main_module.get_db() as conn:
        cust_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_customer",)).fetchone()["id"]
    _seed_reviews(main_module, car_id, cust_id, 3)

    from tests.helpers import login

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    resp = admin.get("/admin/dashboard")
    assert resp.status_code == 200


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_contains_section_headings(logged_in_admin):
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert "Top Rated Cars" in page
    assert "Most Wishlisted" in page
    assert "All Users" in page
    assert "Recent Reviews" in page


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_user_table_shows_users(logged_in_admin):
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert "it_admin" in page
    assert "it_customer" in page


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_contains_car_links(logged_in_admin, first_approved_car):
    car_id, _model = first_approved_car
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    # appears in top rated only if it has a review; so seed one by posting a review first
    logged_in_admin.post(f"/cars/{car_id}/review", data={"rating": "5", "comment": "x"}, follow_redirects=True)
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert f"/cars/{car_id}" in page


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_counts_update_after_hide(logged_in_admin, main_module, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)
    with main_module.get_db() as conn:
        hidden = conn.execute("SELECT COUNT(*) AS c FROM cars WHERE status='hidden'").fetchone()["c"]
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert str(hidden) in page


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_unauthenticated_redirects_to_login(client):
    resp = client.get("/admin/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "pythonlogin" in resp.headers.get("Location", "")


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_total_reviews_stat_matches_db(logged_in_admin, main_module):
    with main_module.get_db() as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM reviews").fetchone()["c"]
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert "Total Reviews" in page
    assert str(n) in page


@pytest.mark.dashboard
@pytest.mark.cb
def test_dashboard_cb_customer_redirects_to_catalog(logged_in_customer):
    resp = logged_in_customer.get("/admin/dashboard", follow_redirects=False)
    assert resp.status_code in (302, 303)
    loc = resp.headers.get("Location", "")
    assert "/cars" in loc


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_top_rated_shows_computed_average(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    with main_module.get_db() as conn:
        admin_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_admin",)).fetchone()["id"]
        conn.execute(
            "INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, 5, 'hi')",
            (car_id, admin_id),
        )
        conn.execute(
            "INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, 3, 'lo')",
            (car_id, admin_id),
        )
        conn.commit()

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert "4.0" in page


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_recent_reviews_newest_first(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    with main_module.get_db() as conn:
        cust_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_customer",)).fetchone()["id"]
        conn.execute(
            """INSERT INTO reviews (car_id, user_id, rating, comment, created_at)
               VALUES (?, ?, 5, 'older-dash', '2000-01-01 00:00:00')""",
            (car_id, cust_id),
        )
        conn.execute(
            """INSERT INTO reviews (car_id, user_id, rating, comment, created_at)
               VALUES (?, ?, 5, 'newer-dash', '2099-01-01 00:00:00')""",
            (car_id, cust_id),
        )
        conn.commit()

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert page.find("newer-dash") < page.find("older-dash")


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_wishlist_singular_user_label(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    with main_module.get_db() as conn:
        cust_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_customer",)).fetchone()["id"]
        conn.execute("INSERT INTO wishlist (user_id, car_id) VALUES (?, ?)", (cust_id, car_id))
        conn.commit()

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert "1 user" in page
    assert "1 users" not in page


@pytest.mark.dashboard
@pytest.mark.tb
def test_dashboard_tb_total_listings_includes_hidden(logged_in_admin, main_module, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)
    with main_module.get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM cars").fetchone()["c"]
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert "Total Listings" in page
    assert str(total) in page


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_recent_review_comment_visible(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    with main_module.get_db() as conn:
        cust_id = conn.execute("SELECT id FROM users WHERE username = ?", ("it_customer",)).fetchone()["id"]
        conn.execute(
            "INSERT INTO reviews (car_id, user_id, rating, comment) VALUES (?, ?, 5, 'unique_dash_comment_q')",
            (car_id, cust_id),
        )
        conn.commit()

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    page = admin.get("/admin/dashboard").get_data(as_text=True)
    assert "unique_dash_comment_q" in page


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_total_reviews_subtitle_copy(logged_in_admin):
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert "Across all listings" in page


@pytest.mark.dashboard
@pytest.mark.ob
def test_dashboard_ob_top_rated_table_headers(logged_in_admin, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_admin.post(
        f"/cars/{car_id}/review",
        data={"rating": "5", "comment": "seed-top"},
        follow_redirects=True,
    )
    page = logged_in_admin.get("/admin/dashboard").get_data(as_text=True)
    assert "Avg Rating" in page
    assert "Reviews" in page
