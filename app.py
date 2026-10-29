import csv
import io
import json
import os
from datetime import datetime, timezone
from functools import wraps

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, Response, redirect, render_template, request, session, url_for, flash

from analyzer import analyze_records, parse_upload, sample_records, report_html

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "dev-only-change-me"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=15 * 1024 * 1024,
)

oauth = OAuth(app)
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
if client_id and client_secret:
    oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

def current_result():
    return session.get("analysis_result")

@app.get("/")
def index():
    result = current_result()
    return render_template(
        "index.html",
        user=session.get("user"),
        oauth_ready=bool(client_id and client_secret),
        result=result,
        demo_available=True,
    )

@app.get("/auth/login")
def login():
    if not (client_id and client_secret):
        flash("Google OAuth ayarlanmamış. .env dosyasına istemci bilgilerini ekle.", "error")
        return redirect(url_for("index"))
    redirect_uri = url_for("callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.get("/auth/callback")
def callback():
    if not (client_id and client_secret):
        return redirect(url_for("index"))
    token = oauth.google.authorize_access_token()
    # Kimlik bilgisi alınır; token oturumda tutulmaz ve API erişimi için kullanılmaz.
    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo = oauth.google.userinfo()
    session["user"] = {
        "email": userinfo.get("email", ""),
        "name": userinfo.get("name", ""),
    }
    flash("Google hesabıyla oturum açıldı. Bu işlem etkinlik geçmişine otomatik erişim vermez.", "success")
    return redirect(url_for("index"))

@app.post("/auth/logout")
def logout():
    session.pop("user", None)
    flash("Oturum kapatıldı.", "success")
    return redirect(url_for("index"))

@app.post("/analyze/demo")
def analyze_demo():
    records = sample_records()
    result = analyze_records(records, source="Örnek veri")
    session["analysis_result"] = result
    return render_template("index.html", user=session.get("user"),
        oauth_ready=bool(client_id and client_secret), result=result, demo_available=True)

@app.post("/analyze/upload")
def analyze_upload():
    uploaded = request.files.get("datafile")
    if not uploaded or not uploaded.filename:
        flash("Lütfen analiz edilecek JSON veya CSV dosyasını seç.", "error")
        return redirect(url_for("index"))
    if not uploaded.filename.lower().endswith((".json", ".csv")):
        flash("Yalnızca JSON veya CSV dosyaları destekleniyor.", "error")
        return redirect(url_for("index"))
    try:
        raw = uploaded.read()
        records = parse_upload(raw, uploaded.filename)
        result = analyze_records(records, source="Yüklenen dosya")
        session["analysis_result"] = result
        flash(f"{len(records)} kayıt işlendi. Dosya kalıcı olarak saklanmadı.", "success")
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        flash(f"Dosya okunamadı: {exc}", "error")
        return redirect(url_for("index"))
    return render_template("index.html", user=session.get("user"),
        oauth_ready=bool(client_id and client_secret), result=result, demo_available=True)

@app.get("/report.html")
def download_html():
    result = current_result()
    if not result:
        flash("Önce analiz başlat.", "error")
        return redirect(url_for("index"))
    body = report_html(result)
    return Response(body, mimetype="text/html; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="google-etkinlik-raporu.html"'})

@app.get("/report.csv")
def download_csv():
    result = current_result()
    if not result:
        flash("Önce analiz başlat.", "error")
        return redirect(url_for("index"))
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=["timestamp", "date", "category", "title", "details"])
    writer.writeheader()
    writer.writerows(result["records"])
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="google-etkinlik-kayitlari.csv"'})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
