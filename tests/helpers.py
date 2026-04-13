"""Small helpers shared across tests."""


def login(client, username, password):
    """POST to the login form (used by integration/system tests)."""
    return client.post(
        "/pythonlogin",
        data={
            "username": username,
            "password": password,
            "form_type": "login",
        },
        follow_redirects=True,
    )
