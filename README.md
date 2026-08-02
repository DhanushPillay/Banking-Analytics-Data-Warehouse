# Banking Analytics Platform – Data Warehouse & Fraud Detection
## Part 1: Banking Data Warehouse (Jury 1)

## Tools you need
- **VS Code** + extensions: `Python` (Microsoft), `Docker` (Microsoft), and either
  `PostgreSQL` (by Chris Kolkman) or `SQLTools` + `SQLTools PostgreSQL Driver` — lets you
  browse tables and run queries without leaving VS Code.
- **Docker Desktop** — runs Postgres in a container, no manual DB install/config.
- **Python 3.10+**
- **Power BI Desktop** (Windows) — for the final dashboard. If you're on Mac/Linux, use
  **Apache Superset** (Docker-based, cross-platform) instead — ask if you want that swap.
- **Git** — for version control (also doubles as your project history for the report).
- Optional: [dbdiagram.io](https://dbdiagram.io) (free, browser) to render a clean ER
  diagram from `sql/schema.sql` for your report.

## Project structure
```
banking-dw/
├── docker-compose.yml     # spins up Postgres
├── requirements.txt       # python deps
├── .env                   # local DB credentials (already filled in for you)
├── sql/
│   ├── schema.sql         # star/galaxy schema DDL
│   └── olap_queries.sql   # 12 OLAP queries (roll-up, drill-down, slice, dice, cube)
└── scripts/
    ├── generate_data.py   # generates + loads representative synthetic banking data
    └── load_real_data.py  # loads the real PKDD'99 dataset into the schema
```

## Step-by-step

### 1. Open the project in VS Code
```bash
code banking-dw
```

### 2. Start Postgres
```bash
docker compose up -d
```
Check it's running: `docker ps` should show `banking_dw_postgres`.

### 3. Create the schema
With the Postgres/SQLTools extension, connect using the credentials in `.env`
(host `localhost`, port `5432`, db `banking_dw`, user `dw_user`, password `dw_pass`),
then run `sql/schema.sql` against it. Or from the terminal:
```bash
docker exec -i banking_dw_postgres psql -U dw_user -d banking_dw < sql/schema.sql
```

### 4. Set up Python and generate the data
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Option A: Generate Synthetic Data
python scripts/generate_data.py

# Option B: Use Real Historical Data (PKDD'99)
# 1. Download from Kaggle: https://www.kaggle.com/datasets/arjunbhasin2013/pkdd-99-financial-data-set
# 2. Extract into a `data/` folder in this project (e.g., data/client.csv, data/trans.csv)
# 3. Run: python scripts/load_real_data.py
```
This generates and loads: 15 branches, 800 customers, ~1,030 accounts, 300 loans,
8,000 transactions across a 12-month period (2025) — enough volume for the roll-up/
drill-down queries to actually show meaningful trends.

### 5. Run the OLAP queries
Open `sql/olap_queries.sql` in VS Code with the DB extension connected, run each
query, screenshot the results — these screenshots go straight into your report as
evidence for the "OLAP Queries (min. 10)" deliverable.

### 6. Build the Power BI dashboard
- Open Power BI Desktop → **Get Data** → **PostgreSQL database**
- Server: `localhost:5432`, Database: `banking_dw`
- Import: `fact_transactions`, `fact_loans`, and all `dim_*` tables
- Power BI should auto-detect the relationships from your foreign keys; if not,
  set them manually in **Model view** (this is worth mentioning in your report —
  it demonstrates you understand the schema's relationships)
- Suggested report pages: Deposits Trend (line chart, roll-up by month), Branch
  Performance (map/bar by region → city → branch), Loan Portfolio (by type/status),
  Customer Segments (segment × age group)

### 7. Documentation
- Export `sql/schema.sql` into an ER diagram via dbdiagram.io for the report
- Architecture diagram: raw generation → Postgres staging → star/galaxy schema → Power BI
- Include the 12 OLAP query results as your evidence

## Deliverable checklist (from the jury PDF)
| Deliverable | Where it comes from |
|---|---|
| Problem definition | Write-up: banking analytics for deposits/loans/branch performance |
| Requirement analysis | The 4-5 business questions the dashboard answers |
| Source database design | `generate_data.py` logic + raw table shapes |
| ETL process | `generate_data.py` (generate → transform → load into schema) |
| DW architecture | Architecture diagram (see above) |
| Star/Snowflake schema | `sql/schema.sql` + ER diagram |
| Fact & dimension tables | Table listing grain/keys/measures (2 fact, 5 dim tables) |
| Data cube design | Query 5 in `olap_queries.sql` (CUBE) |
| OLAP queries (min. 10) | `sql/olap_queries.sql` — 12 provided |
| Dashboard | Power BI report (step 6) |
| Project report | Compile all sections above |
| Demonstration | Live: docker up → generate data → run queries → dashboard drill-down |

## Notes
- `random.seed(42)` is set in `generate_data.py` so your data is reproducible —
  useful if you need to regenerate after schema tweaks and want consistent numbers
  across report drafts.
- To wipe and start over: `docker compose down -v` (deletes the volume), then
  repeat from step 2.
