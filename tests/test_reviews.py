import pytest


def _create_review(main_module, car_id, user_id, rating, comment="", created_at="datetime('now')"):
    with main_module.get_db() as conn:
        conn.execute(
            f"INSERT INTO reviews (car_id, user_id, rating, comment, created_at) VALUES (?, ?, ?, ?, {created_at})",
            (car_id, user_id, rating, comment),
        )
        conn.commit()


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_missing_rating_rejected(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"comment": "no rating"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Please select a rating between 1 and 5" in resp.get_data(as_text=True)


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_rating_out_of_range_rejected(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    before = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "6", "comment": "too high"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    after = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    assert after == before


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_edit_updates_correct_row(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "initial"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
        review_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
            (car_id, user_id),
        ).fetchone()["id"]

    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"review_id": str(review_id), "rating": "2", "comment": "edited"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute("SELECT rating, comment FROM reviews WHERE id = ?", (review_id,)).fetchone()
    assert row["rating"] == 2
    assert row["comment"] == "edited"


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_customer_cannot_edit_others_review(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    with main_module.get_db() as conn:
        admin_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_admin",)
        ).fetchone()["id"]
        _create_review(main_module, car_id, admin_id, 5, "admin review")
        victim_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
            (car_id, admin_id),
        ).fetchone()["id"]

    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"review_id": str(victim_id), "rating": "1", "comment": "hijack"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Could not update that review" in resp.get_data(as_text=True)
    with main_module.get_db() as conn:
        row = conn.execute("SELECT rating, comment FROM reviews WHERE id = ?", (victim_id,)).fetchone()
    assert row["rating"] == 5
    assert row["comment"] == "admin review"


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_delete_requires_review_id(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review/delete",
        data={},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Missing review id" in resp.get_data(as_text=True)


@pytest.mark.reviews
@pytest.mark.tb
@pytest.mark.parametrize("rating", [1, 2, 3, 4, 5])
def test_reviews_tb_valid_ratings_insert(logged_in_customer, first_approved_car, main_module, rating):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": str(rating), "comment": f"r{rating}"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with main_module.get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ? AND comment = ?",
            (car_id, f"r{rating}"),
        ).fetchone()["c"]
    assert count == 1


@pytest.mark.reviews
@pytest.mark.tb
@pytest.mark.parametrize("bad", [0, 6, -1, 999])
def test_reviews_tb_invalid_ratings_rejected(logged_in_customer, first_approved_car, main_module, bad):
    car_id, _model = first_approved_car
    before = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": str(bad), "comment": "bad"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    after = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    assert after == before


@pytest.mark.reviews
@pytest.mark.tb
def test_reviews_tb_non_integer_rating_rejected(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    before = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "abc", "comment": "bad"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    after = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    assert after == before


@pytest.mark.reviews
@pytest.mark.tb
@pytest.mark.parametrize("comment", ["", "x" * 2000])
def test_reviews_tb_comment_equivalence_classes(logged_in_customer, first_approved_car, main_module, comment):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "5", "comment": comment},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with main_module.get_db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ? AND user_id = (SELECT id FROM users WHERE username = ?)",
            (car_id, "it_customer"),
        ).fetchone()["c"]
    assert count >= 1


@pytest.mark.reviews
@pytest.mark.tb
def test_reviews_tb_multiple_reviews_same_user_increases_count(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    with main_module.get_db() as conn:
        before = conn.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ? AND user_id = (SELECT id FROM users WHERE username = ?)",
            (car_id, "it_customer"),
        ).fetchone()["c"]
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "3", "comment": "one"},
        follow_redirects=True,
    )
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "two"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        after = conn.execute(
            "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ? AND user_id = (SELECT id FROM users WHERE username = ?)",
            (car_id, "it_customer"),
        ).fetchone()["c"]
    assert after == before + 2


@pytest.mark.reviews
@pytest.mark.tb
def test_reviews_tb_newest_first_ordering(main_module, app_with_temp_db, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
    _create_review(main_module, car_id, cust_id, 5, "older", created_at="'2000-01-01 00:00:00'")
    _create_review(main_module, car_id, cust_id, 5, "newer", created_at="'2100-01-01 00:00:00'")
    client = app.test_client()
    from tests.helpers import login

    login(client, "it_customer", "pw")
    # Assert ordering at the data layer (deterministic, not affected by page layout).
    with main_module.get_db() as conn:
        rows = conn.execute(
            "SELECT comment FROM reviews WHERE car_id = ? ORDER BY created_at DESC",
            (car_id,),
        ).fetchall()
    comments = [r["comment"] for r in rows]
    assert comments[:2] == ["newer", "older"]


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_post_review_appears_on_detail(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "5", "comment": "great"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "great" in text
    assert "it_customer" in text


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_edit_link_prefills_form(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "prefill me"},
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

    page = logged_in_customer.get(f"/cars/{car_id}?edit_review={review_id}#reviews")
    text = page.get_data(as_text=True)
    assert "prefill me" in text
    assert f'name=\"review_id\" value=\"{review_id}\"' in text


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_admin_can_remove_other_users_review(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    with main_module.get_db() as conn:
        admin_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_admin",)
        ).fetchone()["id"]
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
    _create_review(main_module, car_id, cust_id, 2, "remove-me")
    with main_module.get_db() as conn:
        review_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
            (car_id, cust_id),
        ).fetchone()["id"]

    admin = app.test_client()
    from tests.helpers import login

    login(admin, "it_admin", "pw")
    resp = admin.post(
        f"/cars/{car_id}/review/delete",
        data={"review_id": str(review_id)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "remove-me" not in resp.get_data(as_text=True)


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_review_count_updates(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "5", "comment": "one"},
        follow_redirects=True,
    )
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "two"},
        follow_redirects=True,
    )
    page = logged_in_customer.get(f"/cars/{car_id}")
    text = page.get_data(as_text=True)
    assert "Customer Reviews (" in text


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_customer_cannot_delete_others_review(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    with main_module.get_db() as conn:
        admin_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_admin",)
        ).fetchone()["id"]
    _create_review(main_module, car_id, admin_id, 4, "do-not-delete")
    with main_module.get_db() as conn:
        victim_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? AND user_id = ? ORDER BY id DESC LIMIT 1",
            (car_id, admin_id),
        ).fetchone()["id"]

    logged_in_customer.post(
        f"/cars/{car_id}/review/delete",
        data={"review_id": str(victim_id)},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        still = conn.execute("SELECT COUNT(*) AS c FROM reviews WHERE id = ?", (victim_id,)).fetchone()["c"]
    assert still == 1


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_edit_nonexistent_review_id_rejected(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"review_id": "999999", "rating": "2", "comment": "nope"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Could not update that review" in resp.get_data(as_text=True)


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_admin_can_edit_customer_review(app_with_temp_db, main_module, car_on_first_catalog_page):
    app, _main = app_with_temp_db
    car_id, _title = car_on_first_catalog_page
    from tests.helpers import login

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "3", "comment": "from customer"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        review_id = conn.execute(
            """SELECT id FROM reviews WHERE car_id = ?
               AND user_id = (SELECT id FROM users WHERE username = 'it_customer')
               ORDER BY id DESC LIMIT 1""",
            (car_id,),
        ).fetchone()["id"]

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(
        f"/cars/{car_id}/review",
        data={"review_id": str(review_id), "rating": "5", "comment": "admin revised"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute("SELECT rating, comment FROM reviews WHERE id = ?", (review_id,)).fetchone()
    assert row["rating"] == 5
    assert row["comment"] == "admin revised"


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_edit_review_must_match_car_in_url(logged_in_customer, main_module):
    with main_module.get_db() as conn:
        rows = conn.execute(
            "SELECT id FROM cars WHERE status = 'approved' ORDER BY id LIMIT 2"
        ).fetchall()
    assert len(rows) >= 2
    car_a, car_b = rows[0]["id"], rows[1]["id"]

    logged_in_customer.post(
        f"/cars/{car_a}/review",
        data={"rating": "5", "comment": "only-on-a"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        review_id = conn.execute(
            "SELECT id FROM reviews WHERE car_id = ? ORDER BY id DESC LIMIT 1", (car_a,)
        ).fetchone()["id"]

    logged_in_customer.post(
        f"/cars/{car_b}/review",
        data={"review_id": str(review_id), "rating": "1", "comment": "wrong-car"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute("SELECT rating, comment FROM reviews WHERE id = ?", (review_id,)).fetchone()
    assert row["rating"] == 5
    assert row["comment"] == "only-on-a"


@pytest.mark.reviews
@pytest.mark.cb
def test_reviews_cb_review_endpoint_post_only(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.get(f"/cars/{car_id}/review")
    assert resp.status_code == 405


@pytest.mark.reviews
@pytest.mark.tb
@pytest.mark.parametrize("bad", ["4.2", "3.0", "5e0"])
def test_reviews_tb_decimal_scientific_rating_rejected(
    logged_in_customer, first_approved_car, main_module, bad
):
    car_id, _model = first_approved_car
    before = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": bad, "comment": "bad-num"},
        follow_redirects=True,
    )
    after = main_module.get_db().execute(
        "SELECT COUNT(*) AS c FROM reviews WHERE car_id = ?", (car_id,)
    ).fetchone()["c"]
    assert after == before


@pytest.mark.reviews
@pytest.mark.tb
def test_reviews_tb_leading_zero_rating_accepted(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "04", "comment": "leading-zero"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT rating FROM reviews WHERE car_id = ? AND comment = ?", (car_id, "leading-zero")
        ).fetchone()
    assert row["rating"] == 4


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_delete_own_review_removes_row(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "to-delete"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        review_id = conn.execute(
            """SELECT id FROM reviews WHERE car_id = ?
               AND user_id = (SELECT id FROM users WHERE username = 'it_customer')
               ORDER BY id DESC LIMIT 1""",
            (car_id,),
        ).fetchone()["id"]

    logged_in_customer.post(
        f"/cars/{car_id}/review/delete",
        data={"review_id": str(review_id)},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        n = conn.execute("SELECT COUNT(*) AS c FROM reviews WHERE id = ?", (review_id,)).fetchone()["c"]
    assert n == 0


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_success_flash_on_create(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "5", "comment": "flash-create"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Your review has been submitted" in resp.get_data(as_text=True)


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_success_flash_on_update(logged_in_customer, first_approved_car, main_module):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "2", "comment": "before"},
        follow_redirects=True,
    )
    with main_module.get_db() as conn:
        review_id = conn.execute(
            """SELECT id FROM reviews WHERE car_id = ?
               AND user_id = (SELECT id FROM users WHERE username = 'it_customer')
               ORDER BY id DESC LIMIT 1""",
            (car_id,),
        ).fetchone()["id"]

    resp = logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"review_id": str(review_id), "rating": "3", "comment": "after"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "Your review has been updated" in resp.get_data(as_text=True)


@pytest.mark.reviews
@pytest.mark.ob
def test_reviews_ob_average_rating_rendered_on_detail(logged_in_customer, first_approved_car):
    car_id, _model = first_approved_car
    logged_in_customer.post(
        f"/cars/{car_id}/review",
        data={"rating": "4", "comment": "avg-check"},
        follow_redirects=True,
    )
    page = logged_in_customer.get(f"/cars/{car_id}")
    text = page.get_data(as_text=True)
    assert "rating-num" in text
    assert "4.0" in text
