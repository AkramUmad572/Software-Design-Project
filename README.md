# MotorMatch

CSCI 2040U – Software Design and Analysis  
Team: Qudsia Fawad, Andy, Emma, Umad, Adebayo

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

### Step 1: Launch the Application

Run the project using the instructions in the setup section.

![Launch Application](./screenshots/launch.png)

---

### Step 2: Create an Account / Log In

- New users can register for an account
- Existing users can log in

![Login / Register](./screenshots/login.png)

---

### Browsing Vehicle Listings

- Users can view all available vehicles
- Listings include key vehicle details

![Browse Listings](./screenshots/browse.png)

---

### Viewing Listing Details

- Users can click on a listing to view more information

![Listing Details](./screenshots/details.png)

---

### Searching for Vehicles

- Users can search for vehicles using the search feature

![Search](./screenshots/search.png)

---

### Filtering Vehicles

- Users can apply filters to narrow results

![Filter](./screenshots/filter.png)

---

## Admin Functionality

### Adding a Vehicle

- Admins can create new listings

![Add Vehicle](./screenshots/add.png)

---

### Updating a Vehicle

- Admins can edit existing listings

![Update Vehicle](./screenshots/update.png)

---

### Deleting a Vehicle

- Admins can remove listings

![Delete Vehicle](./screenshots/delete.png)

---

## Additional Features

### Wishlist

- Users can save vehicles they are interested in

![Wishlist](./screenshots/wishlist.png)

---

### Reviews

- Users can leave feedback on vehicles

![Reviews](./screenshots/reviews.png)

---

### Messaging System

- Users can interact through messaging features

![Messaging](./screenshots/messaging.png)

---

### Admin Dashboard

- Admins can manage the system from a central interface

![Dashboard](./screenshots/dashboard.png)
