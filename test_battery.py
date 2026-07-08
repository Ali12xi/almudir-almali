"""
بطارية اختبارات — دقة الأرقام + الحالات الحدّية + الأمان.
تشتغل على المحرك والطبقات مباشرة (سريع)، بلا خادم.
"""
import os
import sys
# ويندوز يستخدم ترميز cp1256 افتراضياً في الكونسول → ينهار على الرموز؛ نفرض UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import tempfile
import pandas as pd
import engine
import report
import extractors
import i18n

TMP = tempfile.mkdtemp(prefix="almudir_test_")
passed = 0
failed = 0


def ok(name, cond):
    global passed, failed
    if cond:
        passed += 1; print(f"  [نجح] {name}")
    else:
        failed += 1; print(f"  [فشل] {name}  <<<<<<")


def make_xlsx(rows, name):
    df = pd.DataFrame(rows, columns=["التاريخ", "البيان", "النوع", "التصنيف", "الطرف", "المبلغ"])
    p = os.path.join(TMP, name)
    df.to_excel(p, index=False)
    return p


print("== 1) دقة الأرقام (بيانات معروفة يدوياً) ==")
rows = [
    ("2026-01-05", "فاتورة", "دخل", "مبيعات", "عميل أ", 1000),
    ("2026-01-10", "فاتورة", "دخل", "مبيعات", "عميل ب", 500),
    ("2026-01-15", "إيجار", "مصروف", "إيجار", "مالك", 300),
    ("2026-02-05", "فاتورة", "دخل", "مبيعات", "عميل أ", 1200),
    ("2026-02-10", "إيجار", "مصروف", "إيجار", "مالك", 400),
    ("2026-02-20", "إعلان", "مصروف", "تسويق", "منصة", 200),
]
a = engine.analyze(make_xlsx(rows, "known.xlsx"), current_cash=None)
ok("إجمالي الدخل = 2700", abs(a.total_income - 2700) < 1e-6)
ok("إجمالي المصاريف = 900", abs(a.total_expense - 900) < 1e-6)
ok("صافي الربح = 1800", abs(a.net_profit - 1800) < 1e-6)
ok("الهامش ≈ 66.7%", abs(a.avg_margin - 1800/2700) < 1e-6)
ok("أكبر عميل = عميل أ", a.income_by_customer[0][0] == "عميل أ")
ok("حصة عميل أ ≈ 81.5%", abs(a.income_by_customer[0][2] - 2200/2700) < 1e-6)
ok("كشف تركّز العملaء", any(f["key"] == "customer_concentration" for f in a.findings))

print("== 2) حالة: بلا رصيد بنكي → لا تحذير سيولة ==")
ok("runway معروف=False", a.runway is not None and a.runway.get("known") is False)

print("== 3) حالة: شهر واحد فقط ==")
one = [("2026-03-01", "فاتورة", "دخل", "مبيعات", "عميل أ", 900),
       ("2026-03-05", "إيجار", "مصروف", "إيجار", "مالك", 300)]
a1 = engine.analyze(make_xlsx(one, "one.xlsx"), current_cash=5000)
ok("لا ينهار بشهر واحد", a1.n_transactions == 2)
ok("لا يوجد تنبؤ سيولة (يحتاج شهرين)", a1.runway is None)
ok("يطلع تقرير بلا خطأ", report.generate(a1, os.path.join(TMP, "one.pdf"), "ش", "ar"))

print("== 4) حالة: كله دخل بلا مصاريف ==")
allinc = [("2026-01-01", "ف", "دخل", "مبيعات", "أ", 500),
          ("2026-02-01", "ف", "دخل", "مبيعات", "أ", 700)]
a2 = engine.analyze(make_xlsx(allinc, "inc.xlsx"), current_cash=1000)
ok("مصاريف = 0", a2.total_expense == 0)
ok("هامش = 100%", abs(a2.avg_margin - 1.0) < 1e-6)
ok("تقرير سليم", report.generate(a2, os.path.join(TMP, "inc.pdf"), "ش", "en"))

print("== 5) حالة: كله مصاريف بلا دخل ==")
allexp = [("2026-01-01", "إيجار", "مصروف", "إيجار", "مالك", 500),
          ("2026-02-01", "إيجار", "مصروف", "إيجار", "مالك", 500)]
a3 = engine.analyze(make_xlsx(allexp, "exp.xlsx"), current_cash=1000)
ok("دخل = 0 بلا قسمة على صفر", a3.total_income == 0 and a3.avg_margin == 0)
ok("احتراق سيولة مكتشف", a3.runway and a3.runway.get("burning") is True)
ok("تقرير سليم", report.generate(a3, os.path.join(TMP, "exp.pdf"), "ش", "ar"))

print("== 6) اشتقاق النوع من إشارة المبلغ (سالب=مصروف) ==")
signed = pd.DataFrame({
    "date": ["2026-01-01", "2026-01-02"],
    "description": ["بيع", "شراء"],
    "amount": [1000, -400],
    "party": ["عميل", "مورد"],
})
sp = os.path.join(TMP, "signed.csv"); signed.to_csv(sp, index=False, encoding="utf-8-sig")
df_s = extractors.extract(sp)
ok("سالب صار مصروف", (df_s[df_s["المبلغ"] == 400]["النوع"] == "مصروف").all())
ok("موجب صار دخل", (df_s[df_s["المبلغ"] == 1000]["النوع"] == "دخل").all())

print("== 7) ملف بلا عمود مبلغ → خطأ ودود بلا انهيار ==")
bad = pd.DataFrame({"foo": [1], "bar": [2]})
bp = os.path.join(TMP, "bad.csv"); bad.to_csv(bp, index=False)
try:
    extractors.extract(bp); ok("رفع خطأ", False)
except extractors.ExtractionError:
    ok("رفع ExtractionError ودود", True)
except Exception:
    ok("نوع الخطأ صحيح", False)

print("== 8) صيغة غير مدعومة → خطأ واضح ==")
zp = os.path.join(TMP, "x.zip"); open(zp, "w").write("x")
try:
    extractors.extract(zp); ok("رفض الصيغة", False)
except extractors.ExtractionError:
    ok("رفض الصيغة غير المدعومة", True)

print("== 9) صورة بلا مفتاح AI → رسالة توجيه واضحة ==")
ip = os.path.join(TMP, "s.png"); open(ip, "wb").write(b"\x89PNG\r\n")
_saved_key = os.environ.pop("ANTHROPIC_API_KEY", None)   # اختبر مسار «بلا مفتاح» حتمياً
try:
    extractors.extract(ip); ok("طلب مفتاح", False)
except extractors.ExtractionError as e:
    ok("رسالة الذكاء الاصطناعي", "الذكاء الاصطناعي" in str(e) or "AI" in str(e))
finally:
    if _saved_key:
        os.environ["ANTHROPIC_API_KEY"] = _saved_key

print("== 10) الترجمة: نفس التحليل بلغتين ==")
ok("قرار عربي", i18n.decision_headline(255000, "yearly", "ar").find("ريال") > 0)
ok("قرار إنجليزي", i18n.decision_headline(255000, "yearly", "en").find("SAR") > 0)

print(f"\n=== النتيجة: {passed} نجح / {failed} فشل ===")
