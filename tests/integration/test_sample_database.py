from sqlalchemy import create_engine, text
from app.database.sample_db import initialize_sample_database


def test_sample_database_contains_150_rows_per_table(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'sample.db'}")
    initialize_sample_database(engine, reset=True)
    with engine.connect() as connection:
        counts = {
            table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
            for table in ("customers", "products", "investments", "accounts", "positions")
        }
    assert counts == {
        "customers": 150,
        "products": 150,
        "investments": 150,
        "accounts": 150,
        "positions": 150,
    }
