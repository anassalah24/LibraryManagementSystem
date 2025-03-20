# Library Management System

Welcome to Siemens Library Management System (SLMS)! This is a full-featured web application built with Flask, designed to streamline library operations. The system allows members to search for books, check out, reserve, renew, and return them , notifcations , view their history and due fines and edit their profiles, while librarians have tools to manage the collection and membership. It also features barcode identification for book copies and memberships and a primitive chatbot for personalized book recommendations.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technologies and Tools](#technologies-and-tools)
3. [Setup and Installation](#setup-and-installation)
4. [Database Schema](#database-schema)
5. [API Documentation](#api-documentation)
6. [Testing](#testing)

---

## Project Overview

The Library Management System (LMS) is a Flask-based web application designed to streamline library operations for both members and librarians. Key features include:

- **User Management & Authentication**
  - Registration, login, and role-based access
  - Membership cancellation and reactivation

- **Book Management**
  - CRUD operations for books
  - Multiple copies per book with unique barcode generation

- **Search & Catalog**
  - Advanced search by title, author, subject, and publication date range

- **Transactions**
  - Book checkout, renewal (with overdue restrictions), and return with fine calculation

- **Reservations & Notifications**
  - Book reservations when no copies are available
  - Automated email notifications for overdue items and available reservations

- **Chatbot Recommendations**
  - Floating chatbot for personalized book recommendations using keyword extraction and spell correction

- **Real-Time Updates**
  - AJAX polling for dynamic dashboard refresh

- **Testing & Validation**
  - Comprehensive Test Suite to test functionality and edge cases


## Technologies and Tools

- **Backend:**
  - Flask (Python) for handling API requests, session management, and business logic.
  - Flask-RESTful for structuring RESTful API endpoints.
  - SQLAlchemy (ORM) for database management.
  - Flask-Mail for sending email notifications.

- **Frontend:**
  - HTML5 & CSS3 for page structure and styling.
  - Bootstrap 4 for responsive UI design.
  - JavaScript & jQuery for interactivity and AJAX-based dynamic content updates.

- **Database:**
  - SQLite used as the primary database for storing books, users, transactions, and reservations.

- **Libraries & Tools:**
  - **Flask Extensions:**
    - APScheduler (Task scheduling)
  - **Python Libraries:**
    - Werkzeug (for password hashing)
    - sentence-transformers (for embedding user prompts & book data in chatbot)
    - pyspellchecker (for correcting spelling mistakes in chatbot prompts)
    - python-barcode (for generating book copy and member barcodes)
    - Pillow (for image handling)
  - **Testing Framework:**
    - Pytest (unit, integration, edge-case tests)
    - unittest.mock (patching external services like email)
  - **Version Control:**
    - Git , GitHub and tortoisegit 


## Setup and Installation

Follow these steps to set up and run the Library Management System locally:

### Prerequisites
- Python 3.8+ (or higher)
- pip (Python package manager)
- Git

### Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/anassalah24/LibraryManagementSystem.git
   cd LibraryManagementSystem
    ```
2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
    ```
3. **Activate the virtual environment:**
   ```bash
   venv\Scripts\activate
    ```
4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
    ```
5. **Run Script for easier testing:**
   ```bash
   TesterSetup.py
    ```
    A setup script named `TesterSetup.py` is provided to reset the database, enroll test users (one librarian and two members), and create a diverse collection of books.Users Info for login: (ofcourse you can register a new user as well)

    **Username:** `librarian`  
    **Email:** `librarian@library.com`  
    **Password:** `securepass`
    
    **Member 1:**  
    **Username:** `member1`  
    **Email:** `member1@member.com`  
    **Password:** `securepass`

    **Member 2:**  
    **Username:** `member2`  
    **Email:** `member2@member.com`  
    **Password:** `securepass`
   
6. **Run the Application:**
   ```bash
   python run.py
    ```
7. **Access the Application:**
   ```bash
    http://localhost:5000
    ```

**Notes:**
- If you want to test multiple users simultaneously, please use two different browsers or incognito/private windows. This is necessary because a single browser session can only maintain one active user session at a time.


## Database Schema

- **User**
  - **Fields:**  
    - `id`: Primary Key, Integer  
    - `username`: String(100), Unique, Non-Nullable  
    - `email`: String(120), Unique, Non-Nullable  
    - `password`: String(128), Non-Nullable (hashed)  
    - `role`: String(20), Non-Nullable (e.g., "member" or "librarian")  
    - `is_active`: Boolean, Default True
  - **Relationships:**  
    - One-to-many with **Transaction** (a user can have many transactions)  
    - One-to-many with **Reservation** (a user can have many reservations)

- **Book**
  - **Fields:**  
    - `id`: Primary Key, Integer  
    - `title`: String(150), Non-Nullable  
    - `author`: String(100), Non-Nullable  
    - `subject`: String(100), Non-Nullable  
    - `publication_date`: Date, Non-Nullable  
    - `rack_location`: String(50), Non-Nullable
  - **Relationships:**  
    - One-to-many with **BookCopy** (a book can have multiple copies)

- **BookCopy**
  - **Fields:**  
    - `id`: Primary Key, Integer  
    - `book_id`: Foreign Key referencing `books.id`, Non-Nullable  
    - `unique_barcode`: String(50), Unique, Non-Nullable  
    - `status`: String(20), Default "available" (e.g., "available", "checked-out", "reserved")
  - **Relationships:**  
    - Belongs to **Book**

- **Transaction**
  - **Fields:**  
    - `id`: Primary Key, Integer  
    - `user_id`: Foreign Key referencing `users.id`, Non-Nullable  
    - `book_copy_id`: Foreign Key referencing `book_copies.id`, Non-Nullable  
    - `transaction_type`: String(20), Non-Nullable (e.g., "checkout", "renew", "returned")  
    - `date_issued`: DateTime, Default `datetime.utcnow`  
    - `due_date`: DateTime, Non-Nullable  
    - `date_returned`: DateTime, Nullable  
    - `fine_amount`: Float, Default 0.0
  - **Relationships:**  
    - Belongs to **User**  
    - Belongs to **BookCopy**

- **Reservation**
  - **Fields:**  
    - `id`: Primary Key, Integer  
    - `user_id`: Foreign Key referencing `users.id`, Non-Nullable  
    - `book_id`: Foreign Key referencing `books.id`, Non-Nullable  
    - `reservation_date`: DateTime, Default `datetime.utcnow`  
    - `status`: String(20), Default "active" (e.g., "active", "notified", "cancelled")
  - **Relationships:**  
    - Belongs to **User**  
    - Belongs to **Book**




## API Documentation

This project’s API documentation is primarily embedded within the code itself using descriptive docstrings and inline comments for each endpoint. You can find these in `routes.py`. Each endpoint includes:

- **HTTP Method** (GET, POST, PUT, DELETE)
- **Route/URL** (e.g., `/checkout`, `/books/<int:book_id>`)
- **Purpose/Use Case** (e.g., checking out a book, updating a book’s details)
- **Required/Optional Parameters** (e.g., `user_id`, `book_id`, JSON payload structure)
- **Expected Response** (success/failure messages, status codes, sample JSON)

### Locating the Documentation

1. **`routes.py`**  
   - Each Flask route (e.g., `@main.route('/checkout', methods=['POST'])`) is accompanied by comments or docstrings describing the endpoint’s purpose, input parameters, and example responses.

2. **Docstrings in Other Modules**  
   - For functionality split into utility modules (e.g., chatbot recommendations, notifications), relevant docstrings describe how the logic works and how it integrates with the endpoints.

### Sample Endpoint Documentation (Example)

```python
@main.route('/checkout', methods=['POST'])
def checkout_book():
    """
    Checks out an available copy of a book to a member.
    
    Expected JSON payload:
    {
      "user_id": <int>,
      "book_id": <int>
    }
    
    Response:
    201 on success with JSON:
    {
      "message": "Book checked out successfully",
      "transaction_id": <int>,
      "due_date": "<YYYY-MM-DD HH:MM:SS>"
    }
    
    Errors:
    - 400 if missing parameters
    - 404 if no available copies
    - 403 if user session is invalid or membership is inactive
    """
    # Endpoint logic...
```



## Testing

This project uses **pytest** for its automated test suite. All tests are located in the `tests/` directory, with each file focusing on a specific area of the application. Below is an overview of the main test files:

- **`test_auth.py`**  
  Covers user authentication flows, including registration, login (with valid/invalid credentials), and membership status checks.

- **`test_barcode_gen.py`**  
  Verifies barcode generation logic for both books and members, ensuring that barcodes are correctly created and can be decoded if necessary.

- **`test_books.py`**  
  Focuses on book management functionalities such as adding, editing, deleting, and searching for books. It also tests scenarios involving transactions , reservations and overdues.

- **`test_edge_cases.py`**  
  Contains tests for unusual or extreme scenarios, including missing fields, invalid data formats, and operations on non-existent records.

- **`test_integration_flows.py`**  
  Simulates end-to-end user flows, such as checking out a book and returning it, ensuring that multiple endpoints work together correctly in real-world scenarios.

- **`test_inventory.py`**  
  Tests the inventory overview endpoints (e.g., total books, available copies, checked-out copies) to confirm that inventory data is calculated and returned accurately.

- **`test_member_management.py`**  
  Focuses on member-related operations (viewing, editing, canceling, and reactivating memberships) and checks that librarians can manage members properly.

- **`test_notifications.py`**  
  Ensures that notification functionalities work as expected, including overdue notifications and reservation availability emails.

- **`test_profile.py`**  
  Validates profile editing for members, including username/email updates and the display of barcodes on the profile.

For each test file, more detailed information is documented within the code. To run all tests, just run the following command:

```bash
pytest
```
or specify individual files , for example:

```bash
pytest tests/test_auth.py
```




