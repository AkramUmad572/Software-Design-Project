# Simple Python prototype for the Lab 6 Car Marketplace project
# Uses Tkinter to simulate the workflow: login → catalog → details → add listing → delete listing

import tkinter as tk
from tkinter import ttk, messagebox


# Main application controller that manages screens and shared data
class CarMarketplaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Marketplace Prototype - Lab 6")
        self.root.geometry("950x600")
        self.root.minsize(900, 550)

        # Stores the role of the currently logged-in user
        self.current_role = "User"

        # Dummy vehicle data used for the prototype
        self.vehicles = [
            {
                "make": "Toyota",
                "model": "Corolla",
                "year": "2020",
                "price": "$18,500",
                "mileage": "52,000 km",
                "condition": "Used",
                "vin": "2T1BURHE0LC123456",
                "seller": "AutoHub"
            },
            {
                "make": "Honda",
                "model": "Civic",
                "year": "2019",
                "price": "$17,200",
                "mileage": "61,000 km",
                "condition": "Used",
                "vin": "19XFC2F69KE234567",
                "seller": "City Cars"
            },
            {
                "make": "Ford",
                "model": "Escape",
                "year": "2021",
                "price": "$24,900",
                "mileage": "38,000 km",
                "condition": "Certified",
                "vin": "1FMCU9G68MUA34567",
                "seller": "North Motors"
            }
        ]

        # Index of the currently selected vehicle
        self.selected_index = None

        # Dictionary storing all application screens
        self.frames = {}

        # Container that holds all page frames
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)

        # Create each page and store it
        for frame_class in (LoginPage, CatalogPage, DetailsPage, AddListingPage):
            frame = frame_class(container, self)
            self.frames[frame_class.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Start the program on the login screen
        self.show_frame("LoginPage")

    # Switch between screens
    def show_frame(self, frame_name):
        frame = self.frames[frame_name]

        # Refresh certain pages when opened
        if frame_name == "CatalogPage":
            frame.refresh_catalog()
        elif frame_name == "DetailsPage":
            frame.refresh_details()
        elif frame_name == "AddListingPage":
            frame.clear_form()

        frame.tkraise()

    # Simulated login
    def login(self, username, role):
        if not username.strip():
            messagebox.showwarning("Missing Username", "Please enter a username.")
            return

        self.current_role = role
        self.frames["CatalogPage"].welcome_var.set(
            f"Welcome, {username}! Role: {self.current_role}"
        )
        self.show_frame("CatalogPage")

    # Logout and return to login screen
    def logout(self):
        self.current_role = "User"
        self.show_frame("LoginPage")

    # Open details page for a selected vehicle
    def open_vehicle_details(self, index):
        self.selected_index = index
        self.show_frame("DetailsPage")

    # Add a new vehicle to the catalog
    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)
        messagebox.showinfo("Listing Added", "The vehicle listing was added successfully.")
        self.show_frame("CatalogPage")

    # Delete a vehicle (admin only)
    def delete_vehicle(self, index):
        if self.current_role != "Admin":
            messagebox.showwarning(
                "Access Denied",
                "Only Admin accounts can delete listings in this prototype."
            )
            return

        vehicle_name = f"{self.vehicles[index]['year']} {self.vehicles[index]['make']} {self.vehicles[index]['model']}"
        confirm = messagebox.askyesno(
            "Delete Listing",
            f"Are you sure you want to delete {vehicle_name}?"
        )
        if confirm:
            self.vehicles.pop(index)
            self.selected_index = None
            messagebox.showinfo("Deleted", "The listing was deleted.")
            self.show_frame("CatalogPage")


#LOGIN PAGE
class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f4f6f8")
        self.app = app

        # Card container for login form
        card = tk.Frame(self, bg="white", bd=1, relief="solid", padx=30, pady=30)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="Car Marketplace Prototype", font=("Arial", 18, "bold"), bg="white").pack(pady=(0, 10))
        tk.Label(card, text="Lab 6 - Customer Meeting Prototype", font=("Arial", 11), bg="white").pack(pady=(0, 20))

        # Username input
        tk.Label(card, text="Username", anchor="w", bg="white").pack(fill="x")
        self.username_entry = tk.Entry(card, width=30)
        self.username_entry.pack(pady=(0, 10))

        # Password input (not validated in prototype)
        tk.Label(card, text="Password", anchor="w", bg="white").pack(fill="x")
        self.password_entry = tk.Entry(card, width=30, show="*")
        self.password_entry.pack(pady=(0, 10))

        # Role selection dropdown
        tk.Label(card, text="Select Role", anchor="w", bg="white").pack(fill="x")
        self.role_var = tk.StringVar(value="User")
        role_dropdown = ttk.Combobox(
            card,
            textvariable=self.role_var,
            values=["User", "Admin"],
            state="readonly",
            width=27
        )
        role_dropdown.pack(pady=(0, 20))

        # Login button
        tk.Button(card, text="Login", width=18, command=self.handle_login).pack()

        tk.Label(card, text="Prototype note: authentication is simulated for the demo.", font=("Arial", 9), bg="white", fg="#555555").pack(pady=(15, 0))

    # Trigger login through main app
    def handle_login(self):
        username = self.username_entry.get()
        role = self.role_var.get()
        self.app.login(username, role)


#CATALOG PAGE
class CatalogPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#eef2f5")
        self.app = app
        self.welcome_var = tk.StringVar(value="Welcome!")

        # Header section
        header = tk.Frame(self, bg="#1f3c5a", pady=12)
        header.pack(fill="x")

        tk.Label(header, text="Vehicle Catalog", font=("Arial", 18, "bold"), fg="white", bg="#1f3c5a").pack(side="left", padx=15)
        tk.Label(header, textvariable=self.welcome_var, font=("Arial", 10), fg="white", bg="#1f3c5a").pack(side="left", padx=20)

        tk.Button(header, text="Add Listing", command=lambda: app.show_frame("AddListingPage")).pack(side="right", padx=10)
        tk.Button(header, text="Logout", command=app.logout).pack(side="right")

        # Main catalog container
        content = tk.Frame(self, bg="#eef2f5", padx=20, pady=20)
        content.pack(fill="both", expand=True)

        instructions = tk.Label(content, text="This prototype shows sample vehicle listings.", bg="#eef2f5", font=("Arial", 10))
        instructions.pack(anchor="w", pady=(0, 12))

        self.cards_container = tk.Frame(content, bg="#eef2f5")
        self.cards_container.pack(fill="both", expand=True)

    # Refresh the vehicle list
    def refresh_catalog(self):
        for widget in self.cards_container.winfo_children():
            widget.destroy()

        if not self.app.vehicles:
            tk.Label(self.cards_container, text="No listings available.", font=("Arial", 12), bg="#eef2f5").pack(pady=20)
            return

        for index, vehicle in enumerate(self.app.vehicles):
            card = tk.Frame(self.cards_container, bg="white", bd=1, relief="solid", padx=15, pady=15)
            card.pack(fill="x", pady=8)

            vehicle_title = f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
            tk.Label(card, text=vehicle_title, font=("Arial", 14, "bold"), bg="white").grid(row=0, column=0, sticky="w")

            tk.Label(card, text=f"Price: {vehicle['price']}", font=("Arial", 11), bg="white").grid(row=1, column=0, sticky="w")
            tk.Label(card, text=f"Mileage: {vehicle['mileage']}", font=("Arial", 11), bg="white").grid(row=2, column=0, sticky="w")
            tk.Label(card, text=f"Condition: {vehicle['condition']}", font=("Arial", 11), bg="white").grid(row=3, column=0, sticky="w")

            btn_frame = tk.Frame(card, bg="white")
            btn_frame.grid(row=0, column=1, rowspan=4, padx=20)

            tk.Button(btn_frame, text="View Details", width=15, command=lambda i=index: self.app.open_vehicle_details(i)).pack(pady=4)
            tk.Button(btn_frame, text="Delete", width=15, command=lambda i=index: self.app.delete_vehicle(i)).pack(pady=4)

            card.grid_columnconfigure(0, weight=1)


#VEHICLE DETAILS PAGE
class DetailsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f7f7f7")
        self.app = app

        header = tk.Frame(self, bg="#324960", pady=12)
        header.pack(fill="x")

        tk.Label(header, text="Vehicle Details", font=("Arial", 18, "bold"), fg="white", bg="#324960").pack(side="left", padx=15)
        tk.Button(header, text="Back to Catalog", command=lambda: app.show_frame("CatalogPage")).pack(side="right", padx=15)

        # Container for vehicle information
        self.details_box = tk.Frame(self, bg="white", bd=1, relief="solid", padx=25, pady=25)
        self.details_box.pack(padx=50, pady=40)

        self.detail_labels = {}
        fields = ["make", "model", "year", "price", "mileage", "condition", "vin", "seller"]

        tk.Label(self.details_box, text="Selected Vehicle", font=("Arial", 16, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Create label pairs for each field
        for row, field in enumerate(fields, start=1):
            field_name = field.upper() if field == "vin" else field.capitalize()
            tk.Label(self.details_box, text=f"{field_name}:", font=("Arial", 11, "bold"), bg="white").grid(row=row, column=0, sticky="w", pady=6)
            value_label = tk.Label(self.details_box, text="", font=("Arial", 11), bg="white")
            value_label.grid(row=row, column=1, sticky="w")
            self.detail_labels[field] = value_label

    # Populate vehicle information
    def refresh_details(self):
        if self.app.selected_index is None:
            return

        vehicle = self.app.vehicles[self.app.selected_index]
        for field, label in self.detail_labels.items():
            label.config(text=vehicle[field])


#ADD LISTING PAGE
class AddListingPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f4f4f4")
        self.app = app
        self.entries = {}

        header = tk.Frame(self, bg="#406343", pady=12)
        header.pack(fill="x")

        tk.Label(header, text="Add Vehicle Listing", font=("Arial", 18, "bold"), fg="white", bg="#406343").pack(side="left", padx=15)
        tk.Button(header, text="Back to Catalog", command=lambda: app.show_frame("CatalogPage")).pack(side="right", padx=15)

        # Form container
        form = tk.Frame(self, bg="white", bd=1, relief="solid", padx=25, pady=25)
        form.pack(padx=60, pady=35)

        fields = [
            ("make", "Make"),
            ("model", "Model"),
            ("year", "Year"),
            ("price", "Price"),
            ("mileage", "Mileage"),
            ("condition", "Condition"),
            ("vin", "VIN"),
            ("seller", "Seller")
        ]

        tk.Label(form, text="Enter Vehicle Information", font=("Arial", 15, "bold"), bg="white").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        # Create input fields
        for row, (key, label_text) in enumerate(fields, start=1):
            tk.Label(form, text=label_text + ":", bg="white", font=("Arial", 11)).grid(row=row, column=0, sticky="w")
            entry = tk.Entry(form, width=35)
            entry.grid(row=row, column=1, pady=7)
            self.entries[key] = entry

        tk.Button(form, text="Submit Listing", width=18, command=self.submit_listing).grid(row=len(fields) + 1, column=0, columnspan=2, pady=(20, 0))

    # Clear form fields when opening the page
    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    # Handle form submission
    def submit_listing(self):
        vehicle = {key: entry.get().strip() for key, entry in self.entries.items()}

        if any(value == "" for value in vehicle.values()):
            messagebox.showwarning("Incomplete Form", "Please fill in all fields before submitting.")
            return

        # Normalize formatting
        if not vehicle["price"].startswith("$"):
            vehicle["price"] = "$" + vehicle["price"]

        if "km" not in vehicle["mileage"].lower():
            vehicle["mileage"] += " km"

        self.app.add_vehicle(vehicle)


#PROGRAM ENTRY POINT
if __name__ == "__main__":
    root = tk.Tk()
    app = CarMarketplaceApp(root)
    root.mainloop()

