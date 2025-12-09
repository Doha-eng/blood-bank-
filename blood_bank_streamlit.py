import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# ==================== Configuration ====================
DATA_FILE = "blood_bank_data.json"
CRITICAL_THRESHOLD = 500  # ml

# ==================== Database Class ====================
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


# ==================== Inventory Class ====================
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


# ==================== Streamlit App ====================
def main():
    st.set_page_config(page_title="Blood Bank System", layout="wide")
    
    # Initialize session state
    if 'db' not in st.session_state:
        st.session_state.db = Database()
        st.session_state.inventory = Inventory(st.session_state.db)
    
    db = st.session_state.db
    inventory = st.session_state.inventory
    
    # ==================== Header ====================
    st.title("🩸 Blood Bank Management System")
    st.markdown("---")
    
    # ==================== Check Alerts ====================
    alerts = []
    for btype, amount in inventory.list_inventory().items():
        if amount < CRITICAL_THRESHOLD:
            alerts.append(f"⚠️ **{btype}** is critically low! Current: {amount} ml (Threshold: {CRITICAL_THRESHOLD} ml)")
    
    if alerts:
        st.warning("### 🚨 INVENTORY ALERTS")
        for alert in alerts:
            st.write(alert)
        st.markdown("---")
    
    # ==================== Sidebar Navigation ====================
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page:", [
        "Dashboard",
        "Staff Management",
        "Donor Registration",
        "Patient Request",
        "Inventory",
        "Search Records",
        "Reports",
        "Transaction History",
        "System Logs"
    ])
    
    # ==================== Dashboard ====================
    if page == "Dashboard":
        st.header("📊 Dashboard")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Donors", len(db.data.get("donors", [])))
        with col2:
            st.metric("Total Patients", len(db.data.get("patients", [])))
        with col3:
            total_donated = sum(d.get("donated_amount", 0) for d in db.data.get("donors", []))
            st.metric("Total Donated (ml)", total_donated)
        with col4:
            total_requested = sum(p.get("required_amount", 0) for p in db.data.get("patients", []))
            st.metric("Total Requested (ml)", total_requested)
        
        st.markdown("---")
        st.subheader("📦 Inventory Status")
        
        inv = inventory.list_inventory()
        inv_df_data = []
        for btype in sorted(inv.keys()):
            status = "🟢 Good" if inv[btype] >= CRITICAL_THRESHOLD else "🔴 Critical"
            inv_df_data.append({
                "Blood Type": btype,
                "Amount (ml)": inv[btype],
                "Status": status
            })
        
        import pandas as pd
        st.dataframe(pd.DataFrame(inv_df_data), use_container_width=True)
    
    # ==================== Staff Management ====================
    elif page == "Staff Management":
        st.header("👨‍💼 Staff Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name")
        with col2:
            email = st.text_input("Email")
        
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age", min_value=18, max_value=65, value=30)
        with col2:
            staff_id = st.number_input("Staff ID", min_value=1, value=1)
        
        salary = st.number_input("Salary", min_value=0.0, value=5000.0)
        
        if st.button("Register Staff"):
            if name and email:
                db.log(f"Staff entry: {name} (ID: {staff_id}, Salary: {salary})")
                st.success(f"✅ Staff {name} registered successfully!")
                st.write(f"**Name:** {name}")
                st.write(f"**Email:** {email}")
                st.write(f"**Age:** {age}")
                st.write(f"**ID:** {staff_id}")
                st.write(f"**Salary:** ${salary}")
            else:
                st.error("❌ Please fill in all required fields.")
    
    # ==================== Donor Registration ====================
    elif page == "Donor Registration":
        st.header("🩸 Donor Registration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            donor_name = st.text_input("Donor Name")
        with col2:
            donor_email = st.text_input("Donor Email")
        
        col1, col2 = st.columns(2)
        
        with col1:
            donor_age = st.number_input("Age", min_value=18, max_value=65, value=30, key="donor_age")
        with col2:
            donor_id = st.number_input("ID", min_value=1, value=1, key="donor_id")
        
        donor_phone = st.text_input("Phone Number")
        
        st.markdown("---")
        st.subheader("Fitness Check")
        chronic_disease = st.radio("Do you suffer from chronic disease?", ["No", "Yes"])
        
        if chronic_disease == "Yes":
            st.error("❌ Donation not allowed due to chronic disease.")
        else:
            st.markdown("---")
            st.subheader("Donation Details")
            
            donation_amount = st.slider("Donation Amount (ml)", min_value=50, max_value=500, value=250, step=50)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                donation_day = st.number_input("Day", min_value=1, max_value=31, value=1, key="donation_day")
            with col2:
                donation_month = st.number_input("Month", min_value=1, max_value=12, value=1, key="donation_month")
            with col3:
                donation_year = st.number_input("Year", min_value=2020, max_value=2025, value=2025, key="donation_year")
            
            blood_type = st.selectbox("Blood Type", list(Inventory.VALID_TYPES))
            
            if st.button("Complete Donation"):
                try:
                    if donor_name and donor_email:
                        if inventory.add_blood(blood_type, donation_amount):
                            donor_rec = {
                                "name": donor_name,
                                "email": donor_email,
                                "age": donor_age,
                                "id": donor_id,
                                "phone": donor_phone,
                                "donated_amount": donation_amount,
                                "blood_type": blood_type,
                                "donation_date": f"{donation_year:04d}-{donation_month:02d}-{donation_day:02d}"
                            }
                            db.data.setdefault("donors", []).append(donor_rec)
                            db.save()
                            st.success(f"✅ Donation successful! {blood_type} now has {inventory.get_amount(blood_type)} ml")
                        else:
                            st.error("❌ Failed to update inventory.")
                    else:
                        st.error("❌ Please fill in all required fields.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # ==================== Patient Request ====================
    elif page == "Patient Request":
        st.header("🏥 Patient Blood Request")
        
        col1, col2 = st.columns(2)
        
        with col1:
            patient_name = st.text_input("Patient Name")
        with col2:
            patient_email = st.text_input("Patient Email")
        
        col1, col2 = st.columns(2)
        
        with col1:
            patient_age = st.number_input("Age", min_value=0, max_value=120, value=30, key="patient_age")
        with col2:
            patient_id = st.number_input("ID", min_value=1, value=1, key="patient_id")
        
        patient_phone = st.text_input("Phone Number", key="patient_phone")
        
        st.markdown("---")
        st.subheader("Blood Request Details")
        
        patient_blood_type = st.selectbox("Blood Type", list(Inventory.VALID_TYPES), key="patient_blood_type")
        required_amount = st.number_input("Required Amount (ml)", min_value=1, value=250)
        
        # Display compatible blood types
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
        st.info(f"✅ Compatible blood types: {mapping.get(patient_blood_type, 'Unknown')}")
        
        if st.button("Request Blood"):
            try:
                if patient_name and patient_email:
                    if inventory.remove_blood(patient_blood_type, required_amount):
                        patient_rec = {
                            "name": patient_name,
                            "email": patient_email,
                            "age": patient_age,
                            "id": patient_id,
                            "phone": patient_phone,
                            "required_amount": required_amount,
                            "blood_type": patient_blood_type,
                            "request_date": datetime.now().strftime("%Y-%m-%d")
                        }
                        db.data.setdefault("patients", []).append(patient_rec)
                        db.save()
                        st.success(f"✅ Request fulfilled! {patient_blood_type} remaining: {inventory.get_amount(patient_blood_type)} ml")
                    else:
                        st.error(f"❌ Insufficient {patient_blood_type} blood. Available: {inventory.get_amount(patient_blood_type)} ml")
                else:
                    st.error("❌ Please fill in all required fields.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # ==================== Inventory ====================
    elif page == "Inventory":
        st.header("📦 Blood Inventory")
        
        inv = inventory.list_inventory()
        inv_data = []
        
        for btype in sorted(inv.keys()):
            inv_data.append({
                "Blood Type": btype,
                "Amount (ml)": inv[btype],
                "Status": "🟢 Good" if inv[btype] >= CRITICAL_THRESHOLD else "🔴 Critical"
            })
        
        import pandas as pd
        st.dataframe(pd.DataFrame(inv_data), use_container_width=True)
        
        st.markdown("---")
        st.subheader("Manual Inventory Adjustment")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            action = st.radio("Action", ["Add", "Remove"])
        with col2:
            btype = st.selectbox("Blood Type", list(Inventory.VALID_TYPES), key="inv_btype")
        with col3:
            amount = st.number_input("Amount (ml)", min_value=1, value=100, key="inv_amount")
        
        if st.button("Apply"):
            if action == "Add":
                if inventory.add_blood(btype, amount):
                    st.success(f"✅ Added {amount} ml to {btype}")
                    st.rerun()
            else:
                if inventory.remove_blood(btype, amount):
                    st.success(f"✅ Removed {amount} ml from {btype}")
                    st.rerun()
                else:
                    st.error(f"❌ Insufficient amount. Available: {inventory.get_amount(btype)} ml")
    
    # ==================== Search Records ====================
    elif page == "Search Records":
        st.header("🔍 Search Records")
        
        search_type = st.radio("Search for:", ["Donor", "Patient"])
        search_term = st.text_input("Enter search term (Name, ID, or Blood Type)")
        
        if st.button("Search"):
            search_for = "donors" if search_type == "Donor" else "patients"
            records = db.data.get(search_for, [])
            results = []
            
            search_term_lower = search_term.lower()
            
            for record in records:
                if search_term_lower in record.get("name", "").lower():
                    results.append(record)
                elif search_term.isdigit() and int(search_term) == record.get("id"):
                    results.append(record)
                elif search_term_lower == record.get("blood_type", "").lower():
                    results.append(record)
            
            db.log(f"Search performed for '{search_term}' in {search_for}. Found {len(results)} records.")
            
            st.write(f"**Found {len(results)} result(s)**")
            
            if results:
                import pandas as pd
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            else:
                st.info("No matching records found.")
    
    # ==================== Reports ====================
    elif page == "Reports":
        st.header("📊 Reports")
        
        donors = db.data.get("donors", [])
        patients = db.data.get("patients", [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Donation Statistics")
            st.metric("Total Donors", len(donors))
            st.metric("Total Donated (ml)", sum(d.get("donated_amount", 0) for d in donors))
        
        with col2:
            st.subheader("Request Statistics")
            st.metric("Total Patients", len(patients))
            st.metric("Total Requested (ml)", sum(p.get("required_amount", 0) for p in patients))
        
        st.markdown("---")
        st.subheader("Activity by Blood Type")
        
        donation_by_type = {bt: 0 for bt in Inventory.VALID_TYPES}
        request_by_type = {bt: 0 for bt in Inventory.VALID_TYPES}
        
        for d in donors:
            bt = d.get("blood_type")
            if bt in donation_by_type:
                donation_by_type[bt] += d.get("donated_amount", 0)
        
        for p in patients:
            bt = p.get("blood_type")
            if bt in request_by_type:
                request_by_type[bt] += p.get("required_amount", 0)
        
        report_data = []
        for bt in sorted(Inventory.VALID_TYPES):
            report_data.append({
                "Blood Type": bt,
                "Donated (ml)": donation_by_type[bt],
                "Requested (ml)": request_by_type[bt],
                "Net (ml)": donation_by_type[bt] - request_by_type[bt]
            })
        
        import pandas as pd
        st.dataframe(pd.DataFrame(report_data), use_container_width=True)
        
        db.log("Generated comprehensive reports.")
    
    # ==================== Transaction History ====================
    elif page == "Transaction History":
        st.header("📜 Transaction History")
        
        history_type = st.radio("View:", ["Donor History", "Patient History"])
        
        records_key = "donors" if history_type == "Donor History" else "patients"
        records = db.data.get(records_key, [])
        
        st.write(f"**Total {records_key.capitalize()}: {len(records)}**")
        
        if records:
            import pandas as pd
            st.dataframe(pd.DataFrame(records), use_container_width=True)
        else:
            st.info(f"No {records_key} records available.")
        
        db.log(f"Viewed {records_key} transaction history.")
    
    # ==================== System Logs ====================
    elif page == "System Logs":
        st.header("📋 System Logs")
        
        logs = db.data.get("logs", [])
        
        if logs:
            st.write(f"**Total Logs: {len(logs)}**")
            for log in reversed(logs[-50:]):  # Show last 50 logs
                st.write(log)
        else:
            st.info("No logs available.")


if __name__ == "__main__":
    main()
