import os
import re
import json
import sqlite3
import smtplib
import threading
import time
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText

from flask import Flask, render_template, request

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
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


def _pipe_sep(value):
    if not value:
        return value
    parts = [p.strip() for p in re.split(r"[,\|]", value) if p.strip()]
    return "|".join(parts)


def search_grants(
    keyword="",
    rows=20,
    opp_statuses="posted",
    agencies="",
    funding_categories="",
    funding_instruments="",
    eligibilities="",
):
    payload = {"keyword": keyword, "rows": rows}
    if opp_statuses:
        payload["oppStatuses"] = opp_statuses
    if _pipe_sep(agencies):
        payload["agencies"] = _pipe_sep(agencies)
    if _pipe_sep(funding_categories):
        payload["fundingCategories"] = _pipe_sep(funding_categories)
    if _pipe_sep(funding_instruments):
        payload["fundingInstruments"] = _pipe_sep(funding_instruments)
    if _pipe_sep(eligibilities):
        payload["eligibilities"] = _pipe_sep(eligibilities)
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


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "to", "for", "of", "with", "from", "by", "in", "on", "at", "as",
    "this", "that", "these", "those", "we", "our", "us", "i", "you",
    "it", "its", "they", "them", "their", "will", "would", "could",
    "can", "should", "may", "might", "project", "program", "grant",
    "funding", "research", "study", "studies", "work", "aim", "propose",
}


def _tokens(text):
    if not text:
        return []
    tokens = re.findall(r"\b[a-z]+\b", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOP_WORDS]


def _parse_date(value):
    if not value:
        return None
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y %I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _add_url(hit):
    hit["url"] = f"https://www.grants.gov/view-opportunity.html?oppId={hit.get('id')}"
    return hit


def date_filter(hit, open_after=None, close_before=None):
    ok = True
    if open_after:
        open_dt = _parse_date(hit.get("openDate"))
        target = datetime.fromisoformat(open_after).date()
        if open_dt is None or open_dt < target:
            ok = False
    if close_before and ok:
        close_dt = _parse_date(hit.get("closeDate"))
        target = datetime.fromisoformat(close_before).date()
        if close_dt is None or close_dt > target:
            ok = False
    return ok


def score_results(hits, text):
    tokens = _tokens(text)
    if not tokens:
        return hits

    total = len(tokens)
    for h in hits:
        _add_url(h)
        hay = " ".join(
            str(h.get(k, "")) for k in ("title", "agencyName", "number")
        ).lower()
        matched = {t for t in tokens if t in hay}
        h["score"] = len(matched)
        h["match_pct"] = round(100 * len(matched) / total)
        h["matched"] = sorted(matched)
    return sorted(hits, key=lambda x: x.get("score", 0), reverse=True)


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
    description = request.form.get("description", "").strip()
    rows = int(request.form.get("rows", "20"))
    opp_statuses = request.form.get("status", "posted")
    agencies = request.form.get("agencies", "").strip()
    funding_categories = request.form.get("funding_categories", "").strip()
    funding_instruments = request.form.get("funding_instruments", "").strip()
    eligibilities = request.form.get("eligibilities", "").strip()
    open_after = request.form.get("open_after", "")
    close_before = request.form.get("close_before", "")

    query = keyword or description
    hits = search_grants(
        query,
        rows=rows,
        opp_statuses=opp_statuses,
        agencies=agencies,
        funding_categories=funding_categories,
        funding_instruments=funding_instruments,
        eligibilities=eligibilities,
    )

    if open_after or close_before:
        hits = [h for h in hits if date_filter(h, open_after, close_before)]

    for h in hits:
        _add_url(h)

    if description:
        hits = score_results(hits, description)

    return render_template(
        "index.html",
        keyword=keyword,
        description=description,
        rows=rows,
        status=opp_statuses,
        agencies=agencies,
        funding_categories=funding_categories,
        funding_instruments=funding_instruments,
        eligibilities=eligibilities,
        open_after=open_after,
        close_before=close_before,
        results=hits,
    )


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
