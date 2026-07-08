"""
مولّد بيانات تجريبية — كشف عمليات بسيط لشركة صيانة سعودية صغيرة.
مصمم بقصة واقعية عشان التقرير يبيّن قيمته:
  - عميل واحد (شركة الواحة) ~45% من الدخل  => خطر تركّز العملاء
  - مصروف التسويق ينتفخ آخر شهرين          => نزيف
  - الرواتب تكبر + الأرباح تتآكل شهر بعد شهر => اتجاه خطر
  - السيولة تنزل تدريجياً                    => تحذير سيولة
البيانات ثابتة (seed) عشان تتكرر بنفس الشكل.
"""
import random
from datetime import date, timedelta
import openpyxl

random.seed(42)

# أعمدة كشف العمليات (زي كشف حساب بنكي مبسّط)
COLUMNS = ["التاريخ", "البيان", "النوع", "التصنيف", "الطرف", "المبلغ"]

# العملاء ونسبهم التقريبية من الدخل (شركة الواحة مهيمنة = خطر تركّز)
CUSTOMERS = [
    ("شركة الواحة القابضة", 0.45),
    ("مؤسسة النخيل التجارية", 0.13),
    ("شركة البناء الحديث", 0.11),
    ("مجمع الرياض الطبي", 0.09),
    ("مؤسسة الصقر", 0.07),
    ("شركة الديار", 0.06),
    ("عميل نقدي", 0.05),
    ("مؤسسة الفجر", 0.04),
]

MONTHS = [(2026, m) for m in range(1, 7)]  # يناير–يونيو 2026

# إجمالي الدخل المستهدف لكل شهر (شبه ثابت — المبيعات مو المشكلة)
MONTHLY_REVENUE = {1: 165000, 2: 172000, 3: 168000, 4: 175000, 5: 170000, 6: 178000}

# مصاريف التسويق تنفجر آخر شهرين (النزيف)
MARKETING = {1: 9000, 2: 10500, 3: 11000, 4: 12000, 5: 28000, 6: 34000}

# الرواتب تكبر (توظيف بدون عائد واضح)
SALARIES = {1: 62000, 2: 62000, 3: 68000, 4: 68000, 5: 78000, 6: 78000}

RENT = 22000            # إيجار ثابت
OPS_BASE = 8000         # مصاريف تشغيلية أساسية
PURCHASES_RATE = 0.34   # مشتريات/تكلفة مباشرة كنسبة من الدخل


def month_days(y, m):
    if m == 12:
        return (date(y + 1, 1, 1) - date(y, m, 1)).days
    return (date(y, m + 1, 1) - date(y, m, 1)).days


def rand_day(y, m):
    return date(y, m, random.randint(1, min(28, month_days(y, m))))


def build_rows():
    rows = []
    for (y, m) in MONTHS:
        target = MONTHLY_REVENUE[m]
        # توزيع الدخل على العملاء حسب نسبهم، مع فواتير متعددة
        for name, share in CUSTOMERS:
            cust_total = target * share
            n_invoices = random.randint(1, 3)
            for _ in range(n_invoices):
                amt = round(cust_total / n_invoices * random.uniform(0.85, 1.15), 2)
                rows.append([
                    rand_day(y, m), f"فاتورة خدمات صيانة", "دخل",
                    "مبيعات خدمات", name, amt,
                ])
        # المصاريف
        rows.append([rand_day(y, m), "رواتب الموظفين", "مصروف", "رواتب", "الموظفون", SALARIES[m]])
        rows.append([rand_day(y, m), "إيجار المقر", "مصروف", "إيجار", "شركة العقارات", RENT])
        rows.append([rand_day(y, m), "حملات إعلانية", "مصروف", "تسويق", "منصات إعلانية", MARKETING[m]])
        rows.append([rand_day(y, m), "مشتريات مواد ومعدات", "مصروف", "مشتريات",
                     "موردون", round(target * PURCHASES_RATE * random.uniform(0.95, 1.05), 2)])
        rows.append([rand_day(y, m), "مصاريف تشغيلية", "مصروف", "تشغيل",
                     "متنوع", round(OPS_BASE * random.uniform(0.9, 1.2), 2)])
        # مصروف متأخر أحياناً
        if m in (4, 6):
            rows.append([rand_day(y, m), "صيانة سيارات الشركة", "مصروف", "تشغيل",
                         "ورشة", round(random.uniform(3000, 6000), 2)])

    rows.sort(key=lambda r: r[0])
    # نحوّل التاريخ لنص عشان يظهر واضح في Excel
    for r in rows:
        r[0] = r[0].strftime("%Y-%m-%d")
    return rows


def main():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "العمليات"
    ws.sheet_view.rightToLeft = True
    ws.append(COLUMNS)
    for row in build_rows():
        ws.append(row)
    out = "بيانات_تجريبية.xlsx"
    wb.save(out)
    print(f"تم إنشاء ملف البيانات التجريبية: {out}")
    print(f"عدد العمليات: {ws.max_row - 1}")


if __name__ == "__main__":
    main()
