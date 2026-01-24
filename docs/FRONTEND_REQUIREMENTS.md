# ZNPHI ImpTracker – Frontend UI Requirements

## 1. Purpose
This document defines the frontend (UI/UX) requirements for the ZNPHI ImpTracker system.
It guides developers in implementing a production-grade, role-aware, responsive user interface.

---

## 2. Design Principles
- Clean, professional, government-grade interface
- Mobile-first, fully responsive
- Tailwind CSS for styling
- Django templates (no admin dependency for users)
- Clear role-based navigation

---

## 3. Authentication & Session Management

### 3.1 Login Page
Route: /login/

- Username & password fields
- Validation & error messages
- Redirect to dashboard on success

### 3.2 Logout
Route: /logout/

- Terminates session
- Redirects to login page

---

## 4. Global Layout

### 4.1 Navigation Bar
- System name
- Logged-in user
- Logout

### 4.2 Sidebar (Role-Aware)
- Dashboard
- Activities
- Excel Upload/Download
- Reports
- Users (User Managers)
- Master Data (Admins)

---

## 5. Dashboard Views

### 5.1 Main Dashboard
Route: /dashboard/

- Total activities
- Activities by status
- Budget summary
- Filters (year, cluster, funder)

### 5.2 Officer Dashboard
- Activities assigned to logged-in user
- Status summary

---

## 6. Activity Management

### 6.1 Activity List
Route: /activities/

- Search & filters
- Read-only for viewers

### 6.2 Activity Detail
Route: /activities/<id>/

- View full details
- Editable fields based on role

---

## 7. Excel Operations

### 7.1 Download Template
Route: /excel/template/

- Year selection
- Protected headers
- Dropdowns

### 7.2 Upload Activities
Route: /excel/upload/

- File upload
- Validation results
- Partial success handling

---

## 8. Reporting

### 8.1 Export Activities
Route: /reports/export/

- Filtered Excel export

---

## 9. User & Role Management

### 9.1 User List
Route: /users/

- Create users
- Assign roles & clusters

---

## 10. Master Data Management
Routes:
- /masters/funders/
- /masters/clusters/
- /masters/statuses/

(Admin-only)

---

## 11. Audit Logs

Route: /audit/

- View user actions and uploads

---

## 12. Acceptance Criteria
- All listed views implemented
- Responsive UI
- RBAC enforced
- Clear error handling

---

Document: FRONTEND_REQUIREMENTS.md
System: ZNPHI ImpTracker
Version: 1.0
