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
        "CREATE TABLE IF NOT EXISTS positions (account_id INTEGER, account_version INTEGER, product_id INTEGER, quantity NUMERIC, PRIMARY KEY (account_id, account_version, product_id))",
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
        connection.execute(text("INSERT OR IGNORE INTO customers VALUES (:id, :name, :country, :status, :date_of_birth)"), [
            {"id": 1, "name": "Smith Holdings", "country": "GB", "status": "active", "date_of_birth": "1980-01-01"},
            {"id": 2, "name": "Jones Family", "country": "US", "status": "active", "date_of_birth": "1975-05-10"},
            {"id": 3, "name": "Brown Ltd", "country": "FR", "status": "inactive", "date_of_birth": "1990-03-12"},
            *[
                {"id": customer_id, "name": f"Customer {customer_id:03d}", "country": ["GB", "US", "FR", "DE", "ES"][customer_id % 5], "status": "inactive" if customer_id % 7 == 0 else "active", "date_of_birth": f"{1970 + customer_id % 30:04d}-01-15"}
                for customer_id in range(4, 151)
            ],
        ])
        connection.execute(text("INSERT OR IGNORE INTO products VALUES (:id, :name, :category, :status)"), [
            {"id": 10, "name": "Product X", "category": "fund", "status": "active"},
            {"id": 11, "name": "Product Y", "category": "bond", "status": "active"},
            *[
                {"id": product_id, "name": f"Product {product_id}", "category": ["fund", "bond", "equity"][product_id % 3], "status": "active" if product_id % 8 else "inactive"}
                for product_id in range(12, 160)
            ],
        ])
        connection.execute(text("INSERT OR IGNORE INTO investments VALUES (:id, :customer_id, :product_id, :value)"), [
            {"id": 100, "customer_id": 1, "product_id": 10, "value": 150000},
            {"id": 101, "customer_id": 2, "product_id": 10, "value": 200000},
            {"id": 102, "customer_id": 2, "product_id": 11, "value": 50000},
            *[
                {"id": investment_id, "customer_id": 1 + (investment_id - 100) % 150, "product_id": 10 + (investment_id - 100) % 150, "value": 10000 + (investment_id - 100) * 1250}
                for investment_id in range(103, 250)
            ],
        ])
        connection.execute(text("INSERT OR IGNORE INTO accounts VALUES (:account_id, :version, :customer_id)"), [
            {"account_id": 20, "version": 1, "customer_id": 1},
            {"account_id": 20, "version": 2, "customer_id": 1},
            {"account_id": 21, "version": 1, "customer_id": 2},
            *[
                {"account_id": account_id, "version": 1, "customer_id": 1 + (account_id - 22) % 150}
                for account_id in range(22, 169)
            ],
        ])
        connection.execute(text("INSERT INTO positions (account_id, account_version, product_id, quantity) SELECT :account_id, :version, :product_id, :quantity WHERE NOT EXISTS (SELECT 1 FROM positions WHERE account_id = :account_id AND account_version = :version AND product_id = :product_id)"), [
            {"account_id": 20, "version": 1, "product_id": 10, "quantity": 12.5},
            {"account_id": 20, "version": 2, "product_id": 11, "quantity": 8},
            {"account_id": 21, "version": 1, "product_id": 10, "quantity": 4},
            *[
                {"account_id": account_id, "version": 1, "product_id": 10 + (account_id - 22) % 150, "quantity": 1 + (account_id - 22) % 20}
                for account_id in range(22, 169)
            ],
        ])

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
