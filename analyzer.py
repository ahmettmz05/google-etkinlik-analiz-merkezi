import csv
import html
import io
import json
from collections import Counter
from datetime import datetime, timezone

def _first(item, keys, default=""):
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default

def _iso(value):
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        # Treat large values as milliseconds, smaller values as seconds.
        stamp = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat()
        except (ValueError, OSError, OverflowError):
            return str(value)
    text = str(value).strip()
    if text.isdigit():
        try:
            return _iso(int(text))
        except Exception:
            pass
    return text

def normalize_record(item, index=0):
    if not isinstance(item, dict):
        item = {"title": str(item)}
    timestamp = _iso(_first(item, [
        "time", "timestamp", "time_usec", "creationTime", "eventTime",
        "date", "datetime", "lastModifiedTime"
    ]))
    title = _first(item, [
        "title", "header", "name", "activity", "query", "searchQuery",
        "description", "product"
    ], "Başlıksız etkinlik")
    category = _first(item, [
        "category", "type", "activityType", "eventType", "header"
    ], "Belirtilmemiş")
    details = _first(item, [
        "details", "url", "link", "titleUrl", "device", "source"
    ], "")
    if isinstance(details, (dict, list)):
        details = json.dumps(details, ensure_ascii=False)
    return {
        "timestamp": str(timestamp),
        "date": str(timestamp)[:10] if timestamp else "Tarih yok",
        "category": str(category)[:300],
        "title": str(title)[:1000],
        "details": str(details)[:2000],
    }

def parse_upload(raw, filename):
    text = raw.decode("utf-8-sig")
    if filename.lower().endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            raise ValueError("CSV dosyasında kayıt bulunamadı.")
        return [normalize_record(row, i) for i, row in enumerate(rows)]
    data = json.loads(text)
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        # Common export shapes; if none match, treat object as one record.
        rows = next((data[k] for k in ("activities", "items", "events", "records", "timelineObjects")
                     if isinstance(data.get(k), list)), [data])
    else:
        raise ValueError("JSON kök yapısı bir nesne veya liste olmalı.")
    return [normalize_record(row, i) for i, row in enumerate(rows)]

def sample_records():
    return [
        {"time": "2026-10-28T09:12:00+03:00", "title": "Örnek arama: hava durumu",
         "category": "Arama", "details": "ÖRNEK VERİ — gerçek hesap verisi değildir"},
        {"time": "2026-10-28T09:19:00+03:00", "title": "Örnek video izleme",
         "category": "YouTube", "details": "ÖRNEK VERİ — gerçek hesap verisi değildir"},
        {"time": "2026-10-27T20:05:00+03:00", "title": "Örnek web etkinliği",
         "category": "Web ve Uygulama Etkinliği", "details": "ÖRNEK VERİ — gerçek hesap verisi değildir"},
        {"time": "2026-10-27T20:30:00+03:00", "title": "Örnek harita araması",
         "category": "Haritalar", "details": "ÖRNEK VERİ — gerçek hesap verisi değildir"},
    ]

def analyze_records(records, source="Yüklenen dosya"):
    normalized = [normalize_record(r, i) for i, r in enumerate(records)]
    categories = Counter(r["category"] for r in normalized)
    dates = Counter(r["date"] for r in normalized)
    return {
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": len(normalized),
        "category_counts": categories.most_common(),
        "date_counts": sorted(dates.items()),
        "records": normalized,
        "limitations": [
            "Sonuçlar yalnızca bu oturumda analiz edilen örnek veya kullanıcı tarafından seçilmiş dosyayı kapsar.",
            "Google OAuth oturumu tüm Google etkinlik geçmişine erişim sağlamaz.",
            "Tarih ve kategori alanları dışa aktarma biçimine göre eksik veya farklı olabilir."
        ],
    }

def report_html(result):
    rows = []
    for r in result["records"]:
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(r[k]))}</td>"
                    for k in ("timestamp", "category", "title", "details")) + "</tr>")
    cats = "".join(f"<li>{html.escape(str(k))}: {v}</li>" for k, v in result["category_counts"])
    dates = "".join(f"<li>{html.escape(str(k))}: {v}</li>" for k, v in result["date_counts"])
    limitations = "".join(f"<li>{html.escape(x)}</li>" for x in result["limitations"])
    return f"""<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Google Etkinlik Analiz Raporu</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#202124}}
table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{border:1px solid #ddd;padding:.5rem;text-align:left;overflow-wrap:anywhere}}
th{{background:#f1f3f4}}.note{{background:#fff4ce;padding:1rem;border-radius:8px}}</style>
<h1>Google Etkinlik Analiz Raporu</h1><p>Kaynak: {html.escape(result["source"])} · Oluşturulma: {html.escape(result["generated_at"])}</p>
<div class="note"><strong>Veri kapsamı:</strong> Bu rapor yalnızca bu oturumda analiz edilen verileri içerir; Google hesabındaki tüm geçmişi temsil ettiği garanti edilmez.</div>
<h2>Özet</h2><p>Toplam kayıt: <strong>{result["total"]}</strong></p>
<h3>Kategori dağılımı</h3><ul>{cats}</ul><h3>Tarihe göre kayıtlar</h3><ul>{dates}</ul>
<h2>Kayıtlar</h2><table><thead><tr><th>Zaman</th><th>Kategori</th><th>Başlık</th><th>Ayrıntı</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Sınırlamalar</h2><ul>{limitations}</ul></html>"""
