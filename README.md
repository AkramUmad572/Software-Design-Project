# MotorMatch

MotorMatch is a vehicle catalog web application that allows users to browse, search, and interact with vehicle listings, while administrators can manage listings through administrative controls. The project was developed as part of a software design course and focuses on providing a structured and user-friendly platform for viewing and managing car listings.

## Overview
MotorMatch supports user account creation and login, vehicle browsing, detailed listing pages, and admin-side listing management. The system also includes features such as filtering, a wishlist system, reviews, an admin dashboard, and messaging functionality to improve user interaction and usability. The system is designed to clearly separate regular user functionality from administrative controls while maintaining a simple and organized interface.

## Setup and Running the Application
To run the application, clone the repository and navigate into the project directory:

git clone https://github.com/AkramUmad572/Software-Design-Project.git  
cd Software-Design-Project  

It is recommended to use a virtual environment. On Windows, run:

python -m venv .venv  
.venv\Scripts\activate  

On macOS/Linux, run:

python3 -m venv .venv  
source .venv/bin/activate  

Next, install the required dependencies:

pip install -r requirements.txt  

Once dependencies are installed, start the application by running:

python main.py  

Alternatively, you may run the provided PowerShell script:

.\scripts\run.ps1  

This script will automatically create a virtual environment, install dependencies, and start the server. If your system supports make, you may also use:

make install  
make run  

After the server starts, open the local URL shown in the terminal in your web browser.

## Running Tests
All tests can be executed using PyTest by running:

pytest  

The final version of the project includes a comprehensive test suite covering unit, integration, and system testing.

## Deployed Version
A deployed version of MotorMatch is available at:  
https://software-design-project-wyiy.onrender.com/  

The application is hosted using Render. Due to the use of the free hosting tier, the website may take approximately 10–20 seconds to load if it has been inactive.

## User Documentation (Video Demo)
A complete walkthrough of the application, including user and admin functionality, is available in the video below:  

https://drive.google.com/file/d/1eQTNhCsAoVl3WiIbzU_dZQ_yBmGQV-Kt/view 

The video demonstrates account creation and login, browsing and filtering vehicle listings, viewing detailed information, interacting with features such as wishlists and reviews, and performing administrative actions such as adding, updating, deleting, and moderating listings.

## Developer Documentation
The system is organized into components with clearly defined responsibilities. The main entry point is main.py, while the motormatch directory contains the core backend logic. The templates directory handles the user interface, and the static and images directories store frontend assets. The tests directory contains automated unit, integration, and system tests. Core functionality includes authentication handling, moderation logic, filtering, pricing calculations, and routing.

## Key User Workflows
Users can create accounts, log in, browse and search vehicle listings, apply filters, view detailed vehicle information, and interact with features such as wishlists and reviews. Administrators can manage listings by adding, updating, deleting, and moderating vehicles through the admin dashboard.

## Notes
Ensure all dependencies are installed before running the application. If the PowerShell script does not work on your system, use the manual setup steps. If the deployed website takes time to load, wait a few seconds and refresh the page.

## Contributors
Umad Akram  
Qudsia Fawad  
Andy Donghakiademanou  
Emma Zhu  
Adebayo Abiodun  
