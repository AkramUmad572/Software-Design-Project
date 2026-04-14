"""
System tests: wishlist workflows across multiple requests.
"""

from tests.helpers import login


def test_end_to_end_wishlist_add_from_detail_then_visible_on_wishlist_page(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    customer = app.test_client()
    login(customer, "it_customer", "pw")

    # Add from detail (simulates using the button)
    add = customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": f"/cars/{car_id}"},
        follow_redirects=True,
    )
    assert add.status_code == 200

    wishlist = customer.get("/wishlist")
    assert wishlist.status_code == 200
    assert title in wishlist.get_data(as_text=True)


def test_end_to_end_wishlist_remove_then_disappears(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    customer = app.test_client()
    login(customer, "it_customer", "pw")

    customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/wishlist"},
        follow_redirects=True,
    )
    page = customer.get("/wishlist")
    assert title in page.get_data(as_text=True)

    customer.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/wishlist"},
        follow_redirects=True,
    )
    page2 = customer.get("/wishlist")
    assert title not in page2.get_data(as_text=True)


def test_end_to_end_wishlist_is_private_between_users(
    app_with_temp_db, car_on_first_catalog_page
):
    app, _main = app_with_temp_db
    car_id, title = car_on_first_catalog_page

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    admin.post(
        f"/wishlist/toggle/{car_id}",
        data={"next": "/wishlist"},
        follow_redirects=True,
    )

    customer = app.test_client()
    login(customer, "it_customer", "pw")
    wishlist = customer.get("/wishlist")
    assert wishlist.status_code == 200
    assert title not in wishlist.get_data(as_text=True)

