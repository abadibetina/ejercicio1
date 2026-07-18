import os

import psycopg
import redis
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


def get_redis_connection():
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "cache"),
        port=int(os.environ.get("REDIS_PORT", "6379")),
        socket_connect_timeout=5,
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


@app.route("/cache-check")
def cache_check():
    try:
        client = get_redis_connection()
        client.ping()
        return jsonify(cache="ok")
    except Exception as exc:
        return jsonify(cache="error", detail=str(exc)), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
