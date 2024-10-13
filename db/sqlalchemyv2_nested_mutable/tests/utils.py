# ruff: noqa
# type: ignore
import time

import psycopg2
import requests


def wait_pg_ready(dbinfo: dict, check_interval_base=0.1, back_rate=1.1, max_check_times=50):
    check_interval = check_interval_base
    for i in range(max_check_times):
        try:
            with (
                psycopg2.connect(
                    host=dbinfo["host"],
                    port=dbinfo["port"],
                    dbname=dbinfo["database"],
                    user=dbinfo["user"],
                    password=dbinfo["password"],
                ) as conn,
                conn.cursor() as cur,
            ):
                cur.execute("SELECT 1;")
                if cur.fetchone()[0] == 1:
                    break
        except psycopg2.OperationalError:
            time.sleep(check_interval)
            check_interval *= back_rate
            print("." * i)  # noqa: T201
            continue


def docker_status_code(container):
    port = container.port_map["80/tcp"]
    status = 200
    response = requests.get(f"http://127.0.0.1:{port}/status/{status}")
    assert response.status_code == status
