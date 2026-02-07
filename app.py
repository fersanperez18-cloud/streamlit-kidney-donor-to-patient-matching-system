import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import hashlib
import json
import time

# Page configuration
st.set_page_config(
    page_title="Kidney Donor Matching System",
    page_icon="🫘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'patients' not in st.session_state:
    st.session_state.patients = []
if 'donors' not in st.session_state:
    st.session_state.donors = []
if 'offers' not in st.session_state:
    st.session_state.offers = []
if 'matches' not in st.session_state:
    st.session_state.matches = []

# Mock user database (in production, use proper database with hashed passwords)
USERS = {
    'dr.smith': hashlib.sha256('password123'.encode()).hexdigest(),
    'dr.johnson': hashlib.sha256('password123'.encode()).hexdigest(),
    'admin': hashlib.sha256('admin123'.encode()).hexdigest()
}

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def login(username, password):
    """Authenticate user"""
    if username in USERS and USERS[username] == hash_password(password):
        return True
    return False

def calculate_blood_type_compatibility(patient_blood, donor_blood):
    """
    Calculate blood type compatibility based on OPTN guidelines
    Returns compatibility score (0-100)
    """
    compatibility_matrix = {
        'O': {'O': 100, 'A': 0, 'B': 0, 'AB': 0},
        'A': {'O': 80, 'A': 100, 'B': 0, 'AB': 0},
        'B': {'O': 80, 'A': 0, 'B': 100, 'AB': 0},
        'AB': {'O': 60, 'A': 80, 'B': 80, 'AB': 100}
    }
    return compatibility_matrix.get(patient_blood, {}).get(donor_blood, 0)

def calculate_hla_match_score(patient_hla, donor_hla):
    """
    Calculate HLA matching score (0-6 antigens matched)
    OPTN considers HLA-A, HLA-B, and HLA-DR (6 total antigens)
    Returns score 0-100
    """
    matches = 0
    for i in range(len(patient_hla)):
        if i < len(donor_hla) and patient_hla[i] == donor_hla[i]:
            matches += 1
    
    # Convert to percentage (6 matches = 100%)
    return (matches / 6) * 100

def calculate_cpra_priority(cpra):
    """
    Calculate priority based on CPRA (Calculated Panel Reactive Antibody)
    Higher CPRA = harder to match = higher priority
    """
    if cpra >= 98:
        return 100
    elif cpra >= 80:
        return 80
    elif cpra >= 20:
        return 50
    else:
        return 20

def calculate_wait_time_points(wait_days):
    """
    Calculate points based on waiting time
    Longer wait = more points
    """
    # Cap at 5 years for calculation
    max_days = 365 * 5
    normalized_wait = min(wait_days, max_days) / max_days
    return normalized_wait * 100

def calculate_age_compatibility(patient_age, donor_age):
    """
    Age matching consideration
    Closer ages generally preferred
    """
    age_diff = abs(patient_age - donor_age)
    if age_diff <= 10:
        return 100
    elif age_diff <= 20:
        return 80
    elif age_diff <= 30:
        return 60
    else:
        return 40

def calculate_distance_score(distance_miles):
    """
    Geographic proximity score
    Closer = better (shorter cold ischemia time)
    """
    if distance_miles <= 50:
        return 100
    elif distance_miles <= 150:
        return 80
    elif distance_miles <= 500:
        return 60
    elif distance_miles <= 1000:
        return 40
    else:
        return 20

def calculate_epts_score(patient_age, diabetes, prior_transplant, dialysis_time):
    """
    Calculate EPTS (Estimated Post-Transplant Survival) Score
    Lower score = better expected survival
    """
    score = 0
    score += patient_age * 0.4
    score += (20 if diabetes else 0)
    score += (10 if prior_transplant else 0)
    score += min(dialysis_time / 365, 5) * 3
    return min(score, 100)

def calculate_kdpi_score(donor_age, donor_height, donor_weight, 
                         hypertension, diabetes, creatinine, hcv, dcd):
    """
    Calculate KDPI (Kidney Donor Profile Index)
    Lower KDPI = higher quality kidney
    """
    score = 0
    score += donor_age * 0.5
    score += (15 if hypertension else 0)
    score += (15 if diabetes else 0)
    score += (10 if hcv else 0)
    score += (20 if dcd else 0)
    score += max(0, (creatinine - 1.0) * 10)
    
    # BMI factor
    bmi = (donor_weight * 703) / (donor_height ** 2)
    if bmi > 30:
        score += 10
    
    return min(score, 100)

def calculate_overall_match_score(patient, donor):
    """
    Calculate comprehensive match score based on OPTN criteria
    Combines multiple factors with appropriate weights
    """
    # Blood type compatibility (25% weight)
    blood_score = calculate_blood_type_compatibility(
        patient['blood_type'], donor['blood_type']
    ) * 0.25
    
    # HLA matching (20% weight)
    hla_score = calculate_hla_match_score(
        patient['hla_type'], donor['hla_type']
    ) * 0.20
    
    # CPRA priority (15% weight)
    cpra_score = calculate_cpra_priority(patient['cpra']) * 0.15
    
    # Wait time (15% weight)
    wait_score = calculate_wait_time_points(patient['wait_days']) * 0.15
    
    # Age compatibility (10% weight)
    age_score = calculate_age_compatibility(
        patient['age'], donor['age']
    ) * 0.10
    
    # Geographic distance (10% weight)
    distance_score = calculate_distance_score(patient['distance_miles']) * 0.10
    
    # EPTS/KDPI matching (5% weight)
    # Match low EPTS patients with low KDPI kidneys
    epts = calculate_epts_score(
        patient['age'], patient['diabetes'], 
        patient['prior_transplant'], patient['dialysis_time']
    )
    kdpi = calculate_kdpi_score(
        donor['age'], donor['height'], donor['weight'],
        donor['hypertension'], donor['diabetes'], 
        donor['creatinine'], donor['hcv'], donor['dcd']
    )
    
    # Low EPTS with low KDPI is ideal
    quality_match_score = 100 - abs(epts - kdpi) * 0.05
    
    total_score = (blood_score + hla_score + cpra_score + wait_score + 
                   age_score + distance_score + quality_match_score)
    
    return round(total_score, 2)

def generate_matches(donors, patients):
    """
    Generate matches between donors and patients
    Returns list of matches sorted by compatibility score
    """
    matches = []
    
    for donor in donors:
        if donor['status'] != 'Available':
            continue
            
        donor_matches = []
        for patient in patients:
            if patient['status'] != 'Active':
                continue
            
            # Check basic compatibility
            blood_compat = calculate_blood_type_compatibility(
                patient['blood_type'], donor['blood_type']
            )
            
            if blood_compat > 0:  # Only if blood type compatible
                score = calculate_overall_match_score(patient, donor)
                donor_matches.append({
                    'donor_id': donor['donor_id'],
                    'patient_id': patient['patient_id'],
                    'patient_name': patient['name'],
                    'doctor': patient['doctor'],
                    'score': score,
                    'blood_type_compat': blood_compat,
                    'donor': donor,
                    'patient': patient
                })
        
        # Sort by score (highest first)
        donor_matches.sort(key=lambda x: x['score'], reverse=True)
        matches.extend(donor_matches)
    
    return matches

def create_offer(match):
    """Create an offer with 1-hour expiration"""
    offer = {
        'offer_id': f"OFF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'donor_id': match['donor_id'],
        'patient_id': match['patient_id'],
        'patient_name': match['patient_name'],
        'doctor': match['doctor'],
        'score': match['score'],
        'created_at': datetime.now(),
        'expires_at': datetime.now() + timedelta(hours=1),
        'status': 'Pending',
        'match_details': match
    }
    return offer

def login_page():
    """Display login page"""
    st.title("🫘 Kidney Donor Matching System")
    st.subheader("Healthcare Professional Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Login", type="primary", use_container_width=True):
                if login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        with col_b:
            if st.button("Clear", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        st.info("""
        **Demo Credentials:**
        - Username: `dr.smith` | Password: `password123`
        - Username: `dr.johnson` | Password: `password123`
        - Username: `admin` | Password: `admin123`
        """)

def initialize_sample_data():
    """Initialize sample patients and donors"""
    if not st.session_state.patients:
        st.session_state.patients = [
            {
                'patient_id': 'P001',
                'name': 'John Anderson',
                'age': 45,
                'blood_type': 'A',
                'hla_type': ['A1', 'A2', 'B8', 'B44', 'DR3', 'DR4'],
                'cpra': 85,
                'wait_days': 730,
                'diabetes': True,
                'prior_transplant': False,
                'dialysis_time': 547,
                'distance_miles': 25,
                'doctor': 'dr.smith',
                'status': 'Active'
            },
            {
                'patient_id': 'P002',
                'name': 'Sarah Martinez',
                'age': 32,
                'blood_type': 'O',
                'hla_type': ['A3', 'A24', 'B7', 'B35', 'DR1', 'DR15'],
                'cpra': 95,
                'wait_days': 1095,
                'diabetes': False,
                'prior_transplant': True,
                'dialysis_time': 821,
                'distance_miles': 45,
                'doctor': 'dr.johnson',
                'status': 'Active'
            },
            {
                'patient_id': 'P003',
                'name': 'Michael Chen',
                'age': 58,
                'blood_type': 'B',
                'hla_type': ['A2', 'A11', 'B44', 'B51', 'DR4', 'DR7'],
                'cpra': 15,
                'wait_days': 365,
                'diabetes': False,
                'prior_transplant': False,
                'dialysis_time': 273,
                'distance_miles': 120,
                'doctor': 'dr.smith',
                'status': 'Active'
            },
            {
                'patient_id': 'P004',
                'name': 'Emily Thompson',
                'age': 28,
                'blood_type': 'AB',
                'hla_type': ['A1', 'A3', 'B8', 'B7', 'DR3', 'DR1'],
                'cpra': 42,
                'wait_days': 180,
                'diabetes': False,
                'prior_transplant': False,
                'dialysis_time': 91,
                'distance_miles': 75,
                'doctor': 'dr.johnson',
                'status': 'Active'
            }
        ]
    
    if not st.session_state.donors:
        st.session_state.donors = [
            {
                'donor_id': 'D001',
                'age': 42,
                'blood_type': 'O',
                'hla_type': ['A1', 'A2', 'B8', 'B35', 'DR3', 'DR15'],
                'height': 68,
                'weight': 170,
                'hypertension': False,
                'diabetes': False,
                'creatinine': 1.1,
                'hcv': False,
                'dcd': False,
                'status': 'Available',
                'procurement_time': datetime.now()
            },
            {
                'donor_id': 'D002',
                'age': 35,
                'blood_type': 'A',
                'hla_type': ['A1', 'A3', 'B7', 'B44', 'DR4', 'DR7'],
                'height': 65,
                'weight': 145,
                'hypertension': False,
                'diabetes': False,
                'creatinine': 0.9,
                'hcv': False,
                'dcd': False,
                'status': 'Available',
                'procurement_time': datetime.now()
            }
        ]

def dashboard_page():
    """Main dashboard for logged-in users"""
    st.title("🫘 Kidney Donor Matching System")
    st.subheader(f"Welcome, {st.session_state.username}")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Dashboard", "Active Offers", "Patient Waitlist", "Available Donors", "Match Analysis"]
        )
        
        st.markdown("---")
        if st.button("Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    # Initialize sample data
    initialize_sample_data()
    
    if page == "Dashboard":
        show_dashboard()
    elif page == "Active Offers":
        show_active_offers()
    elif page == "Patient Waitlist":
        show_patient_waitlist()
    elif page == "Available Donors":
        show_available_donors()
    elif page == "Match Analysis":
        show_match_analysis()

def show_dashboard():
    """Display main dashboard with statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    active_patients = len([p for p in st.session_state.patients if p['status'] == 'Active'])
    available_donors = len([d for d in st.session_state.donors if d['status'] == 'Available'])
    pending_offers = len([o for o in st.session_state.offers if o['status'] == 'Pending'])
    
    with col1:
        st.metric("Active Patients", active_patients)
    with col2:
        st.metric("Available Donors", available_donors)
    with col3:
        st.metric("Pending Offers", pending_offers)
    with col4:
        st.metric("Successful Matches", len([o for o in st.session_state.offers if o['status'] == 'Accepted']))
    
    st.markdown("---")
    
    # Generate matches button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Generate New Matches", type="primary", use_container_width=True):
            matches = generate_matches(st.session_state.donors, st.session_state.patients)
            st.session_state.matches = matches
            st.success(f"Generated {len(matches)} potential matches!")
            st.rerun()
    
    # Display recent matches
    if st.session_state.matches:
        st.subheader("Top Matches")
        
        # Show top 10 matches
        top_matches = st.session_state.matches[:10]
        
        for i, match in enumerate(top_matches):
            with st.expander(f"#{i+1} - {match['patient_name']} (Patient ID: {match['patient_id']}) ← Donor {match['donor_id']} | Score: {match['score']:.2f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Patient Information**")
                    st.write(f"Name: {match['patient_name']}")
                    st.write(f"Blood Type: {match['patient']['blood_type']}")
                    st.write(f"Age: {match['patient']['age']}")
                    st.write(f"CPRA: {match['patient']['cpra']}%")
                    st.write(f"Wait Time: {match['patient']['wait_days']} days")
                    st.write(f"Attending Doctor: {match['doctor']}")
                
                with col2:
                    st.markdown("**Donor Information**")
                    st.write(f"Donor ID: {match['donor_id']}")
                    st.write(f"Blood Type: {match['donor']['blood_type']}")
                    st.write(f"Age: {match['donor']['age']}")
                    kdpi = calculate_kdpi_score(
                        match['donor']['age'], match['donor']['height'], 
                        match['donor']['weight'], match['donor']['hypertension'],
                        match['donor']['diabetes'], match['donor']['creatinine'],
                        match['donor']['hcv'], match['donor']['dcd']
                    )
                    st.write(f"KDPI Score: {kdpi:.1f}%")
                
                st.markdown("**Match Details**")
                st.progress(match['score'] / 100, text=f"Overall Match Score: {match['score']:.2f}/100")
                
                if st.button(f"Send Offer to {match['doctor']}", key=f"offer_{i}"):
                    # Check if offer already exists for this patient
                    existing_offer = any(
                        o['patient_id'] == match['patient_id'] and o['status'] == 'Pending'
                        for o in st.session_state.offers
                    )
                    
                    if not existing_offer:
                        offer = create_offer(match)
                        st.session_state.offers.append(offer)
                        st.success(f"Offer {offer['offer_id']} sent to {match['doctor']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("An active offer already exists for this patient.")

def show_active_offers():
    """Display active offers with countdown timers"""
    st.subheader("Active Offers")
    
    # Filter offers for current doctor or show all for admin
    if st.session_state.username == 'admin':
        relevant_offers = st.session_state.offers
    else:
        relevant_offers = [o for o in st.session_state.offers if o['doctor'] == st.session_state.username]
    
    pending_offers = [o for o in relevant_offers if o['status'] == 'Pending']
    
    if not pending_offers:
        st.info("No active offers at this time.")
        return
    
    for offer in pending_offers:
        time_remaining = offer['expires_at'] - datetime.now()
        
        if time_remaining.total_seconds() <= 0:
            # Offer expired
            offer['status'] = 'Expired'
            st.warning(f"Offer {offer['offer_id']} has expired.")
            continue
        
        minutes_remaining = int(time_remaining.total_seconds() / 60)
        
        with st.container():
            st.markdown(f"### Offer {offer['offer_id']}")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Patient:** {offer['patient_name']} ({offer['patient_id']})")
                st.write(f"**Donor:** {offer['donor_id']}")
                st.write(f"**Match Score:** {offer['score']:.2f}/100")
            
            with col2:
                st.write(f"**Doctor:** {offer['doctor']}")
                st.write(f"**Created:** {offer['created_at'].strftime('%Y-%m-%d %H:%M')}")
                
                if minutes_remaining <= 10:
                    st.error(f"⏰ **Time Remaining:** {minutes_remaining} minutes")
                else:
                    st.info(f"⏰ **Time Remaining:** {minutes_remaining} minutes")
            
            with col3:
                if st.button("✅ Accept", key=f"accept_{offer['offer_id']}", type="primary"):
                    offer['status'] = 'Accepted'
                    offer['response_time'] = datetime.now()
                    
                    # Update donor status
                    for donor in st.session_state.donors:
                        if donor['donor_id'] == offer['donor_id']:
                            donor['status'] = 'Allocated'
                    
                    # Update patient status
                    for patient in st.session_state.patients:
                        if patient['patient_id'] == offer['patient_id']:
                            patient['status'] = 'Matched'
                    
                    st.success("Offer accepted! Initiating organ transport protocol...")
                    time.sleep(2)
                    st.rerun()
                
                if st.button("❌ Reject", key=f"reject_{offer['offer_id']}"):
                    offer['status'] = 'Rejected'
                    offer['response_time'] = datetime.now()
                    st.info("Offer rejected. Moving to next patient...")
                    time.sleep(1)
                    st.rerun()
            
            st.markdown("---")
    
    # Show offer history
    st.subheader("Offer History")
    completed_offers = [o for o in relevant_offers if o['status'] in ['Accepted', 'Rejected', 'Expired']]
    
    if completed_offers:
        history_data = []
        for offer in completed_offers:
            history_data.append({
                'Offer ID': offer['offer_id'],
                'Patient': offer['patient_name'],
                'Donor': offer['donor_id'],
                'Score': f"{offer['score']:.2f}",
                'Status': offer['status'],
                'Created': offer['created_at'].strftime('%Y-%m-%d %H:%M'),
                'Response Time': offer.get('response_time', 'N/A').strftime('%Y-%m-%d %H:%M') if offer.get('response_time') != 'N/A' else 'N/A'
            })
        
        st.dataframe(pd.DataFrame(history_data), use_container_width=True)

def show_patient_waitlist():
    """Display patient waitlist"""
    st.subheader("Patient Waitlist")
    
    if not st.session_state.patients:
        st.info("No patients in the waitlist.")
        return
    
    # Filter patients by doctor (except admin)
    if st.session_state.username == 'admin':
        patients = st.session_state.patients
    else:
        patients = [p for p in st.session_state.patients if p['doctor'] == st.session_state.username]
    
    patient_data = []
    for patient in patients:
        epts = calculate_epts_score(
            patient['age'], patient['diabetes'],
            patient['prior_transplant'], patient['dialysis_time']
        )
        
        patient_data.append({
            'ID': patient['patient_id'],
            'Name': patient['name'],
            'Age': patient['age'],
            'Blood Type': patient['blood_type'],
            'CPRA %': patient['cpra'],
            'Wait Days': patient['wait_days'],
            'EPTS Score': f"{epts:.1f}",
            'Status': patient['status'],
            'Doctor': patient['doctor']
        })
    
    df = pd.DataFrame(patient_data)
    st.dataframe(df, use_container_width=True)

def show_available_donors():
    """Display available donors"""
    st.subheader("Available Kidney Donors")
    
    available = [d for d in st.session_state.donors if d['status'] == 'Available']
    
    if not available:
        st.info("No donors currently available.")
        return
    
    donor_data = []
    for donor in available:
        kdpi = calculate_kdpi_score(
            donor['age'], donor['height'], donor['weight'],
            donor['hypertension'], donor['diabetes'],
            donor['creatinine'], donor['hcv'], donor['dcd']
        )
        
        donor_data.append({
            'Donor ID': donor['donor_id'],
            'Age': donor['age'],
            'Blood Type': donor['blood_type'],
            'KDPI %': f"{kdpi:.1f}",
            'Height (in)': donor['height'],
            'Weight (lbs)': donor['weight'],
            'Creatinine': donor['creatinine'],
            'Status': donor['status']
        })
    
    df = pd.DataFrame(donor_data)
    st.dataframe(df, use_container_width=True)

def show_match_analysis():
    """Display detailed match analysis"""
    st.subheader("Match Analysis & Compatibility Factors")
    
    st.markdown("""
    ### OPTN Kidney Allocation Criteria
    
    This system considers the following factors based on OPTN Policy (pages 147-177):
    
    1. **Blood Type Compatibility (25% weight)**
       - ABO blood type matching
       - O donors are universal; AB recipients are universal
    
    2. **HLA Matching (20% weight)**
       - Human Leukocyte Antigen matching (6 antigens: A, B, DR)
       - Better matching improves long-term graft survival
    
    3. **CPRA Priority (15% weight)**
       - Calculated Panel Reactive Antibody
       - Highly sensitized patients (CPRA ≥98%) receive priority
    
    4. **Waiting Time (15% weight)**
       - Time on dialysis and waitlist
       - Longer wait = higher priority
    
    5. **Age Matching (10% weight)**
       - Pediatric priority
       - Age-appropriate matching for optimal outcomes
    
    6. **Geographic Distance (10% weight)**
       - Minimize cold ischemia time
       - Local allocation priority
    
    7. **EPTS/KDPI Matching (5% weight)**
       - Estimated Post-Transplant Survival (patient)
       - Kidney Donor Profile Index (donor quality)
       - Best organs go to patients with best expected survival
    """)
    
    if st.session_state.matches:
        st.markdown("---")
        st.subheader("Current Match Statistics")
        
        scores = [m['score'] for m in st.session_state.matches]
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Average Match Score", f"{np.mean(scores):.2f}")
        with col2:
            st.metric("Highest Match Score", f"{np.max(scores):.2f}")
        with col3:
            st.metric("Total Matches", len(st.session_state.matches))

def main():
    """Main application entry point"""
    if not st.session_state.logged_in:
        login_page()
    else:
        dashboard_page()

if __name__ == "__main__":
    main()
