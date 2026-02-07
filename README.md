# Kidney Donor to Patient Matching System

A comprehensive web-based application for managing kidney transplant matching based on OPTN (Organ Procurement and Transplantation Network) Policy guidelines (pages 147-177).

## 🎯 Overview

This system automates the kidney allocation process by:
- Organizing patients on the waitlist
- Matching available kidney organs with compatible recipients
- Calculating compatibility scores based on multiple clinical factors
- Sending time-limited offers (1 hour) to physicians
- Managing acceptance/rejection workflow
- Automatically moving to the next patient upon rejection

## 🏥 Features

### Patient Management
- Comprehensive patient waitlist tracking
- Patient demographics and clinical data
- Wait time calculation
- Status monitoring (Active, Matched, etc.)

### Donor Management
- Available kidney donor registry
- Donor clinical characteristics
- KDPI (Kidney Donor Profile Index) scoring
- Allocation status tracking

### Matching Algorithm
The system implements OPTN-based matching criteria with weighted scoring:

1. **Blood Type Compatibility (25% weight)**
   - ABO matching rules
   - Universal donor/recipient considerations

2. **HLA Matching (20% weight)**
   - 6-antigen matching (HLA-A, HLA-B, HLA-DR)
   - Improved long-term graft survival

3. **CPRA Priority (15% weight)**
   - Calculated Panel Reactive Antibody
   - Priority for highly sensitized patients (CPRA ≥98%)

4. **Waiting Time (15% weight)**
   - Time on dialysis
   - Waitlist duration

5. **Age Compatibility (10% weight)**
   - Age-appropriate matching
   - Pediatric priority

6. **Geographic Distance (10% weight)**
   - Minimizing cold ischemia time
   - Local allocation preference

7. **EPTS/KDPI Matching (5% weight)**
   - Estimated Post-Transplant Survival (patient)
   - Kidney quality assessment (donor)

### Offer Management
- **1-Hour Time Limit**: Each offer expires after 60 minutes
- **Real-time Countdown**: Visual timer showing remaining time
- **Accept/Reject Workflow**: Simple physician interface
- **Automatic Escalation**: Rejected offers automatically move to next compatible patient
- **Offer History**: Complete audit trail of all offers

### Security
- Healthcare professional authentication
- Role-based access (doctor/admin)
- Secure password hashing (SHA-256)
- Session management

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Web browser (Chrome, Firefox, Safari, or Edge)

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd kidney-matching-system
```

Or download and extract the ZIP file.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will automatically open in your default web browser at `http://localhost:8501`

## 👤 User Credentials

### Demo Accounts

The system comes with three pre-configured accounts for testing:

| Username | Password | Role |
|----------|----------|------|
| dr.smith | password123 | Physician |
| dr.johnson | password123 | Physician |
| admin | admin123 | Administrator |

**⚠️ Security Note**: In production, change these default credentials and implement proper password policies.

## 📖 Usage Guide

### For Healthcare Professionals

#### 1. Login
- Navigate to the application URL
- Enter your username and password
- Click "Login"

#### 2. Dashboard
- View system statistics (active patients, available donors, pending offers)
- Click "Generate New Matches" to create compatibility rankings
- Review top matches with detailed scoring

#### 3. Sending Offers
- From the Dashboard, review the top matches
- Expand a match to see detailed patient and donor information
- Click "Send Offer to [doctor]" to create a time-limited offer
- The offer will be sent to the patient's attending physician

#### 4. Managing Offers (Active Offers Page)
- View all pending offers assigned to you
- Monitor countdown timers (offers expire in 1 hour)
- **Accept**: Initiates organ transport protocol
  - Updates patient status to "Matched"
  - Updates donor status to "Allocated"
  - Records acceptance timestamp
- **Reject**: Moves to next compatible patient
  - Offer marked as rejected
  - Organ remains available for next match

#### 5. Patient Waitlist
- View all patients under your care
- Review patient clinical data and wait times
- Monitor EPTS scores and compatibility factors

#### 6. Available Donors
- See all available kidney donors
- Review donor characteristics and KDPI scores
- Check organ quality metrics

#### 7. Match Analysis
- Understand the OPTN-based matching criteria
- Review system algorithms and scoring weights
- View current match statistics

### For Administrators

Administrators have access to all features plus:
- View all patients across all physicians
- View all offers system-wide
- Monitor system-wide statistics
- Oversee allocation efficiency

## 🔧 Configuration

### Adding New Users

Edit the `USERS` dictionary in `app.py`:

```python
USERS = {
    'username': hashlib.sha256('password'.encode()).hexdigest(),
    # Add more users here
}
```

### Adjusting Matching Weights

Modify the weights in the `calculate_overall_match_score()` function:

```python
blood_score = calculate_blood_type_compatibility(...) * 0.25  # 25% weight
hla_score = calculate_hla_match_score(...) * 0.20  # 20% weight
# Adjust these multipliers as needed
```

### Changing Offer Expiration Time

Modify the `create_offer()` function:

```python
'expires_at': datetime.now() + timedelta(hours=1),  # Change hours as needed
```

## 📊 Sample Data

The system includes sample data for demonstration:
- 4 sample patients with varying clinical profiles
- 2 sample donors with different characteristics
- Diverse CPRA levels, wait times, and age ranges

### Adding Custom Data

Patients and donors can be added programmatically by modifying the `initialize_sample_data()` function or by implementing data import functionality.

## 🏗️ System Architecture

```
app.py
├── Authentication Module
├── Matching Algorithm
│   ├── Blood Type Compatibility
│   ├── HLA Matching
│   ├── CPRA Scoring
│   ├── Wait Time Points
│   ├── Age Compatibility
│   ├── Distance Scoring
│   └── EPTS/KDPI Matching
├── Offer Management
│   ├── Offer Creation
│   ├── Expiration Tracking
│   └── Accept/Reject Workflow
└── User Interface
    ├── Login Page
    ├── Dashboard
    ├── Active Offers
    ├── Patient Waitlist
    ├── Available Donors
    └── Match Analysis
```

## 📝 OPTN Policy Compliance

This system implements kidney allocation criteria based on OPTN Policy sections 147-177:

- **Section 8.5**: Allocation of Kidneys
- **Section 8.5.A**: Blood Type Compatibility
- **Section 8.5.B**: HLA Matching Requirements
- **Section 8.5.C**: Calculated Panel Reactive Antibody (CPRA)
- **Section 8.5.D**: Waiting Time
- **Section 8.5.E**: Pediatric Candidates
- **Section 8.5.F**: Estimated Post-Transplant Survival (EPTS)
- **Section 8.5.G**: Kidney Donor Profile Index (KDPI)
- **Section 8.5.H**: Geographic Distribution

## ⚠️ Important Notes

### For Development/Testing Use Only

This system is designed for:
- Educational purposes
- Demonstration of OPTN matching principles
- Prototype development
- Training scenarios

### NOT FOR CLINICAL USE

This application is **NOT**:
- FDA approved
- Validated for clinical decision-making
- Compliant with HIPAA or other healthcare regulations
- A replacement for UNOS or established allocation systems

### Production Requirements

For production deployment in a healthcare setting, you must:

1. **Regulatory Compliance**
   - Obtain FDA clearance/approval
   - Ensure HIPAA compliance
   - Meet UNOS integration requirements
   - Follow local healthcare regulations

2. **Security Enhancements**
   - Implement SSL/TLS encryption
   - Use secure database (PostgreSQL, MySQL)
   - Implement proper authentication (OAuth2, SAML)
   - Add audit logging
   - Implement data encryption at rest
   - Add intrusion detection
   - Regular security audits

3. **Data Management**
   - Replace in-memory storage with database
   - Implement data backup and recovery
   - Add data validation and sanitization
   - Ensure data integrity constraints

4. **Clinical Validation**
   - Validate matching algorithm with clinical experts
   - Conduct comparative studies with existing systems
   - Peer review of scoring methodology
   - Clinical trials and testing

5. **Integration**
   - UNOS system integration
   - EHR/EMR integration
   - Laboratory systems integration
   - Tissue typing databases

## 🛠️ Troubleshooting

### Application Won't Start
- Ensure Python 3.8+ is installed: `python --version`
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check for port conflicts (default port 8501)

### Login Issues
- Verify credentials match demo accounts
- Clear browser cache and cookies
- Check console for error messages

### Matches Not Generating
- Ensure sample data is initialized
- Check that donors have "Available" status
- Check that patients have "Active" status
- Verify blood type compatibility exists

### Offers Not Appearing
- Check that you're logged in as the correct doctor
- Verify offer was created successfully
- Check offer expiration status
- Refresh the page

## 📈 Future Enhancements

Potential improvements for production version:
- Database integration (PostgreSQL)
- Email/SMS notifications for offers
- Mobile application
- Real-time websocket updates
- Advanced reporting and analytics
- Integration with tissue typing systems
- Automated organ transport coordination
- Multi-organ allocation support
- Transplant outcome tracking
- Machine learning for outcome prediction

## 📄 License

This project is provided as-is for educational and demonstration purposes.

## 👥 Support

For questions or issues:
1. Check this README thoroughly
2. Review the code comments
3. Consult OPTN policy documentation
4. Contact your system administrator

## 🙏 Acknowledgments

- OPTN/UNOS for kidney allocation policy guidelines
- Streamlit for the web application framework
- Medical professionals who provided domain expertise

---

**Disclaimer**: This is a demonstration system. It should not be used for actual clinical decision-making. Always consult with qualified healthcare professionals and use officially approved allocation systems for real kidney transplant matching.
