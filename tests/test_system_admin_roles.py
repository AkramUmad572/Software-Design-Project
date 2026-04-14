"""
System tests: admin promote/demote workflows across sessions.
"""

from tests.helpers import login


def test_end_to_end_admin_promotes_customer_then_customer_can_access_dashboard(
    app_with_temp_db, main_module
):
    app, _main = app_with_temp_db

    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]

    admin = app.test_client()
    login(admin, "it_admin", "pw")
    promote = admin.post(
        f"/admin/users/{cust_id}/promote",
        follow_redirects=True,
    )
    assert promote.status_code == 200

    # Customer must log in again to pick up new role into session
    customer = app.test_client()
    login(customer, "it_customer", "pw")
    dash = customer.get("/admin/dashboard", follow_redirects=False)
    assert dash.status_code == 200
    assert "Admin Dashboard" in dash.get_data(as_text=True)


def test_end_to_end_admin_demotes_admin_then_access_revoked_on_next_login(
    app_with_temp_db, main_module
):
    app, _main = app_with_temp_db

    admin = app.test_client()
    login(admin, "it_admin", "pw")

    # First promote customer so there will still be an admin after demote.
    with main_module.get_db() as conn:
        cust_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_customer",)
        ).fetchone()["id"]
    admin.post(f"/admin/users/{cust_id}/promote", follow_redirects=True)

    # Demote the original admin account.
    with main_module.get_db() as conn:
        admin_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("it_admin",)
        ).fetchone()["id"]
    demote = admin.post(
        f"/admin/users/{admin_id}/demote",
        follow_redirects=True,
    )
    assert demote.status_code == 200

    # New session login as it_admin should now be blocked from dashboard.
    old_admin = app.test_client()
    login(old_admin, "it_admin", "pw")
    resp = old_admin.get("/admin/dashboard", follow_redirects=True)
    assert "do not have permission" in resp.get_data(as_text=True).lower()

