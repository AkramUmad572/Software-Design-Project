def login(client, username, password):
    return client.post(
        "/pythonlogin",
        data={
            "username": username,
            "password": password,
            "form_type": "login",
        },
        follow_redirects=True,
    )
