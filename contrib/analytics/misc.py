from pathlib import Path

SQL_SCRIPTS_DIR = Path(__file__).resolve().parent / "sql"
UPDATE_DDL_SQL = SQL_SCRIPTS_DIR / "update.sql"
LOCAL_SERVER_ANALYTICS_DDL_SQL = SQL_SCRIPTS_DIR / "local_server_analytics.sql"
