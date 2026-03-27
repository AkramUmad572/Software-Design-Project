## Overview
MotorMatch is a prototype vehicle listings platform developed as part of our course project.

## Quick start (Windows PowerShell)

```powershell
cd "C:\Users\akram\OneDrive\Desktop\Coding_Projects\Software-Design-Project"
.\scripts\run.ps1
```

This script creates a virtual environment (`venv`), installs dependencies, and starts the server.

## Quick start (Makefile)
If you have `make` installed (macOS/Linux, or Windows via Git Bash / WSL / MSYS2):

```bash
make install
make run
```

## Run unit tests (TDD / Iteration 2+)

```bash
pytest
```

Expected right now:
- Some tests pass (existing feature)
- Some tests fail (future features written TDD-first; still unimplemented)

## App URLs
- Home: `http://127.0.0.1:5000/`
- Login / Register: `http://127.0.0.1:5000/pythonlogin`
- Catalog: `http://127.0.0.1:5000/cars`

## Features implemented (Iteration 1 + some Iteration 2)
- Browse vehicle catalog (with images)
- Click a listing image to view details
- Login / Register with roles (customer/admin)
- Admin-only add/edit/delete listings
- Search/filter catalog by make + price
