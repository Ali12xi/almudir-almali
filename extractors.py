"""
طبقة الاستخراج الموحّدة — تحوّل أي ملف مدخل إلى جدول عمليات موحّد.
تدعم الآن: Excel/CSV, PDF (جداول), Word (.docx), نص (.txt).
الصور والملفات الممسوحة الفوضوية: تُوجَّه لطبقة الذكاء الاصطناعي (extract_with_ai)
  التي تُفعّل بمفتاح Claude API — نقطة تمديد واحدة، بدون تغيير باقي النظام.

الأعمدة الموحّدة: التاريخ، البيان، النوع، التصنيف، الطرف، المبلغ
"""
from __future__ import annotations
import os
import re
import logging
import pandas as pd

_log = logging.getLogger("almudir.extract")


def _load_dotenv():
    """يحمّل مفتاح .env تلقائياً — بلا مكتبات خارجية، ويتحمّل BOM وعلامات الاقتباس.
    لا يطغى على متغيرات البيئة الحقيقية إن وُجدت."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except OSError:
        pass


_load_dotenv()

STD_COLS = ["التاريخ", "البيان", "النوع", "التصنيف", "الطرف", "المبلغ"]

# مرادفات الأعمدة (عربي + إنجليزي) — لمطابقة رؤوس الجداول المتنوعة
SYN = {
    "التاريخ": ["التاريخ", "تاريخ", "date", "day", "trans date", "transaction date", "posting date"],
    "البيان": ["البيان", "بيان", "الوصف", "وصف", "تفاصيل", "description", "details", "narration", "memo", "notes"],
    "النوع": ["النوع", "نوع", "type", "dr/cr", "debit/credit"],
    "التصنيف": ["التصنيف", "تصنيف", "البند", "الفئة", "category", "class", "account"],
    "الطرف": ["الطرف", "الجهة", "العميل", "المورد", "الاسم", "party", "customer", "vendor", "name", "payee", "beneficiary"],
    "المبلغ": ["المبلغ", "مبلغ", "القيمة", "قيمة", "amount", "value", "total"],
    # أعمدة مساعدة لاشتقاق النوع/المبلغ
    "_مدين": ["مدين", "debit", "withdrawal", "سحب", "منصرف"],
    "_دائن": ["دائن", "credit", "deposit", "إيداع", "وارد"],
}

INCOME_HINT = re.compile(r"دخل|إيراد|مبيع|إيداع|وارد|دائن|credit|deposit|income|sale", re.I)


class ExtractionError(Exception):
    pass


# ---------- المُرسِل حسب نوع الملف ----------
def _has_ai():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# حد صفحات الـPDF قابل للضبط بالبيئة: افتراضياً 60 (آمن لذاكرة الخطة المجانية 512MB).
# الأكبر يُوجَّه لتصدير Excel (خفيف على الذاكرة، فوري). ارفعه على استضافة أكبر عبر PDF_MAX_PAGES.
_PDF_MAX_PAGES = int(os.environ.get("PDF_MAX_PAGES", "60"))
_PDF_DETERMINISTIC_MAX = 5  # PDF أكبر من هذا يذهب مباشرة لمسار النص (أسرع من استخراج الجداول)


def _pdf_page_count(path: str) -> int:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return len(pdf.pages)
    except Exception:
        return 0


def extract(path: str) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()

    # الصور دائماً عبر الذكاء الاصطناعي
    if ext in (".png", ".jpg", ".jpeg", ".webp", ".heic"):
        return extract_with_ai(path)

    # PDF: نوجّه حسب الحجم — الصغير جدولياً حتمياً، الكبير عبر النص المقسّم المتوازي
    if ext == ".pdf":
        n = _pdf_page_count(path)
        if n > _PDF_MAX_PAGES:
            raise ExtractionError(
                f"كشفك {n} صفحة — ضخم جداً كملف PDF. من تطبيق بنكك اختر «تصدير» واحفظه كـ "
                "Excel أو CSV، وارفعه هنا — يُعالَج فوراً وبدقة مهما بلغ حجمه (آلاف الصفحات).")
        if n > _PDF_DETERMINISTIC_MAX and _has_ai():
            return extract_with_ai(path)   # كشف كبير → مسار النص المقسّم المتوازي مباشرة

    # الصيغ المهيكلة: نجرّب القراءة الحتمية أولاً، ونرجع للذكاء الاصطناعي عند الفشل
    try:
        if ext in (".xlsx", ".xls"):
            return _normalize(pd.read_excel(path), source=ext)
        if ext == ".csv":
            return _normalize(pd.read_csv(path), source=ext)
        if ext == ".pdf":
            return _normalize(_read_pdf_table(path), source=ext)
        if ext == ".docx":
            return _normalize(_read_docx_table(path), source=ext)
        if ext == ".txt":
            return _normalize(_read_txt_table(path), source=ext)
    except ExtractionError:
        if _has_ai():
            return extract_with_ai(path)   # كشف فوضوي / بلا جدول → الذكاء الاصطناعي
        raise
    raise ExtractionError(f"صيغة غير مدعومة: {ext}")


# ---------- التطبيع (مطابقة الأعمدة + اشتقاق النوع) ----------
def _match_col(cols, targets):
    norm = {str(c).strip().lower(): c for c in cols}
    for t in targets:
        for k, orig in norm.items():
            if t.lower() == k or t.lower() in k:
                return orig
    return None


def _normalize(df: pd.DataFrame, source: str) -> pd.DataFrame:
    if df is None or df.empty:
        raise ExtractionError("لم يُعثر على جدول عمليات صالح في الملف.")
    cols = list(df.columns)
    mapping = {}
    for std in STD_COLS + ["_مدين", "_دائن"]:
        found = _match_col(cols, SYN[std])
        if found is not None:
            mapping[std] = found

    if "المبلغ" not in mapping and not ("_مدين" in mapping or "_دائن" in mapping):
        raise ExtractionError(
            "ما قدرت أتعرف على عمود المبلغ. تأكد أن الملف فيه جدول واضح، "
            "أو استخدم القالب الجاهز (التاريخ، البيان، النوع، التصنيف، الطرف، المبلغ).")

    out = pd.DataFrame()
    out["التاريخ"] = df[mapping["التاريخ"]] if "التاريخ" in mapping else pd.NaT
    out["البيان"] = df[mapping["البيان"]] if "البيان" in mapping else ""
    out["التصنيف"] = df[mapping["التصنيف"]] if "التصنيف" in mapping else "غير مصنّف"
    out["الطرف"] = df[mapping["الطرف"]] if "الطرف" in mapping else "غير محدد"

    # المبلغ والنوع — عدة سيناريوهات
    if "المبلغ" in mapping:
        amt = pd.to_numeric(df[mapping["المبلغ"]].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
                            errors="coerce").fillna(0.0)
        if "النوع" in mapping:
            out["النوع"] = df[mapping["النوع"]].astype(str)
            out["المبلغ"] = amt.abs()
        else:
            # اشتقاق النوع من إشارة المبلغ (سالب = مصروف)
            out["النوع"] = amt.apply(lambda v: "مصروف" if v < 0 else "دخل")
            out["المبلغ"] = amt.abs()
    else:
        # عمودا مدين/دائن منفصلان
        debit = pd.to_numeric(df[mapping["_مدين"]], errors="coerce").fillna(0.0) if "_مدين" in mapping else 0.0
        credit = pd.to_numeric(df[mapping["_دائن"]], errors="coerce").fillna(0.0) if "_دائن" in mapping else 0.0
        net = (credit if isinstance(credit, (int, float)) else credit) - \
              (debit if isinstance(debit, (int, float)) else debit)
        out["النوع"] = net.apply(lambda v: "دخل" if v >= 0 else "مصروف")
        out["المبلغ"] = net.abs()

    # لو النوع نصّي غامض، نطبّعه لدخل/مصروف عبر التلميحات
    out["النوع"] = out["النوع"].apply(
        lambda s: "دخل" if INCOME_HINT.search(str(s)) else ("مصروف" if str(s).strip() else "مصروف"))

    out = out[out["المبلغ"] > 0].reset_index(drop=True)
    if out.empty:
        raise ExtractionError("الجدول لا يحتوي على مبالغ صالحة.")
    return out[STD_COLS]


# ---------- قرّاء الصيغ ----------
def _read_pdf_table(path):
    import pdfplumber
    rows = []
    header = None
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in (page.extract_tables() or []):
                if not table:
                    continue
                if header is None:
                    header = [str(h).strip() if h else f"col{i}" for i, h in enumerate(table[0])]
                    body = table[1:]
                else:
                    body = table
                for r in body:
                    if r and any(c for c in r):
                        rows.append(r[:len(header)])
    if not header or not rows:
        raise ExtractionError("ما لقيت جدول في ملف PDF. لو الملف صورة/ممسوح، يحتاج طبقة الذكاء الاصطناعي.")
    return pd.DataFrame(rows, columns=header)


def _read_docx_table(path):
    import docx
    doc = docx.Document(path)
    if not doc.tables:
        raise ExtractionError("ملف Word لا يحتوي جدولاً. ضع البيانات في جدول بأعمدة واضحة.")
    t = doc.tables[0]
    header = [c.text.strip() for c in t.rows[0].cells]
    rows = [[c.text.strip() for c in row.cells] for row in t.rows[1:]]
    return pd.DataFrame(rows, columns=header)


def _read_txt_table(path):
    # نص مفصول بفواصل/تبويب
    for sep in [",", "\t", ";", "|"]:
        try:
            df = pd.read_csv(path, sep=sep)
            if df.shape[1] >= 3:
                return df
        except Exception:
            continue
    raise ExtractionError("ما قدرت أقرأ الملف النصي كجدول.")


# ---------- طبقة الذكاء الاصطناعي: قارئ كشوف البنوك الذكي ----------
# النموذج الافتراضي: Opus 4.8 — الأدق في قراءة الأرقام العربية من الكشوف الممسوحة.
# الدقة هنا هي المنتج (حصننا ضد ChatGPT)؛ التكلفة لكل مستند ضئيلة أمام الاشتراك الشهري.
# قابل للتبديل عبر ANTHROPIC_MODEL لمن يريد نموذجاً أرخص عن قصد.
# نموذج سريع للاستخراج المنظّم — Haiku 4.5 سريع ودقيق وأرخص بكثير من Opus.
# (Opus كان يجعل تحليل كشف حقيقي يستغرق دقيقة–دقيقتين ويبدو معلّقاً.)
AI_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

_IMAGE_MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".webp": "image/webp"}

# مخطط الإخراج المنظّم — يضمن JSON صالح دائماً
_TX_SCHEMA = {
    "type": "object",
    "properties": {
        "transactions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "تاريخ العملية YYYY-MM-DD"},
                    "description": {"type": "string", "description": "بيان العملية"},
                    "type": {"type": "string", "enum": ["دخل", "مصروف"]},
                    "category": {"type": "string", "description": "تصنيف عربي: رواتب/إيجار/تسويق/مبيعات/مشتريات/تحويلات/رسوم بنكية/وقود/تشغيل/أخرى"},
                    "party": {"type": "string", "description": "اسم الطرف أو التاجر"},
                    "amount": {"type": "number", "description": "المبلغ موجب"},
                },
                "required": ["date", "description", "type", "category", "party", "amount"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["transactions"],
    "additionalProperties": False,
}

_AI_PROMPT = (
    "أنت محلل مالي خبير في كشوف الحسابات البنكية السعودية (الراجحي، الأهلي، الإنماء، "
    "بنك ساب، الرياض) وأنظمة المحاسبة (قيود، دفترة). استخرج كل العمليات من هذا المستند.\n"
    "لكل عملية: حدّد النوع (دخل أو مصروف)، واستنتج تصنيفاً عربياً مناسباً من البيان أو اسم "
    "التاجر (مثال: 'محطة الدريس' → وقود، 'راتب' → رواتب، 'إيجار' → إيجار، تحويل من عميل → "
    "مبيعات)، واسم الطرف/التاجر، والمبلغ كرقم موجب، والتاريخ بصيغة YYYY-MM-DD.\n"
    "تجاهل عمود الرصيد الجاري إن وُجد — نريد مبلغ العملية فقط. لا تخترع عمليات غير موجودة. "
    "أعِد كل العمليات التي تراها."
)


def _pdf_all_text(path: str) -> str:
    """يستخرج نص كل صفحات الـPDF (للكشوف النصّية — الأغلبية)."""
    import pdfplumber
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
    return "\n".join(parts)


# القيد الحقيقي على حجم الجزء = مخرجات النموذج (≤16 ألف توكن).
# عملية واحدة ≈ ~45 توكن مخرجات، فنحدّ كل جزء بعدد أسطر آمن (+حدّ أحرف للأسطر الطويلة).
_CHUNK_LINES = 220
_CHUNK_CHARS = 45000
_MAX_CHUNKS = 14  # يكفي ~3000 عملية (مئات الصفحات)؛ أبعد منه نوجّه لتصدير Excel


def _chunk_text(text: str, max_lines: int = _CHUNK_LINES, max_chars: int = _CHUNK_CHARS):
    """يقسّم النص على حدود الأسطر — بحدّ أقصى للأسطر (يضبط المخرجات) وللأحرف (يضبط المدخلات)."""
    lines = text.splitlines(keepends=True)
    chunks, cur, n_lines, n_chars = [], [], 0, 0
    for ln in lines:
        if cur and (n_lines >= max_lines or n_chars + len(ln) > max_chars):
            chunks.append("".join(cur)); cur, n_lines, n_chars = [], 0, 0
        cur.append(ln); n_lines += 1; n_chars += len(ln)
    if cur:
        chunks.append("".join(cur))
    return chunks or [text]


def _call_model(client, anthropic, content_blocks) -> list:
    """مكالمة واحدة للنموذج → قائمة عمليات خام. تعالج الأخطاء وحالات التوقف."""
    import json
    try:
        resp = client.messages.create(
            model=AI_MODEL, max_tokens=16000, system=_AI_PROMPT,
            messages=[{"role": "user", "content": content_blocks}],
            output_config={"format": {"type": "json_schema", "schema": _TX_SCHEMA}},
        )
    except anthropic.AuthenticationError:
        _log.error("Anthropic auth failed — invalid API key")
        raise ExtractionError("الخدمة غير متاحة مؤقتاً. حاول بعد قليل.")
    except anthropic.APITimeoutError:
        raise ExtractionError("المعالجة أخذت وقتاً أطول من المتوقع. جرّب تصدير الكشف كملف Excel — يُعالَج فوراً.")
    except anthropic.RateLimitError:
        raise ExtractionError("الخدمة مشغولة حالياً. أعد المحاولة بعد دقيقة.")
    except anthropic.BadRequestError as e:
        msg = str(getattr(e, "message", e))
        _log.error("Anthropic 400: %s", msg)
        if "too long" in msg or "maximum" in msg.lower() or "PDF pages" in msg:
            raise ExtractionError(
                "هذا الكشف ضخم. صدّره كملف Excel أو CSV من بنكك — يُعالَج فوراً وبدقة مهما كان حجمه.")
        raise ExtractionError("الخدمة غير متاحة مؤقتاً. حاول بعد قليل.")
    except anthropic.APIConnectionError:
        raise ExtractionError("تعذّر الاتصال بخدمة الذكاء الاصطناعي. تأكد من الإنترنت وحاول مرة أخرى.")
    except anthropic.APIError as e:
        _log.error("Anthropic API error: %s", getattr(e, "message", e))
        raise ExtractionError("الخدمة غير متاحة مؤقتاً. حاول بعد قليل.")

    if resp.stop_reason == "refusal":
        raise ExtractionError("تعذّرت معالجة هذا الملف. جرّب ملفاً آخر أو صيغة أوضح.")
    if resp.stop_reason == "max_tokens":
        raise ExtractionError(
            "هذا الكشف يحوي عمليات أكثر من أن تُعالَج دفعة. صدّره كملف Excel/CSV، أو ارفع فترة أقصر.")
    text = next((b.text for b in resp.content if b.type == "text"), "")
    try:
        return json.loads(text).get("transactions", [])
    except (json.JSONDecodeError, AttributeError):
        raise ExtractionError("ما قدرنا نقرأ العمليات من المستند. تأكد أنه كشف حساب واضح.")


def _extract_text_via_ai(client, anthropic, text: str) -> list:
    """يقسّم النص الطويل إلى أجزاء ويعالجها بالتوازي ثم يدمج — سريع ويتوسّع لأي حجم."""
    chunks = _chunk_text(text)
    if len(chunks) > _MAX_CHUNKS:
        raise ExtractionError(
            "الكشف ضخم (مئات الصفحات). صدّره كملف Excel أو CSV من تطبيق بنكك — "
            "يُعالَج فوراً وبدقة مهما كان عدد صفحاته.")
    if len(chunks) == 1:
        return _call_model(client, anthropic,
                           [{"type": "text", "text": "محتوى كشف الحساب:\n\n" + chunks[0]}])

    # أجزاء متعددة → توازٍ (كل جزء مكالمة I/O مستقلّة) لتقليص الزمن للثلث
    from concurrent.futures import ThreadPoolExecutor
    def _one(ch):
        return _call_model(client, anthropic,
                           [{"type": "text", "text": "محتوى كشف الحساب (جزء):\n\n" + ch}])
    # توازٍ محدود (3): يوازن بين السرعة وذاكرة الخطة المجانية (512MB) لتفادي 502
    workers = int(os.environ.get("AI_WORKERS", "3"))
    rows = []
    with ThreadPoolExecutor(max_workers=min(len(chunks), workers)) as ex:
        for part in ex.map(_one, chunks):     # يحافظ على الترتيب ويرفع أي ExtractionError
            rows += part
    return rows


def extract_with_ai(path: str) -> pd.DataFrame:
    """
    تحوّل أي ملف (صورة، PDF، كشف بنكي، مستند فوضوي) إلى جدول عمليات موحّد.
    الكشوف النصّية الطويلة تُقسَّم تلقائياً لتتجاوز حد سياق النموذج (يتوسّع لأي حجم).
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ExtractionError(
            "قراءة الصور والكشوف الممسوحة تحتاج تفعيل طبقة الذكاء الاصطناعي "
            "(مفتاح Claude API في متغير البيئة ANTHROPIC_API_KEY). "
            "مبدئياً استخدم Excel / CSV / PDF / Word فيه جدول واضح.")
    try:
        import anthropic
    except ImportError:
        raise ExtractionError("مكتبة anthropic غير مثبّتة: pip install anthropic")

    import base64
    ext = os.path.splitext(path)[1].lower()
    client = anthropic.Anthropic(timeout=100.0, max_retries=1)   # يفشل بلطف بدل التعليق للأبد

    if ext in _IMAGE_MEDIA:                                    # صورة كشف
        with open(path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode()
        rows = _call_model(client, anthropic, [{"type": "image", "source": {
            "type": "base64", "media_type": _IMAGE_MEDIA[ext], "data": data}}])
    elif ext == ".pdf":
        text = ""
        try:
            text = _pdf_all_text(path)
        except Exception:
            text = ""
        if len(text.strip()) >= 200:                          # PDF نصّي → نص مقسّم (بلا حد صفحات)
            rows = _extract_text_via_ai(client, anthropic, text)
        else:                                                 # PDF ممسوح (صورة) → مستند
            with open(path, "rb") as f:
                data = base64.standard_b64encode(f.read()).decode()
            rows = _call_model(client, anthropic, [{"type": "document", "source": {
                "type": "base64", "media_type": "application/pdf", "data": data}}])
    else:                                                     # xlsx/csv/txt فوضوي → نص مقسّم
        if ext in (".xlsx", ".xls"):
            text = pd.read_excel(path).to_csv(index=False)
        else:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        rows = _extract_text_via_ai(client, anthropic, text)

    if not rows:
        raise ExtractionError("ما لقينا عمليات في المستند.")
    df = pd.DataFrame(rows).rename(columns={
        "date": "التاريخ", "description": "البيان", "type": "النوع",
        "category": "التصنيف", "party": "الطرف", "amount": "المبلغ"})
    return _normalize(df, source="ai")
