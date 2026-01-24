# ZNPHI ImpTracker – System Requirements Specification

## 1. Introduction
ZNPHI ImpTracker is a web-based activity planning, implementation tracking, and reporting system designed to support annual and multi-year planning. The system enables structured tracking of activities, budgets, implementation status, and accountability across organizational clusters and funders.

This document defines **production-grade functional and non-functional requirements** to guide system design, development, testing, and deployment.

---

## 2. Objectives
- Provide a centralized system for planning and tracking activities by year
- Enable accountability through responsible officers and audit trails
- Support Excel-based workflows (download templates, bulk upload, export)
- Enable management oversight via dashboards and reports
- Enforce role-based access control
- Be scalable, secure, and maintainable

---

## 3. Target Users
- System Administrators
- User Managers
- Data Managers
- Activity Managers / Responsible Officers
- Read-only Viewers

---

## 4. Functional Requirements

### 4.1 User & Access Management
- The system shall support user authentication via username/password
- The system shall support role-based access control (RBAC)
- A user may have multiple roles
- Roles include:
  - System Admin
  - User Manager
  - Data Manager
  - Activity Manager
  - Viewer
- Users may be associated with one or more organizational clusters
- Only authorized roles may:
  - Create users
  - Assign roles
  - Manage master data

---

### 4.2 Activity Management
- The system shall allow creation, update, and viewing of activities
- Each activity shall be uniquely identified by a system-generated Activity ID
- Activity ID format:
  - Y{YY}-{NNNNNN} (e.g., Y26-000001)
- Activity IDs shall be unique per year
- Activities shall be associated with:
  - Planning year
  - Cluster / unit
  - Funder
  - Implementation status
  - Responsible officer
- The same activity name may exist in multiple years

---

### 4.3 Dates & Scheduling
- Planned Implementation Month shall be stored as a date representing the last day of the selected month
- Quarter shall be auto-derived from Planned Implementation Month
- The system shall support:
  - Actual Start Date
  - Actual Completion Date
- Fully Implemented By date shall be optional

---

### 4.4 Financial Management
- Activities shall store planned budget amounts
- The system shall support multi-currency budgets
- Default currency shall be ZMW
- Balance shall be auto-calculated
- Financial fields shall enforce numeric validation

---

### 4.5 Master Data Configuration
- The system shall provide admin-managed master tables for:
  - Funders (code, name, active flag)
  - Clusters (short name, full name)
  - Implementation Statuses (configurable)
  - Currencies
- Master data changes shall not break historical records

---

### 4.6 Excel Template & Bulk Upload
- The system shall allow users to download a blank Excel template
- The template shall include:
  - Protected headers
  - Data validation
  - Dropdowns for configurable fields
- The system shall allow bulk upload of activities via Excel
- Upload process shall:
  - Require selection of a planning year
  - Validate data before save
  - Save valid rows
  - Reject invalid rows with clear error messages
- Uploads shall be versioned and auditable

---

### 4.7 Reporting & Dashboards
- The system shall provide dashboards showing:
  - Total activities by year
  - Activities by status
  - Activities by cluster and funder
  - Budget summaries (planned, disbursed, balance)
- Dashboards shall respect user permissions
- The system shall support Excel export of filtered activity data

---

### 4.8 Audit & Traceability
- The system shall log:
  - Activity creation and updates
  - Status changes
  - Excel uploads
- Audit logs shall include:
  - User
  - Action
  - Timestamp
  - Affected record

---

## 5. Non-Functional Requirements

### 5.1 Security
- Passwords shall be securely hashed
- Role-based authorization shall be enforced at:
  - View level
  - Data access level
- CSRF protection shall be enabled
- Sensitive actions shall be restricted by role

---

### 5.2 Performance
- The system shall support concurrent users
- Bulk uploads shall handle large Excel files efficiently
- Dashboard queries shall be optimized using indexes and aggregation

---

### 5.3 Scalability & Maintainability
- Modular architecture using Django apps
- Clear separation of concerns
- Codebase shall be extensible without major refactors
- Database schema shall support multi-year growth

---

### 5.4 Usability
- The system shall provide a public-facing UI
- UI shall be responsive and mobile-friendly
- Tailwind CSS shall be used for styling
- Forms shall provide clear validation feedback

---

### 5.5 Deployment
- The system shall run on:
  - Linux (production)
  - Windows (development/testing)
- Database: PostgreSQL
- The system shall support:
  - On-prem deployment
  - Docker-based deployment (future)
- Environment-based configuration shall be supported

---

## 6. Technology Stack
- Backend: Django (Python)
- Database: PostgreSQL
- Frontend: Django Templates + Tailwind CSS
- Excel Processing: openpyxl, pandas
- Authentication: Django Auth
- RBAC: Django Groups & Permissions

---

## 7. Assumptions & Constraints
- Internet access may be limited in production environments
- Excel remains a key workflow tool for users
- Initial version prioritizes correctness and traceability over advanced automation

---

## 8. Future Enhancements (Out of Scope)
- REST APIs for external systems
- Workflow approvals
- Email notifications
- BI integrations
- Advanced analytics & forecasting

---

## 9. Acceptance Criteria
- All functional requirements implemented and tested
- RBAC enforced correctly
- Excel import/export validated
- Dashboards reflect accurate data
- System deployable in production environment

---

**Document Version:** 1.0  
**System:** ZNPHI ImpTracker  
