## Overview

MotorMatch is a prototype vehicle listings platform developed as part of our course project.

How to Run
Clone the repository: git clone [PASTE REPO LINK]

.\scripts\run.ps1

````

This script creates a virtual environment (`venv`), installs dependencies, and starts the server.

## Quick start (Makefile)

If you have `make` installed (Git Bash / WSL / MSYS2):

```bash
make install
make run
````

## Iteration 2

Install deps (includes pytest), then run:

```bash
pytest
```

Note: `tests/test_password_strength.py` is intentionally written for a _future_ feature.
Right now it should fail (“Red”) because `motormatch/auth_rules.py::password_is_strong` is not implemented yet.

## Features implemented (Iteration 1 + some Iteration 2)

- Browse vehicle catalog (with images)
- Click a listing image to view details
- Login / Register with roles (customer/admin)
- Admin-only add/edit/delete listings
