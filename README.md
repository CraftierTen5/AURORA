# AURORA — Aircraft & Unified Runway Operations Records Archive

**ARTOS 2.0 Extension**

AURORA extends ARTOS 2.0 into a relational database-driven airport operations management system built using **Python, Pygame, and MySQL**.

The system manages aircraft, airlines, airports, flight schedules, runway infrastructure, and manual runway assignments.

### Core Features
- Relational database with 18 tables, foreign-key constraints, indexes, and views.
- Manual runway assignment with validation against airport alignment, landing/takeoff permissions, aircraft-runway compatibility, runway status, and operational restrictions.
- Database triggers for assignment audit logging.
- SQL queries demonstrating joins, aggregation, anti-joins, and relational views.
- Database-backed ARTOS radar visualization and airport infrastructure management.

### Tech Stack
Python · Pygame · MySQL 8.0+ · InnoDB · SQL

### Setup
1. Install dependencies using `pip install -r requirements.txt`.
2. Configure MySQL credentials in `.env`.
3. Initialize the database using `python database/setup_db.py`.
4. Launch using `python main.py`.

**Scope:** AURORA supports manual, rule-based runway assignment. It is an academic DBMS project, not a certified air traffic control system.
