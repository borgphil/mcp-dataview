import argparse
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine
from app.database.engine import create_database_engine

def initialize_sample_database(engine: Engine, reset: bool = False) -> None:
    statements = [
        "CREATE TABLE IF NOT EXISTS customers (customer_id INTEGER PRIMARY KEY, customer_name TEXT, country_code TEXT, customer_status TEXT, date_of_birth TEXT)",
        "CREATE TABLE IF NOT EXISTS products (product_id INTEGER PRIMARY KEY, product_name TEXT, product_category TEXT, product_status TEXT)",
        "CREATE TABLE IF NOT EXISTS investments (investment_id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER, investment_value NUMERIC)",
        "CREATE TABLE IF NOT EXISTS accounts (account_id INTEGER, account_version INTEGER, customer_id INTEGER, PRIMARY KEY (account_id, account_version))",
        "CREATE TABLE IF NOT EXISTS positions (account_id INTEGER, account_version INTEGER, product_id INTEGER, quantity NUMERIC)",
        "CREATE VIEW IF NOT EXISTS vw_customers AS SELECT * FROM customers",
        "CREATE VIEW IF NOT EXISTS vw_products AS SELECT * FROM products",
        "CREATE VIEW IF NOT EXISTS vw_investments AS SELECT * FROM investments",
        "CREATE VIEW IF NOT EXISTS vw_accounts AS SELECT * FROM accounts",
        "CREATE VIEW IF NOT EXISTS vw_positions AS SELECT * FROM positions",
    ]
    with engine.begin() as connection:
        if reset:
            connection.execute(text("DROP VIEW IF EXISTS vw_positions"))
            connection.execute(text("DROP VIEW IF EXISTS vw_accounts"))
            connection.execute(text("DROP VIEW IF EXISTS vw_investments"))
            connection.execute(text("DROP VIEW IF EXISTS vw_products"))
            connection.execute(text("DROP VIEW IF EXISTS vw_customers"))
            connection.execute(text("DROP TABLE IF EXISTS positions"))
            connection.execute(text("DROP TABLE IF EXISTS accounts"))
            connection.execute(text("DROP TABLE IF EXISTS investments"))
            connection.execute(text("DROP TABLE IF EXISTS products"))
            connection.execute(text("DROP TABLE IF EXISTS customers"))
        for statement in statements:
            connection.execute(text(statement))
        if connection.execute(text("SELECT COUNT(*) FROM customers")).scalar_one() == 0:
            connection.execute(text("INSERT INTO customers VALUES (1, 'Smith Holdings', 'GB', 'active', '1980-01-01'), (2, 'Jones Family', 'US', 'active', '1975-05-10'), (3, 'Brown Ltd', 'FR', 'inactive', '1990-03-12')"))
            connection.execute(text("INSERT INTO products VALUES (10, 'Product X', 'fund', 'active'), (11, 'Product Y', 'bond', 'active')"))
            connection.execute(text("INSERT INTO investments VALUES (100, 1, 10, 150000), (101, 2, 10, 200000), (102, 2, 11, 50000)"))
            connection.execute(text("INSERT INTO accounts VALUES (20, 1, 1), (20, 2, 1), (21, 1, 2)"))
            connection.execute(text("INSERT INTO positions VALUES (20, 1, 10, 12.5), (20, 2, 11, 8), (21, 1, 10, 4)"))

def main() -> None:
    parser = argparse.ArgumentParser(description="Create the local restricted-SQL SQLite database.")
    parser.add_argument("--database", type=Path, default=Path("data/sample.db"))
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all sample tables and views.")
    args = parser.parse_args()
    engine = create_database_engine(args.database)
    initialize_sample_database(engine, reset=args.reset)
    engine.dispose()
    print(f"Initialized sample database at {args.database}")

if __name__ == "__main__":
    main()
