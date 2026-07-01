import os

import psycopg
from flask import Flask, jsonify

app = Flask(__name__)


def get_db_connection():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ.get("DB_NAME", "devops"),
        user=os.environ.get("DB_USER", "devops"),
        password=os.environ.get("DB_PASSWORD", "devops"),
        connect_timeout=5,
    )


@app.route("/")
def hello():
    return jsonify(message="Hello DevOps")


@app.route("/health")
def health():
    return jsonify(status="ok")


@app.route("/db-check")
def db_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify(database="ok")
    except Exception as exc:
        return jsonify(database="error", detail=str(exc)), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
