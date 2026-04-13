"""Pytest fixtures: isolated SQLite DB, Flask client, and seeded it_admin / it_customer users."""

import os
import tempfile

import pytest

from tests.helpers import login as flask_login


@pytest.fixture
def app_with_temp_db():
    import main

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        os.unlink(path)
    except OSError:
        pass

    main.DB_PATH = path
    main.init_db()

    main.app.config["TESTING"] = True

    with main.get_db() as conn:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("it_admin", "pw", "admin"),
        )
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("it_customer", "pw", "customer"),
        )
        conn.commit()

    yield main.app, main

    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def client(app_with_temp_db):
    app, _main = app_with_temp_db
    return app.test_client()


@pytest.fixture
def main_module(app_with_temp_db):
    _app, main = app_with_temp_db
    return main


@pytest.fixture
def logged_in_admin(client):
    flask_login(client, "it_admin", "pw")
    return client


@pytest.fixture
def logged_in_customer(client):
    flask_login(client, "it_customer", "pw")
    return client


@pytest.fixture
def first_approved_car(main_module):
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT id, model FROM cars WHERE status = 'approved' ORDER BY id LIMIT 1"
        ).fetchone()
    assert row is not None
    return row["id"], row["model"]


@pytest.fixture
def car_on_first_catalog_page(main_module):
    """Newest seeded car (highest id) — stable target for listing/detail/moderation tests."""
    with main_module.get_db() as conn:
        row = conn.execute(
            "SELECT id, make, model FROM cars ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row is not None
    title = f'{row["make"]} {row["model"]}'
    return row["id"], title
