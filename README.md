
# Secure Online Examination System

## Overview
A Flask-based Network Security mini project that demonstrates
secure student authentication and an online multiple-choice examination.

## Objectives
- Protect student accounts with password hashing.
- Prevent cross-site request forgery (CSRF).
- Demonstrate session-based authentication and route protection.
- Use parameterized SQLite queries.
- Calculate exam scores on the server.
- Prevent duplicate result records.
- Record important security events.

## Technologies
- Python
- Flask
- Flask-WTF
- SQLite
- HTML, CSS and JavaScript
- Git and GitHub

## Project Structure
- app.py: Flask routes and application logic
- database.py: SQLite tables and sample questions
- security.py: Security event logging
- templates/: HTML pages
- static/: CSS and JavaScript
- instance/exam.db: Automatically generated database

## Installation on Windows
1. Install Python 3.11 or newer and Git.
2. Create and activate a virtual environment.
3. Install requirements using pip.
4. Copy .env.example to .env.
5. Set SECRET_KEY to a long random secret.
6. Run python app.py.
7. Open http://127.0.0.1:5000 in your browser.

## Security Concepts Demonstrated
- Password hashing
- CSRF protection
- Session cookies
- SQL injection prevention through parameterized queries
- Server-side authorization and score calculation
- Security headers
- Security event logging

## Testing
- Register and log in.
- Try opening /dashboard without logging in.
- Complete and submit the quiz.
- Verify that the result is saved.
- Try submitting the examination a second time.
- Check security.log for authentication and submission events.

## Limitations
This is an educational prototype. It does not provide a
production-grade proctoring system, administrator interface,
distributed rate limiting, or hardened exam timing.

## Academic Use
Created for a Network Security mini project.
