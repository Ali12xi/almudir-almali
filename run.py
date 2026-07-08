"""
المدير المالي — النسخة صفر (سكربت محلي).
الاستخدام:
    python run.py <ملف_الكشف.xlsx> [--cash الرصيد_الحالي] [--company اسم_الشركة] [--out المخرج.pdf]

مثال:
    python run.py بيانات_تجريبية.xlsx --cash 120000 --company "مؤسسة الإتقان" --out تقرير.pdf
"""
import argparse
import sys
import engine
import report
import i18n


def main():
    p = argparse.ArgumentParser(description="المدير المالي — تحليل مالي وتقرير")
    p.add_argument("file", help="ملف كشف العمليات (Excel/CSV/PDF/Word/نص)")
    p.add_argument("--cash", type=float, default=None,
                   help="الرصيد البنكي الحالي (لتنبؤ السيولة)")
    p.add_argument("--company", default="شركتك", help="اسم الشركة")
    p.add_argument("--lang", default="ar", choices=["ar", "en"], help="لغة التقرير")
    p.add_argument("--out", default="تقرير_المدير_المالي.pdf", help="ملف التقرير الناتج")
    args = p.parse_args()

    try:
        a = engine.analyze(args.file, current_cash=args.cash)
    except Exception as e:
        print(f"خطأ في قراءة/تحليل الملف: {e}", file=sys.stderr)
        sys.exit(1)

    report.generate(a, args.out, company=args.company, lang=args.lang)
    print(f"[تم] التقرير: {args.out}")
    print(f"     الفترة: {a.period_label} | عمليات: {a.n_transactions}")
    print(f"     صافي: {a.net_profit:,.0f} | هامش: {a.avg_margin*100:.1f}%")
    if a.decision:
        print("     قرار الأسبوع: " +
              i18n.decision_headline(a.decision["sar"], a.decision["timeframe"], args.lang))


if __name__ == "__main__":
    main()
