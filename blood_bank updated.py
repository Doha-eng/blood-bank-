# blood_bank.py
from typing import Dict, Any
import json
import os
from datetime import datetime

DATA_FILE = "data.json"
CRITICAL_THRESHOLD = 500 # ml


class Database:
    def __init__(self, path: str = DATA_FILE):
        self.path = path
        self.data: Dict[str, Any] = {}
        self.load()

    def ensure_structure(self):
        changed = False
        if "inventory" not in self.data:
            self.data["inventory"] = {
                "A+": 2000, "A-": 2000, "B+": 2000, "B-": 2000,
                "AB+": 2000, "AB-": 2000, "O+": 2000, "O-": 2000
            }
            changed = True
        if "donors" not in self.data:
            self.data["donors"] = []
            changed = True
        if "patients" not in self.data:
            self.data["patients"] = []
            changed = True
        if "logs" not in self.data:
            self.data["logs"] = []
            changed = True
        if changed:
            self.save()

    def load(self):
        if not os.path.exists(self.path):
            self.data = {}
            self.ensure_structure()
            return
        with open(self.path, "r", encoding="utf-8") as f:
            try:
                self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {}
        self.ensure_structure()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def log(self, entry: str):
        timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
        self.data.setdefault("logs", []).append(f"{timestamp} - {entry}")
        self.save()


class Inventory:
    VALID_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}

    def __init__(self, db: Database):
        self.db = db

    def _get_inventory(self) -> Dict[str, int]:
        return self.db.data["inventory"]

    def get_amount(self, btype: str) -> int:
        inv = self._get_inventory()
        return int(inv.get(btype, 0))

    def add_blood(self, btype: str, amount: int) -> bool:
        if btype not in Inventory.VALID_TYPES or amount <= 0:
            return False
        inv = self._get_inventory()
        inv[btype] = inv.get(btype, 0) + amount
        self.db.save()
        self.db.log(f"Added {amount}ml to {btype} (new: {inv[btype]} ml)")
        return True

    def remove_blood(self, btype: str, amount: int) -> bool:
        if btype not in Inventory.VALID_TYPES or amount <= 0:
            return False
        inv = self._get_inventory()
        current = inv.get(btype, 0)
        if amount > current:
            return False
        inv[btype] = current - amount
        self.db.save()
        self.db.log(f"Removed {amount}ml from {btype} (remaining: {inv[btype]} ml)")
        return True

    def list_inventory(self) -> Dict[str, int]:
        return dict(self._get_inventory())


class Staff:
    def __init__(self):
        self.name: str = ""
        self.email: str = ""
        self.age: int = 0
        self.id: int = 0
        self.salary: float = 0.0

    def input_basic(self):
        self.name = input("Enter your name: ").strip()
        self.email = input("Enter your email: ").strip()
        while True:
            try:
                self.age = int(input("Enter your age: ").strip())
                if 18 <= self.age <= 65:
                    break
                print("Age must be between 18 and 65.")
            except ValueError:
                print("Please enter a valid integer for age.")
        while True:
            try:
                self.id = int(input("Enter your ID: ").strip())
                break
            except ValueError:
                print("Please enter a numeric ID.")

    def set_salary(self):
        while True:
            try:
                self.salary = float(input("Enter your salary: ").strip())
                break
            except ValueError:
                print("Enter a valid number for salary.")

    def display(self):
        print("==========")
        print(f"Name: {self.name}")
        print(f"Email: {self.email}")
        print(f"Age: {self.age}")
        print(f"ID: {self.id}")
        print("==========")


class Donor(Staff):
    def __init__(self, db: Database):
        super().__init__()
        self.phone: str = ""
        self.day: int = 0
        self.month: int = 0
        self.year: int = 0
        self.blood_type: str = ""
        self.donated_amount: int = 0
        self.db = db

    def input_donor(self):
        self.input_basic()
        self.phone = input("Enter your phone number: ").strip()

    def fitness_check(self) -> bool:
        fitness = input("Do you suffer from chronic disease? (yes/no): ").strip().lower()
        if fitness == "no":
            print("Donation accepted.")
            return True
        print("Donation not allowed.")
        return False

    def donation_data(self):
        while True:
            try:
                self.donated_amount = int(input("Enter donation amount (50-500 ml): ").strip())
                if 50 <= self.donated_amount <= 500:
                    break
                print("Amount must be between 50 and 500.")
            except ValueError:
                print("Please enter a valid integer.")
        while True:
            try:
                d = int(input("Donation day (1-31): ").strip())
                m = int(input("Donation month (1-12): ").strip())
                y = int(input("Donation year (e.g., 2025): ").strip())
                datetime(y, m, d)
                self.day, self.month, self.year = d, m, y
                break
            except (ValueError, OverflowError):
                print("Invalid date, enter again.")
        print(f"Donation date: {self.day}/{self.month}/{self.year}")

    def donate(self, inventory: Inventory):
        bt = input("Enter blood type (A+/A-/B+/B-/AB+/AB-/O+/O-): ").strip()
        if bt not in Inventory.VALID_TYPES:
            print("Wrong blood type.")
            return False
        self.blood_type = bt
        ok = inventory.add_blood(bt, self.donated_amount)
        if ok:
            donor_rec = {
                "name": self.name,
                "email": self.email,
                "age": self.age,
                "id": self.id,
                "phone": self.phone,
                "donated_amount": self.donated_amount,
                "blood_type": self.blood_type,
                "donation_date": f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
            }
            self.db.data.setdefault("donors", []).append(donor_rec)
            self.db.save()
            print("Donation recorded. Total for", bt, "=", inventory.get_amount(bt), "ml")
            return True
        print("Failed to update inventory.")
        return False

    def display(self):
        super().display()
        print("Phone:", self.phone)
        print("Donated amount:", self.donated_amount)
        print("Blood type:", self.blood_type)


class Patient(Staff):
    def __init__(self, db: Database):
        super().__init__()
        self.phone: str = ""
        self.blood_type: str = ""
        self.required_amount: int = 0
        self.db = db

    def input_patient(self):
        self.input_basic()
        self.phone = input("Enter your phone number: ").strip()

    def patient_data(self):
        while True:
            try:
                self.required_amount = int(input("Enter required amount (ml): ").strip())
                if self.required_amount > 0:
                    break
                print("Amount must be positive.")
            except ValueError:
                print("Enter a valid integer.")
        valid = Inventory.VALID_TYPES
        while True:
            bt = input("Enter your blood type: ").strip()
            if bt in valid:
                self.blood_type = bt
                break
            print("Invalid blood type. Try again.")

    def get_types(self):
        bt = self.blood_type
        mapping = {
            "O-": "O-",
            "O+": "O-, O+",
            "A-": "O-, A-",
            "A+": "O-, O+, A-, A+",
            "B-": "O-, B-",
            "B+": "O-, O+, B-, B+",
            "AB-": "O-, A-, B-, AB-",
            "AB+": "All types"
        }
        print("You can receive from:", mapping.get(bt, "WRONG INPUT"))

    def request_blood(self, inventory: Inventory):
        bt = self.blood_type
        success = inventory.remove_blood(bt, self.required_amount)
        if success:
            rec = {
                "name": self.name,
                "email": self.email,
                "age": self.age,
                "id": self.id,
                "phone": self.phone,
                "required_amount": self.required_amount,
                "blood_type": bt,
                "request_date": datetime.now().strftime("%Y-%m-%d")
            }
            self.db.data.setdefault("patients", []).append(rec)
            self.db.save()
            print("Request fulfilled. Remaining", bt, "=", inventory.get_amount(bt), "ml")
            return True
        else:
            print("There is not enough amount or invalid type.")
            return False

    def display(self):
        super().display()
        print("Phone:", self.phone)
        print("Required amount:", self.required_amount)
        print("Blood type:", self.blood_type)


def generate_reports(db: Database, inv: Inventory):
    print("\n===== Blood Bank Reports =====")
    
    donors = db.data.get("donors", [])
    patients = db.data.get("patients", [])
    
    # 1. Donation Statistics
    total_donors = len(donors)
    total_donated_amount = sum(d.get("donated_amount", 0) for d in donors)
    
    print("\n--- Donation Statistics ---")
    print(f"Total Donors Registered: {total_donors}")
    print(f"Total Blood Donated: {total_donated_amount} ml")
    
    # 2. Request Statistics
    total_patients = len(patients)
    total_requested_amount = sum(p.get("required_amount", 0) for p in patients)
    
    print("\n--- Request Statistics ---")
    print(f"Total Patients Registered: {total_patients}")
    print(f"Total Blood Requested: {total_requested_amount} ml")
    
    # 3. Inventory Summary (re-using print_inventory logic)
    print("\n--- Current Inventory Summary (ml) ---")
    inv_map = inv.list_inventory()
    for bt in sorted(inv_map.keys()):
        print(f"{bt:3}: {inv_map[bt]:5} ml")
    
    # 4. Activity by Blood Type
    donation_by_type = {bt: 0 for bt in Inventory.VALID_TYPES}
    request_by_type = {bt: 0 for bt in Inventory.VALID_TYPES}
    
    for d in donors:
        bt = d.get("blood_type")
        amount = d.get("donated_amount", 0)
        if bt in donation_by_type:
            donation_by_type[bt] += amount
            
    for p in patients:
        bt = p.get("blood_type")
        amount = p.get("required_amount", 0)
        if bt in request_by_type:
            request_by_type[bt] += amount

    print("\n--- Activity by Blood Type (ml) ---")
    print(f"{'Type':<5} | {'Donated':<10} | {'Requested':<10}")
    print("-" * 30)
    for bt in sorted(Inventory.VALID_TYPES):
        print(f"{bt:<5} | {donation_by_type[bt]:<10} | {request_by_type[bt]:<10}")
        
    db.log("Generated comprehensive reports.")
    input("\nPress Enter to return to menu...")


def check_alerts(inv: Inventory):
    alerts = []
    for btype, amount in inv.list_inventory().items():
        if amount < CRITICAL_THRESHOLD:
            alerts.append(f"ALERT: {btype} is critically low! Current level: {amount} ml (Threshold: {CRITICAL_THRESHOLD} ml)")
    
    if alerts:
        print("\n!!! INVENTORY ALERTS !!!")
        for alert in alerts:
            print(alert)
        print("!!! INVENTORY ALERTS !!!\n")
        return True
    return False

def print_inventory(inv: Inventory):
    inv_map = inv.list_inventory()
    print("\n===== Current Inventory (ml) =====")
    for bt in sorted(inv_map.keys()):
        print(f"{bt:3}: {inv_map[bt]:5} ml")
    print("==================================")
    input("Press Enter to return to menu...")


def search_records(db: Database):
    print("\n===== Search Records =====")
    while True:
        search_type = input("Search for (1) Donor or (2) Patient? (Enter 1 or 2, or 0 to cancel): ").strip()
        if search_type == '0':
            return
        if search_type not in ['1', '2']:
            print("Invalid choice.")
            continue

        search_for = "donors" if search_type == '1' else "patients"
        search_term = input(f"Enter search term (Name, ID, or Blood Type) for {search_for}: ").strip().lower()
        if not search_term:
            print("Search term cannot be empty.")
            continue

        records = db.data.get(search_for, [])
        results = []

        for record in records:
            # Search by Name (partial, case-insensitive)
            if search_term in record.get("name", "").lower():
                results.append(record)
                continue
            # Search by ID (exact match)
            if search_term.isdigit() and int(search_term) == record.get("id"):
                results.append(record)
                continue
            # Search by Blood Type (exact match, case-insensitive)
            if search_term == record.get("blood_type", "").lower():
                results.append(record)
                continue

        print(f"\n--- {len(results)} Result(s) Found for '{search_term}' in {search_for} ---")
        if results:
            for i, rec in enumerate(results):
                print(f"--- Record {i+1} ---")
                for key, value in rec.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")
                print("------------------")
        else:
            print("No matching records found.")
        
        db.log(f"Search performed for '{search_term}' in {search_for}. Found {len(results)} records.")
        input("Press Enter to return to search menu...")

def view_transaction_history(db: Database):
    print("\n===== Transaction History =====")
    while True:
        choice = input("View (1) Donor History or (2) Patient History? (Enter 1 or 2, or 0 to cancel): ").strip()
        if choice == '0':
            return
        if choice not in ['1', '2']:
            print("Invalid choice.")
            continue

        records_key = "donors" if choice == '1' else "patients"
        records = db.data.get(records_key, [])
        
        print(f"\n--- {records_key.title()} History ({len(records)} Records) ---")
        if not records:
            print(f"No {records_key} records available.")
        else:
            for i, rec in enumerate(records):
                print(f"--- Record {i+1} ---")
                for key, value in rec.items():
                    print(f"{key.replace('_', ' ').title()}: {value}")
                print("------------------")
        
        db.log(f"Viewed {records_key} transaction history.")
        input("Press Enter to return to history menu...")


def print_logs(db: Database):
    logs = db.data.get("logs", [])
    print("\n===== System Logs =====")
    if not logs:
        print("No logs available.")
    else:
        for line in logs:
            print(line)
    print("========================")
    input("Press Enter to return to menu...")


def main():
    db = Database()
    inventory = Inventory(db)

    print("===== WELCOME TO OUR BLOODBANK SYSTEM =====")

    while True:
        check_alerts(inventory)
        print("\nMenu:")
        print("1 - Staff (enter/display/set salary)")
        print("2 - Donor (register & donate)")
        print("3 - Patient (request blood)")
        print("4 - View Inventory")
        print("5 - View System Logs")
        print("6 - Search Records")
        print("7 - Generate Reports")
        print("8 - View Transaction History")
        print("0 - Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            s = Staff()
            s.input_basic()
            s.set_salary()
            s.display()
            print(f"Salary: {s.salary}")
            db.log(f"Staff entry: {s.name} (ID: {s.id})")
            input("Press Enter to return to menu...")
        elif choice == "2":
            d = Donor(db)
            d.input_donor()
            if d.fitness_check():
                d.donation_data()
                if d.donate(inventory):
                    print("Donation successful.")
                else:
                    print("Donation failed.")
                d.display()
            input("Press Enter to return to menu...")
        elif choice == "3":
            p = Patient(db)
            p.input_patient()
            p.patient_data()
            p.get_types()
            if p.request_blood(inventory):
                print("Request completed.")
            else:
                print("Request failed.")
            p.display()
            input("Press Enter to return to menu...")
        elif choice == "4":
            print_inventory(inventory)
        elif choice == "5":
            print_logs(db)
        elif choice == "6":
            search_records(db)
        elif choice == "7":
            generate_reports(db, inventory)
        elif choice == "8":
            view_transaction_history(db)
        elif choice == "0":
            print("Thank you for using our blood bank system.")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
