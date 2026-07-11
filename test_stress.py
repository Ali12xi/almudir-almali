"""
تحقّق StressTest — يشغّل المحرك على ملف أزمة التدفق النقدي ويقارن
المكتشفات بمفتاح الإجابة (Answer_Key). يطبع نسبة الاكتشاف والصياغة العربية.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import engine
import i18n

FILE = "C:/Users/Alibi/Downloads/StressTest_CashFlowCrisis (1).xlsx"
# رصيد نقدي واقعي لشركة في أزمة تحصيل (نُدخله ليُفعّل تقدير الأيام)
CASH = 120000


def run(cash):
    a = engine.analyze(FILE, current_cash=cash)
    print(f"\n{'='*70}\nCASH = {cash}\n{'='*70}")
    print(f"عمليات: {a.n_transactions} | أشهر: {len(a.months)}")
    print(f"استحقاق؟ {a.is_accrual} | فواتير: {a.invoiced_total:,.0f} | "
          f"تحصيل: {a.collected_total:,.0f} | ذمم: {a.receivables:,.0f} | "
          f"نسبة تحصيل: {a.collection_rate*100:.0f}%")
    print(f"نقد داخل (فعلي): {a.total_income:,.0f} | صادر: {a.total_expense:,.0f} | "
          f"صافي التدفق: {a.net_profit:,.0f}")
    print(f"تشغيلي داخل: {a.operating_income:,.0f} | تشغيلي خارج: {a.operating_expense:,.0f}")
    print(f"رواتب: {a.salary_total:,.0f} ({a.salary_ratio*100:.0f}%) | موظفون: {a.salary_count}")
    print(f"مؤشر الأمان: {a.safety_score}/100 ({a.safety_band}) | "
          f"بقاء: {a.survival_days} | وسادة: {a.buffer_months}")

    print("\n-- تفكيك المؤشر --")
    for reason, pts in a.score_breakdown:
        print(f"   {pts:+d}  {reason}")

    if getattr(a, "risk_chain", None):
        print("\n-- سلسلة السبب والنتيجة --")
        for line in i18n.risk_chain_sentences(a, "ar"):
            print("   ", line)

    print("\n-- المكتشفات (مرتّبة بالأولوية) --")
    for f in a.findings:
        badge = i18n.priority_badge(f.get("severity", "medium"), "ar")
        print(f"   {badge} [{f['key']}] {i18n.finding_title(f,'ar')}")
        print(f"        {i18n.finding_text(f,'ar')}")

    print("\n-- التوصيات --")
    for r in a.recommendations:
        print("   •", i18n.rec_text(r, "ar"))
    return a


def score_answer_key(a):
    keys = {f["key"] for f in a.findings}
    text_blob = " ".join(i18n.finding_text(f, "ar") for f in a.findings)
    text_blob += " " + " ".join(i18n.rec_text(r, "ar") for r in a.recommendations)
    if getattr(a, "risk_chain", None):
        text_blob += " " + " ".join(i18n.risk_chain_sentences(a, "ar"))
    text_blob += " " + i18n.recurring_sentence(a, "ar") if a.recurring else ""

    checks = [
        ("أزمة التدفق (تأخر التحصيل)", "receivables_crisis" in keys),
        ("اشتراك Legacy CRM المنسي", any("crm" in r["party"].lower() or "legacy" in r["party"].lower()
                                          for r in a.recurring)),
        ("شراء أصل كبير في وقت ضغط", "large_asset_purchase" in keys),
        ("التزامات ثابتة مرتفعة (رواتب/قرض/إيجار)", "high_payroll" in keys or a.salary_total > 0),
        ("تراكم الحسابات المدينة", a.receivables > 0 and "receivables_crisis" in keys),
        ("عدم إطلاق إنذار كهرباء موسمي كاحتيال",
         not any("كهرباء" in i18n.finding_title(f, "ar") or
                 (f["key"] == "expense_spike" and "كهرباء" in str(f["data"].get("category", "")))
                 for f in a.findings)),
    ]
    print(f"\n{'='*70}\nمقارنة بمفتاح الإجابة\n{'='*70}")
    hit = 0
    for name, cond in checks:
        print(f"   {'✅' if cond else '❌'} {name}")
        hit += 1 if cond else 0
    print(f"\n   النتيجة: {hit}/{len(checks)}")
    return hit, len(checks)


if __name__ == "__main__":
    a = run(CASH)
    score_answer_key(a)
