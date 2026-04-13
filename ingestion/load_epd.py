import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os
import time

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cursor = conn.cursor()

cursor.execute("""
    DROP TABLE IF EXISTS raw_prescriptions;
    CREATE TABLE raw_prescriptions (
        year_month                  TEXT,
        regional_office_name        TEXT,
        regional_office_code        TEXT,
        icb_name                    TEXT,
        icb_code                    TEXT,
        pco_name                    TEXT,
        pco_code                    TEXT,
        practice_name               TEXT,
        practice_code               TEXT,
        address_1                   TEXT,
        address_2                   TEXT,
        address_3                   TEXT,
        address_4                   TEXT,
        postcode                    TEXT,
        bnf_chemical_substance_code TEXT,
        bnf_chemical_substance      TEXT,
        bnf_presentation_code       TEXT,
        bnf_presentation_name       TEXT,
        bnf_chapter_plus_code       TEXT,
        quantity                    NUMERIC,
        items                       NUMERIC,
        total_quantity              NUMERIC,
        adq_usage                   NUMERIC,
        nic                         NUMERIC,
        actual_cost                 NUMERIC,
        unidentified                TEXT,
        snomed_code                 TEXT
    );
""")
conn.commit()
print("Table created successfully.")

files = [
    'data/raw/epd_snomed_202511.csv',
    'data/raw/epd_snomed_202512.csv',
    'data/raw/epd_snomed_202601.csv',
]

BATCH_SIZE = 100000

for filepath in files:
    print(f"\nLoading {filepath}...")
    start = time.time()
    total_rows = 0

    for chunk in pd.read_csv(
        filepath,
        chunksize=BATCH_SIZE,
        dtype=str,
        encoding='utf-8'
    ):
        chunk.columns = [c.strip().lower() for c in chunk.columns]
        chunk = chunk.where(pd.notnull(chunk), None)

        # Convert numeric columns
        for col in ['quantity','items','total_quantity','adq_usage','nic','actual_cost']:
            if col in chunk.columns:
                chunk[col] = pd.to_numeric(chunk[col], errors='coerce')

        rows = [tuple(row) for row in chunk.itertuples(index=False)]

        execute_values(cursor, """
            INSERT INTO raw_prescriptions VALUES %s
        """, rows)

        conn.commit()
        total_rows += len(rows)
        elapsed = time.time() - start
        print(f"  {total_rows:,} rows loaded in {elapsed:.0f}s", end='\r')

    print(f"  Done — {total_rows:,} rows from {filepath}")

cursor.execute("SELECT COUNT(*) FROM raw_prescriptions;")
total = cursor.fetchone()[0]
print(f"\nTotal rows in raw_prescriptions: {total:,}")

cursor.close()
conn.close()
print("Connection closed. Ingestion complete.")
