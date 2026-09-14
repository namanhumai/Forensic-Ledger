import sqlite3
import os

def setup_database():
    print("Setting up Forensic AML Database...")
    if os.path.exists("aml_database.db"):
        os.remove("aml_database.db")
        
    conn = sqlite3.connect("aml_database.db")
    cursor = conn.cursor()

    # Table 1: Financial Transactions
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            amount INTEGER,
            date TEXT
        )
    """)
    
    # Table 2: Shell Company Ownership
    cursor.execute("""
        CREATE TABLE corporate_registry (
            id INTEGER PRIMARY KEY,
            company_name TEXT,
            ultimate_beneficial_owner TEXT,
            registration_country TEXT
        )
    """)
    
    # Table 3: International Watchlist
    cursor.execute("""
        CREATE TABLE sanctions (
            id INTEGER PRIMARY KEY,
            person_name TEXT,
            reason TEXT
        )
    """)

    # INJECTING MOCK DATA ---
    
    # Notice the "smurfing" pattern: Three transactions just under $10k
    txs = [
        (1, 'Global Traders LLC', 'Oceanic Shell Ltd', 9500, '2026-09-01'),
        (2, 'Global Traders LLC', 'Oceanic Shell Ltd', 9200, '2026-09-03'),
        (3, 'Global Traders LLC', 'Oceanic Shell Ltd', 9800, '2026-09-05'),
        (4, 'Retail Store A', 'Supplier B', 1500, '2026-09-02') # Innocent transaction
    ]
    cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)", txs)

    corps = [
        (1, 'Oceanic Shell Ltd', 'Victor Dragov', 'Panama'),
        (2, 'Global Traders LLC', 'Alice Smith', 'USA')
    ]
    cursor.executemany("INSERT INTO corporate_registry VALUES (?, ?, ?, ?)", corps)

    sancs = [
        (1, 'Victor Dragov', 'International Arms Dealing and Sanctions Evasion')
    ]
    cursor.executemany("INSERT INTO sanctions VALUES (?, ?, ?)", sancs)

    conn.commit()
    conn.close()
    print("Database seeded successfully with money laundering scenario!")

if __name__ == "__main__":
    setup_database()