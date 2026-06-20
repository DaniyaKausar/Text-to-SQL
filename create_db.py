import sqlite3
import os

# Create the data folder path
DB_PATH = "data/company.db"

def create_database():
    """Creates a sample company database with realistic data"""
    
    # Connect to SQLite (creates the file automatically if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── TABLE 1: employees ──────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            department  TEXT NOT NULL,
            salary      REAL NOT NULL,
            hire_date   TEXT NOT NULL,
            email       TEXT UNIQUE NOT NULL
        )
    """)

    # ── TABLE 2: departments ────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            budget      REAL NOT NULL,
            manager     TEXT NOT NULL,
            location    TEXT NOT NULL
        )
    """)

    # ── TABLE 3: sales ──────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id   INTEGER NOT NULL,
            product       TEXT NOT NULL,
            amount        REAL NOT NULL,
            sale_date     TEXT NOT NULL,
            region        TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)

    # ── TABLE 4: products ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            category    TEXT NOT NULL,
            price       REAL NOT NULL,
            stock       INTEGER NOT NULL
        )
    """)

    # ── SEED DATA: employees ────────────────────────────────────────
    employees = [
        ("Alice Johnson",   "Engineering",  95000, "2021-03-15", "alice@company.com"),
        ("Bob Smith",       "Sales",        72000, "2020-07-01", "bob@company.com"),
        ("Carol White",     "Marketing",    68000, "2022-01-10", "carol@company.com"),
        ("David Brown",     "Engineering",  105000,"2019-11-20", "david@company.com"),
        ("Eva Martinez",    "HR",           61000, "2023-02-28", "eva@company.com"),
        ("Frank Lee",       "Sales",        78000, "2021-08-15", "frank@company.com"),
        ("Grace Kim",       "Engineering",  98000, "2020-04-01", "grace@company.com"),
        ("Henry Wilson",    "Marketing",    71000, "2022-09-12", "henry@company.com"),
        ("Iris Chen",       "Sales",        75000, "2021-05-20", "iris@company.com"),
        ("Jack Taylor",     "Engineering",  110000,"2018-06-30", "jack@company.com"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO employees (name, department, salary, hire_date, email)
        VALUES (?, ?, ?, ?, ?)
    """, employees)

    # ── SEED DATA: departments ──────────────────────────────────────
    departments = [
        ("Engineering",  850000, "Jack Taylor",   "New York"),
        ("Sales",        620000, "Bob Smith",      "Chicago"),
        ("Marketing",    430000, "Henry Wilson",   "Los Angeles"),
        ("HR",           280000, "Eva Martinez",   "New York"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO departments (name, budget, manager, location)
        VALUES (?, ?, ?, ?)
    """, departments)

    # ── SEED DATA: products ─────────────────────────────────────────
    products = [
        ("Laptop Pro",      "Electronics",  1299.99, 45),
        ("Wireless Mouse",  "Electronics",   29.99,  200),
        ("Standing Desk",   "Furniture",    499.99,  30),
        ("Office Chair",    "Furniture",    349.99,  55),
        ("Monitor 27inch",  "Electronics",  399.99,  80),
        ("Keyboard",        "Electronics",   79.99,  150),
        ("Webcam HD",       "Electronics",   89.99,  95),
        ("Notebook Pack",   "Stationery",    12.99,  500),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO products (name, category, price, stock)
        VALUES (?, ?, ?, ?)
    """, products)

    # ── SEED DATA: sales ────────────────────────────────────────────
    sales = [
        (2,  "Laptop Pro",     2599.98, "2024-01-15", "North"),
        (6,  "Monitor 27inch", 1199.97, "2024-01-22", "South"),
        (9,  "Standing Desk",   999.98, "2024-02-05", "East"),
        (2,  "Office Chair",    699.98, "2024-02-14", "North"),
        (6,  "Laptop Pro",     1299.99, "2024-02-28", "West"),
        (9,  "Webcam HD",       269.97, "2024-03-10", "South"),
        (2,  "Keyboard",        239.97, "2024-03-18", "North"),
        (6,  "Wireless Mouse",  149.95, "2024-04-02", "East"),
        (9,  "Laptop Pro",     3899.97, "2024-04-15", "West"),
        (2,  "Monitor 27inch",  799.98, "2024-05-01", "South"),
        (6,  "Standing Desk",  1499.97, "2024-05-20", "North"),
        (9,  "Office Chair",    349.99, "2024-06-08", "East"),
        (2,  "Webcam HD",       179.98, "2024-06-25", "West"),
        (6,  "Laptop Pro",     2599.98, "2024-07-14", "North"),
        (9,  "Keyboard",        159.98, "2024-07-30", "South"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO sales (employee_id, product, amount, sale_date, region)
        VALUES (?, ?, ?, ?, ?)
    """, sales)

    # Save everything
    conn.commit()
    conn.close()

    print("✅ Database created successfully at:", DB_PATH)
    print("   Tables: employees, departments, sales, products")
    print("   Rows inserted: 10 employees, 4 departments, 8 products, 15 sales")

if __name__ == "__main__":
    create_database()