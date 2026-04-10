"""
System tests: full HTTP workflows for listing visibility (user perspective).
"""

from tests.helpers import login


def test_end_to_end_admin_hides_listing_customer_no_longer_sees_it(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    hide = admin.post(
        f"/cars/{car_id}/moderate",
        data={"action": "hide"},
        follow_redirects=True,
    )
    assert hide.status_code == 200

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    page = customer.get("/cars")
    assert page.status_code == 200
    assert title not in page.get_data(as_text=True)


def test_end_to_end_admin_approves_listing_customer_sees_it_again(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)

    admin.post(
        f"/cars/{car_id}/moderate",
        data={"action": "approve"},
        follow_redirects=True,
    )

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    page = customer.get("/cars")
    assert page.status_code == 200
    assert title in page.get_data(as_text=True)


def test_end_to_end_customer_cannot_open_detail_of_hidden_listing(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(f"/cars/{car_id}/moderate", data={"action": "hide"}, follow_redirects=True)

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    resp = customer.get(f"/cars/{car_id}", follow_redirects=True)
    assert resp.status_code == 200
    assert title not in resp.get_data(as_text=True)
