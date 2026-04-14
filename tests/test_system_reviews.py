"""
System tests: review workflows across multiple requests.
"""

from tests.helpers import login


def test_end_to_end_customer_posts_review_then_sees_it_on_detail(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page

    customer = app.test_client()
    login(customer, "it_customer", "pw")

    post = customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "5", "comment": "system_review_1"},
        follow_redirects=True,
    )
    assert post.status_code == 200
    assert "system_review_1" in post.get_data(as_text=True)

    page = customer.get(f"/cars/{car_id}")
    assert "system_review_1" in page.get_data(as_text=True)


def test_end_to_end_customer_edits_review_via_edit_link(
    app_with_temp_db, main_module, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page

    customer = app.test_client()
    login(customer, "it_customer", "pw")

    customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "system_review_edit_me"},
        follow_redirects=True,
    )

    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
        review_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
            (car_id, cust_id),
        ).fetchone()["id"]

    # Load edit form and submit update
    page = customer.get(f"/cars/{car_id}?edit_review={review_id}#reviews")
    assert "system_review_edit_me" in page.get_data(as_text=True)

    updated = customer.post(
        f"/cars/{car_id}/review",
        data={"review_id": str(review_id), "rating": "2", "comment": "system_review_edited"},
        follow_redirects=True,
    )
    assert updated.status_code == 200
    assert "system_review_edited" in updated.get_data(as_text=True)


def test_end_to_end_admin_removes_customer_review(
    app_with_temp_db, main_module, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "1", "comment": "system_remove_me"},
        follow_redirects=True,
    )

    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
        review_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
            (car_id, cust_id),
        ).fetchone()["id"]

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    removed = admin.post(
        f"/cars/{car_id}/review/delete",
        data={"review_id": str(review_id)},
        follow_redirects=True,
    )
    assert removed.status_code == 200
    assert "system_remove_me" not in removed.get_data(as_text=True)

