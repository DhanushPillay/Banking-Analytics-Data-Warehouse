from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "banking_dw.duckdb"


@pytest.fixture(scope="module")
def con():
    if not DB.exists():
        pytest.skip("Local DuckDB not built yet")
    connection = duckdb.connect(str(DB), read_only=True)
    yield connection
    connection.close()


def test_mart_counts(con):
    assert con.execute("SELECT count(*) FROM mart.fact_loans").fetchone()[0] == 682
    assert con.execute("SELECT count(*) FROM mart.fact_transactions").fetchone()[0] == 1_056_320
    assert con.execute("SELECT count(*) FROM mart.dim_customer").fetchone()[0] == 5369


def test_loan_target(con):
    defaults = con.execute(
        "SELECT count(*) FROM mart.fact_loans WHERE status_code IN ('B', 'D')"
    ).fetchone()[0]
    assert defaults == 76


def test_feature_mart(con):
    rows, defaults = con.execute(
        "SELECT count(*), sum(target) FROM analytics.loan_features"
    ).fetchone()
    assert rows == 682
    assert defaults == 76


def test_feature_counts_use_only_pre_loan_transactions(con):
    mismatches = con.execute(
        """
        SELECT count(*)
        FROM analytics.loan_features f
        WHERE f.n_txn <> (
            SELECT count(*)
            FROM mart.fact_transactions t
            WHERE t.account_id = f.account_id
              AND t.date_id < f.loan_date_id
        )
        """
    ).fetchone()[0]
    assert mismatches == 0


def test_gender_bin(con):
    rows = con.execute(
        """
        SELECT gender, gender_bin, count(*)
        FROM analytics.loan_features
        GROUP BY 1, 2
        ORDER BY 1
        """
    ).fetchall()
    assert rows == [("Female", 1, 348), ("Male", 0, 334)]


def test_analytics_outputs(con):
    assert con.execute("SELECT count(*) FROM analytics.model_scores").fetchone()[0] == 682
    assert con.execute("SELECT count(*) FROM analytics.loan_segments").fetchone()[0] == 682
    assert con.execute("SELECT count(*) FROM analytics.cv_comparison").fetchone()[0] == 24


def test_advanced_outputs(con):
    assert con.execute("SELECT count(*) FROM analytics.advanced_metrics").fetchone()[0] == 2
    assert con.execute("SELECT count(*) FROM analytics.advanced_scores").fetchone()[0] == 682
    assert con.execute("SELECT count(*) FROM analytics.cba_rules").fetchone()[0] >= 1
    labels = con.execute(
        "SELECT count(*), count(kmedoids), count(agnes), count(dbscan) "
        "FROM analytics.cluster_labels"
    ).fetchone()
    assert labels == (682, 682, 682, 682)
