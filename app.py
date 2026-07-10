"""
المدير المالي — خادم الموقع (Flask)، ثنائي اللغة (عربي/إنجليزي).
رفع أي ملف → استخراج → تحليل → تقرير PDF + ملخص في الصفحة.

التشغيل (تطوير):   python app.py
التشغيل (إنتاج):    python app.py --serve   (خادم waitress)
"""
import os
import re
import time
import uuid
import logging
import secrets

from flask import (Flask, request, render_template, send_file,
                   redirect, url_for, abort, Response, g)

import engine
import report
import i18n
from extractors import ExtractionError

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOADS = os.path.join(BASE, "uploads")
OUTPUTS = os.path.join(BASE, "outputs")
os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

ALLOWED = {".xlsx", ".xls", ".csv", ".pdf", ".docx", ".txt",
           ".png", ".jpg", ".jpeg", ".webp"}
MAX_BYTES = 25 * 1024 * 1024

# تواقيع الملفات الحقيقية (magic bytes) — نتحقق أن المحتوى يطابق الامتداد،
# فلا يمرّ ملف خبيث مُسمّى بامتداد بريء. (النصوص csv/txt بلا توقيع موثوق.)
_MAGIC = {
    ".pdf":  [b"%PDF-"],
    ".xlsx": [b"PK\x03\x04"], ".docx": [b"PK\x03\x04"],   # حاويات ZIP
    ".xls":  [b"\xD0\xCF\x11\xE0"],                         # OLE
    ".png":  [b"\x89PNG\r\n\x1a\n"],
    ".jpg":  [b"\xFF\xD8\xFF"], ".jpeg": [b"\xFF\xD8\xFF"],
    ".webp": [b"RIFF"],
}


def _verify_magic(head: bytes, ext: str) -> bool:
    """يتحقق أن أول بايتات الملف تطابق نوعه المُعلَن (يمنع التمويه بالامتداد)."""
    sigs = _MAGIC.get(ext)
    if not sigs:                       # csv/txt: لا توقيع ثنائي — نقبل كنص
        return True
    return any(head.startswith(s) for s in sigs)
UID_RE = re.compile(r"^[a-f0-9]{12}$")
SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:5000")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("almudir")

app = Flask(__name__)
app.config.update(
    MAX_CONTENT_LENGTH=MAX_BYTES,
    SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
    JSON_AS_ASCII=False,
)


# ---------- nonce لكل طلب (يسمح بـ JSON-LD دون فتح السكربتات) ----------
@app.before_request
def make_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)


@app.context_processor
def inject_nonce():
    return {"csp_nonce": getattr(g, "csp_nonce", "")}


# ---------- رؤوس أمان على كل استجابة ----------
@app.after_request
def secure_headers(resp):
    nonce = getattr(g, "csp_nonce", "")
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        f"script-src 'self' 'nonce-{nonce}'; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none'")
    return resp


RETENTION_SECS = int(os.environ.get("RETENTION_SECS", str(2 * 3600)))  # عمر التقارير المؤقتة


def _prune(folder, max_age=RETENTION_SECS):
    """يحذف الملفات الأقدم من max_age — يمنع امتلاء القرص وبقاء بيانات مالية."""
    now = time.time()
    try:
        for fn in os.listdir(folder):
            p = os.path.join(folder, fn)
            try:
                if os.path.isfile(p) and now - os.path.getmtime(p) > max_age:
                    os.remove(p)
            except OSError:
                pass
    except OSError:
        pass


def _lang():
    return i18n.norm_lang(request.values.get("lang", "ar"))


# ---------- الصفحات ----------
@app.route("/")
def index():
    t = i18n.ui(_lang())
    return render_template("index.html", t=t, site=SITE_URL)


@app.route("/analyze", methods=["POST"])
def analyze():
    lang = _lang()
    t = i18n.ui(lang)
    f = request.files.get("file")
    if not f or not f.filename:
        return render_template("index.html", t=t, site=SITE_URL, error=t["err_nofile"]), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in ALLOWED:
        return render_template("index.html", t=t, site=SITE_URL, error=t["err_badformat"]), 400

    # فحص التوقيع الفعلي: يمنع ملفاً خبيثاً مُموَّهاً بامتداد بريء
    head = f.stream.read(16); f.stream.seek(0)
    if not _verify_magic(head, ext):
        log.warning("magic mismatch for %s (ext %s)", f.filename, ext)
        return render_template("index.html", t=t, site=SITE_URL, error=t["err_badformat"]), 400

    _prune(OUTPUTS); _prune(UPLOADS)          # نظافة دورية عند كل طلب

    uid = uuid.uuid4().hex[:12]
    in_path = os.path.join(UPLOADS, uid + ext)
    f.save(in_path)

    company = request.form.get("company", "").strip()[:80] or t["brand"]
    cash_raw = request.form.get("cash", "").strip()
    try:
        cash = float(re.sub(r"[^\d.\-]", "", cash_raw)) if cash_raw else None
    except ValueError:
        cash = None

    try:
        a = engine.analyze(in_path, current_cash=cash)
        pdf_path = os.path.join(OUTPUTS, uid + ".pdf")
        report.generate(a, pdf_path, company=company, lang=lang)
    except ExtractionError as e:
        return render_template("index.html", t=t, site=SITE_URL, error=str(e)), 422
    except Exception:
        log.exception("analysis failed for %s", in_path)   # سجل داخلي فقط — لا تسريب للمستخدم
        return render_template("index.html", t=t, site=SITE_URL, error=t["err_generic"]), 500
    finally:
        try:
            os.remove(in_path)                              # لا نحتفظ بالملف المالي الخام
        except OSError:
            pass

    vm = _view_model(a, lang)
    return render_template("result.html", t=t, site=SITE_URL, a=a, vm=vm,
                           uid=uid, company=company)


def _view_model(a, lang):
    """نُصيّر نصوص التحليل مرة واحدة هنا (تبقى القوالب نظيفة)."""
    if a.ftype == "payroll":                      # وضع تحليل الرواتب (تخطيط مختلف)
        return {
            "ftype": "payroll",
            "payroll_summary": i18n.payroll_summary(a, lang),
            "employees": a.employees[:12],
            "risks": [{"title": i18n.finding_title(f, lang), "text": i18n.finding_text(f, lang)}
                      for f in a.findings],
            "recs": [i18n.rec_text(r, lang) for r in a.recommendations],
        }
    band_txt = {"good": "healthy", "medium": "caution", "high_risk": "risk"}[a.safety_band]
    vm = {
        "ftype": "statement",
        "decision_head": None, "decision_detail": None,
        "summary": i18n.summary_sentence(a, lang),
        "status_key": band_txt, "safety_label": i18n.safety_label(a.safety_band, lang),
        "risks": [i18n.finding_text(f, lang) for f in a.findings],
        "recs": [i18n.rec_text(r, lang) for r in a.recommendations],
        "savings_line": i18n.savings_sentence(a.total_savings, lang) if a.total_savings > 0 else None,
        "survival_line": (i18n.survival_sentence(a.survival_days, lang)
                          if a.survival_days is not None else None),
        "salary_line": i18n.salary_sentence(a, lang) if a.salary_total > 0 else None,
        "recurring_line": i18n.recurring_sentence(a, lang) if a.recurring else None,
        # وسادة التدفق: نعرضها كطمأنة حين تكون قوية/متوسطة، أو كتحذير حين يحترق النقد فعلاً.
        # لا نعرض "0% انتبه" لحساب متوازن (داخل≈خارج) — تضليل بالنبرة.
        "resilience_line": (i18n.resilience_sentence(a, lang)
                            if a.breakeven_drop_pct is not None and
                            (a.breakeven_drop_pct >= 0.10 or (a.runway and a.runway.get("burning")))
                            else None),
        "buffer_line": i18n.buffer_sentence(a, lang) if a.buffer_months is not None else None,
        "runway_line": (i18n.runway_sentence(a.runway, lang)
                        if a.runway and a.runway.get("burning") else None),
    }
    if a.decision:
        vm["decision_head"] = i18n.decision_headline(a.decision["sar"], a.decision["timeframe"], lang,
                                                     a.decision.get("kind", "save"))
        vm["decision_detail"] = i18n.finding_text(a.decision["finding"], lang)
    return vm


@app.route("/download/<uid>")
def download(uid):
    if not UID_RE.match(uid or ""):
        abort(404)
    path = os.path.join(OUTPUTS, uid + ".pdf")
    if not os.path.exists(path):
        abort(404)
    return send_file(path, as_attachment=True, download_name="financial-report.pdf",
                     mimetype="application/pdf")


# ---------- SEO / صحة ----------
@app.route("/robots.txt")
def robots():
    body = f"User-agent: *\nAllow: /\nDisallow: /analyze\nDisallow: /download/\nSitemap: {SITE_URL}/sitemap.xml\n"
    return Response(body, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    urls = [f"{SITE_URL}/", f"{SITE_URL}/?lang=en"]
    items = "".join(f"<url><loc>{u}</loc><changefreq>weekly</changefreq></url>" for u in urls)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{items}</urlset>'
    return Response(xml, mimetype="application/xml")


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


# ---------- معالجات الأخطاء (بلا تسريب) ----------
@app.errorhandler(413)
def too_big(e):
    t = i18n.ui(_lang())
    return render_template("index.html", t=t, site=SITE_URL, error=t["err_toobig"]), 413


@app.errorhandler(404)
def not_found(e):
    return redirect(url_for("index"))


@app.errorhandler(500)
def server_error(e):
    t = i18n.ui(_lang())
    return render_template("index.html", t=t, site=SITE_URL, error=t["err_generic"]), 500


if __name__ == "__main__":
    import sys
    port = int(os.environ.get("PORT", "5000"))
    if "--serve" in sys.argv:
        from waitress import serve
        # خيطان فقط: الخطة المجانية 512MB؛ تحليلان متزامنان يضاعفان الذاكرة ويسبّبان OOM/502.
        threads = int(os.environ.get("THREADS", "2"))
        log.info("waitress on http://0.0.0.0:%d (threads=%d)", port, threads)
        serve(app, host="0.0.0.0", port=port, threads=threads)
    else:
        debug = os.environ.get("FLASK_DEBUG", "0") == "1"
        app.run(host="127.0.0.1", port=port, debug=debug)
