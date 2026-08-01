import os
import json
import sqlite3
import smtplib
import threading
import time
import urllib.request
from email.mime.text import MIMEText

from flask import Flask, render_template, request

app = Flask(__name__)
DATABASE = "alerts.db"
GRANTS_API = "https://api.grants.gov/v1/api/search2"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        keyword TEXT NOT NULL,
        agencies TEXT,
        opp_statuses TEXT DEFAULT 'posted',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_checked TEXT
    );
    CREATE TABLE IF NOT EXISTS alert_hits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_id INTEGER NOT NULL,
        opp_number TEXT,
        title TEXT,
        agency TEXT,
        open_date TEXT,
        close_date TEXT,
        notified_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(alert_id, opp_number)
    );
    """)
    conn.commit()
    conn.close()


def search_grants(keyword, rows=20, opp_statuses="posted", agencies=""):
    payload = {
        "keyword": keyword,
        "rows": rows,
        "oppStatuses": opp_statuses,
    }
    if agencies:
        payload["agencies"] = agencies
    req = urllib.request.Request(
        GRANTS_API,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("data", {}).get("oppHits", [])
    except Exception as e:
        app.logger.error(f"Grants.gov API error: {e}")
        return []


def send_email(to_address, subject, body):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("SMTP_FROM", smtp_user)

    if not (smtp_host and smtp_user and smtp_pass and from_addr):
        print(f"[EMAIL NOT SENT - SMTP not configured]\nTo: {to_address}\nSubject: {subject}\n{body}")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_address

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_addr, [to_address], msg.as_string())
        return True
    except Exception as e:
        app.logger.error(f"Email error: {e}")
        return False


def check_alerts():
    conn = get_db()
    alerts = conn.execute("SELECT * FROM alerts").fetchall()

    for alert in alerts:
        hits = search_grants(
            alert["keyword"],
            rows=100,
            opp_statuses=alert["opp_statuses"] or "posted",
            agencies=alert["agencies"] or "",
        )
        new_hits = []

        for h in hits:
            already = conn.execute(
                "SELECT 1 FROM alert_hits WHERE alert_id=? AND opp_number=?",
                (alert["id"], h.get("number")),
            ).fetchone()
            if not already:
                conn.execute(
                    "INSERT INTO alert_hits (alert_id, opp_number, title, agency, open_date, close_date) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        alert["id"],
                        h.get("number"),
                        h.get("title"),
                        h.get("agencyName"),
                        h.get("openDate"),
                        h.get("closeDate"),
                    ),
                )
                new_hits.append(h)

        if new_hits:
            lines = [f"{h.get('number')}: {h.get('title')} ({h.get('agencyName') or 'N/A'})" for h in new_hits]
            body = "New grant opportunities matching your alert:\n\n" + "\n".join(lines)
            send_email(alert["email"], f'New grants matching "{alert["keyword"]}"', body)

        conn.execute("UPDATE alerts SET last_checked=CURRENT_TIMESTAMP WHERE id=?", (alert["id"],))

    conn.commit()
    conn.close()


def alert_worker():
    interval = int(os.environ.get("ALERT_INTERVAL_SECONDS", "3600"))
    while True:
        try:
            check_alerts()
        except Exception as e:
            app.logger.error(f"Alert worker error: {e}")
        time.sleep(interval)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    keyword = request.form.get("keyword", "").strip()
    rows = int(request.form.get("rows", "20"))
    status = request.form.get("status", "posted")
    hits = search_grants(keyword, rows=rows, opp_statuses=status)
    return render_template("index.html", keyword=keyword, results=hits)


@app.route("/alerts", methods=["POST"])
def create_alert():
    email = request.form.get("email", "").strip()
    keyword = request.form.get("keyword", "").strip()
    if not email or not keyword:
        return "Email and keyword are required.", 400

    conn = get_db()
    conn.execute(
        "INSERT INTO alerts (email, keyword, agencies, opp_statuses) VALUES (?, ?, ?, ?)",
        (email, keyword, request.form.get("agencies", ""), request.form.get("status", "posted")),
    )
    conn.commit()
    conn.close()
    return "Alert saved. We'll email you when new grants match your keyword.", 200


@app.route("/send-alerts", methods=["POST"])
def trigger_alerts():
    check_alerts()
    return "Alerts checked.", 200


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=alert_worker, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
