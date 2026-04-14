# MotorMatch

CSCI 2040U – Software Design and Analysis  
Team: Qudsia, Andy, Emma, Umad, Adebayo

---

## Overview

MotorMatch is a vehicle catalog application that allows users to browse and search for cars, while admins can manage listings.

The system supports user account creation and login, viewing vehicle listings, and administrative actions such as adding, updating, and removing vehicles.

Additional features such as a wishlist system, reviews, an admin dashboard, and a messaging system are being integrated to enhance user interaction.

---

## Setup and Running the Application

### Clone the Repository

git clone <PASTE REPO LINK>  
cd MotorMatch

---

### Run Using PowerShell Script

.\scripts\run.ps1

This script:

- creates a virtual environment
- installs dependencies
- starts the server

---

### Alternative: Using Makefile

make install  
make run

---

### Running Tests

pytest

---

## Developer Documentation

### Project Structure Overview

The project is organized into components that handle different responsibilities:

- Routes / Controllers  
  Handle application flow and user requests

- Database / Data Layer  
  Stores and manages vehicle and user data

- Core Logic  
  Handles filtering, validation, and processing

---

### Key System Features

- User authentication with role-based access (user/admin)
- Vehicle listing management
- Search and filtering functionality
- Input validation

---

## User Documentation

- Use the demo below as a reference. <br>
https://drive.google.com/file/d/1eQTNhCsAoVl3WiIbzU_dZQ_yBmGQV-Kt/view?usp=sharing
