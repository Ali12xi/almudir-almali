"""
i18n — مصدر واحد لكل النصوص (عربي/إنجليزي).
يفصل الصياغة عن الحساب: المحرك يُنتج بيانات رقمية + مفاتيح،
وهنا نحوّلها إلى جُمل بأي لغة. هذا يخدم التقرير والواجهة معاً.
"""
from __future__ import annotations

LANGS = ("ar", "en")


def norm_lang(lang: str) -> str:
    return "en" if str(lang).lower().startswith("en") else "ar"


def money(v, lang="ar") -> str:
    n = f"{abs(round(v)):,.0f}"
    return f"{n} ريال" if lang == "ar" else f"SAR {n}"


def pct(v) -> str:
    return f"{v*100:.0f}%"


def timeframe_word(tf, lang):
    return {"monthly": ("شهرياً", "per month"),
            "yearly": ("سنوياً", "per year")}.get(tf, ("", ""))[0 if lang == "ar" else 1]


# ---------- عناوين شارات المخاطر ----------
def finding_title(f, lang) -> str:
    k = f["key"]
    if k == "customer_concentration":
        return "تركّز العملاء" if lang == "ar" else "Client concentration"
    if k == "margin_erosion":
        return "تآكل صافي التدفق" if lang == "ar" else "Cash-flow erosion"
    if k == "sales_up_profit_down":
        return "الوارد يزيد / الصافي ينقص" if lang == "ar" else "Inflows up / net down"
    if k == "expense_spike":
        cat = f["data"]["category"]
        return f"قفزة في مصروف: {cat}" if lang == "ar" else f"Spike in {cat}"
    if k == "thin_cushion":
        return "وسادة أمان رقيقة" if lang == "ar" else "Thin safety cushion"
    if k == "high_payroll":
        return "عبء رواتب مرتفع" if lang == "ar" else "Heavy payroll load"
    return ""


# ---------- نص المخاطرة ----------
def finding_text(f, lang) -> str:
    k, d = f["key"], f["data"]
    if k == "customer_concentration":
        if lang == "ar":
            return (f"أكبر مصدر وارد ({d['name']}) يمثّل {pct(d['share'])} من الوارد إلى حسابك. "
                    f"لو توقّف، ينقص وارِدك حوالي {money(d['monthly'], 'ar')} شهرياً.")
        return (f"Your largest inflow source ({d['name']}) makes up {pct(d['share'])} of money coming in. "
                f"If it stops, your inflows drop about {money(d['monthly'], 'en')} per month.")
    if k == "margin_erosion":
        if lang == "ar":
            return (f"نسبة صافي تدفقك النقدي نزلت من {pct(d['first'])} إلى {pct(d['last'])} خلال الفترة "
                    f"(انخفاض {d['drop_pts']:.0f} نقطة). ما يبقى في حسابك من كل ريال وارد يتآكل.")
        return (f"Your net cash-flow ratio fell from {pct(d['first'])} to {pct(d['last'])} over the period "
                f"(a {d['drop_pts']:.0f}-point drop). Less of each riyal coming in stays in your account.")
    if k == "sales_up_profit_down":
        if lang == "ar":
            return "الوارد إلى حسابك يرتفع لكن صافي تدفقك ينخفض — مدفوعاتك تكبر أسرع من الوارد."
        return "Money coming in is rising but your net cash flow is falling — outflows are growing faster than inflows."
    if k == "expense_spike":
        if lang == "ar":
            return (f"مصروف «{d['category']}» قفز من ~{money(d['early'],'ar')} إلى ~{money(d['late'],'ar')} شهرياً. "
                    f"لو رجع لمستواه الطبيعي، توفّر حوالي {money(d['excess_year'],'ar')} سنوياً.")
        return (f"Your «{d['category']}» expense jumped from ~{money(d['early'],'en')} to ~{money(d['late'],'en')} per month. "
                f"Bringing it back to normal saves about {money(d['excess_year'],'en')} per year.")
    if k == "thin_cushion":
        if lang == "ar":
            return (f"يتحمّل وارِدك انخفاضاً حتى {pct(d['drop_pct'])} فقط قبل أن يصير تدفقك النقدي سالباً — "
                    f"وسادة ضيّقة. أي تراجع مفاجئ أو توقّف مصدر وارد يدخلك منطقة الخطر بسرعة.")
        return (f"Your inflows can fall only {pct(d['drop_pct'])} before your cash flow turns negative — "
                f"a thin cushion. Any sudden dip or lost inflow source pushes you into the red fast.")
    if k == "high_payroll":
        if lang == "ar":
            return (f"الرواتب تلتهم {pct(d['ratio'])} من الوارد إلى حسابك (~{money(d['monthly'],'ar')} شهرياً "
                    f"لـ{d['count']} مستفيد). نسبة مرتفعة تجعل أي شهر ضعيف يضغط على نقدك مباشرة.")
        return (f"Payroll eats {pct(d['ratio'])} of your inflows (~{money(d['monthly'],'en')}/month "
                f"for {d['count']} recipients). A high ratio means any slow month squeezes your cash immediately.")
    return ""


# ---------- قرار الأسبوع ----------
def decision_headline(sar, tf, lang, kind="save") -> str:
    tw = timeframe_word(tf, lang)
    if kind == "protect":   # الرقم وارد مهدَّد (تركّز مصدر) — نحميه لا نوفّره
        if lang == "ar":
            return f"قرار واحد هذا الأسبوع يحمي ~{money(sar,'ar')} {tw} من وارِدك المعلّق على مصدر واحد."
        return f"One decision this week protects ~{money(sar,'en')} {tw} of inflows riding on a single source."
    if lang == "ar":
        return f"في قرار واحد لو أخذته هذا الأسبوع، يوفّر لك حوالي {money(sar,'ar')} {tw}."
    return f"One decision this week could save you about {money(sar,'en')} {tw}."


# ---------- التوصيات (أفعال قابلة للتنفيذ — لا تكرار للتشخيص) ----------
def rec_text(item, lang) -> str:
    k, d = item.get("key"), item.get("data", {})
    if k == "act_cut_burn":
        if lang == "ar":
            return (f"قلّص مصاريفك بما لا يقل عن {money(d['burn'],'ar')} شهرياً لوقف نزيف "
                    f"السيولة — ابدأ بأكبر بند غير أساسي هذا الأسبوع.")
        return (f"Cut expenses by at least {money(d['burn'],'en')} per month to stop the cash "
                f"bleed — start with your largest non-essential line this week.")
    if k == "act_diversify":
        if lang == "ar":
            return (f"اعتمادك على مصدر وارد واحد ({pct(d['share'])}) خطر. استهدف إضافة "
                    f"~{money(d['monthly_new'],'ar')} شهرياً من مصادر وارد جديدة خلال 90 يوماً "
                    f"لتنزيل الحصة تحت 50%.")
        return (f"Depending on one inflow source ({pct(d['share'])}) is risky. Aim to add "
                f"~{money(d['monthly_new'],'en')} per month from new inflow sources within 90 days "
                f"to bring the share under 50%.")
    if k == "act_trim":
        if lang == "ar":
            return (f"أرجِع مصروف «{d['category']}» إلى مستواه الطبيعي (~{money(d['target'],'ar')} شهرياً) "
                    f"— يوفّر ~{money(d['yearly'],'ar')} سنوياً.")
        return (f"Bring «{d['category']}» back to its normal level (~{money(d['target'],'en')}/month) "
                f"— saves ~{money(d['yearly'],'en')} per year.")
    if k == "act_cushion":
        if lang == "ar":
            return (f"وسادتك رقيقة (تتحمّل {pct(d['drop_pct'])} فقط). ارفع الهامش أو خفّض المصاريف "
                    f"الثابتة حتى تتحمّل انخفاضاً أكبر في المبيعات دون خسارة.")
        return (f"Your cushion is thin ({pct(d['drop_pct'])} only). Raise your margin or cut fixed "
                f"costs so you can absorb a bigger sales drop without loss.")
    if k == "act_review_costs":
        if lang == "ar":
            return ("راجع بنود المصاريف المتغيّرة وحدّد أي بند نما أسرع من دخلك — هامشك يتآكل، "
                    "والسبب مصروف يكبر بصمت.")
        return ("Review your variable costs and find which line grew faster than revenue — your "
                "margin is eroding because a cost is quietly climbing.")
    if k == "act_review_payroll":
        if lang == "ar":
            return (f"رواتبك ({pct(d['ratio'])} من الدخل، ~{money(d['monthly'],'ar')} شهرياً) عبء ثقيل. "
                    f"راجع الإنتاجية لكل موظف قبل أي توظيف جديد، ووازن النمو مع الطاقة الحالية.")
        return (f"Payroll ({pct(d['ratio'])} of revenue, ~{money(d['monthly'],'en')}/month) is heavy. "
                f"Review output per employee before any new hire, and match growth to current capacity.")
    if k == "act_review_recurring":
        if lang == "ar":
            return (f"لديك التزامات متكررة تُسحب تلقائياً بـ~{money(d['yearly'],'ar')} سنوياً "
                    f"({d['count']} جهة). راجعها وألغِ ما لا تستخدمه فعلاً — توفير صامت مباشر.")
        return (f"You have recurring auto-charges of ~{money(d['yearly'],'en')} per year "
                f"({d['count']} vendors). Review them and cancel what you don't truly use — instant silent savings.")
    return finding_text(item, lang)


# ---------- جُمل التقرير (لغة تدفق نقدي صادقة — ليست ربحاً محاسبياً) ----------
def summary_sentence(a, lang) -> str:
    inc, exp, net = a.total_income, a.total_expense, a.net_profit
    if lang == "ar":
        kind = "فائض نقدي" if net >= 0 else "عجز نقدي"
        return (f"خلال الفترة، دخل إلى حسابك {money(inc,'ar')} وخرج منه {money(exp,'ar')}، "
                f"أي صافي {kind} قدره {money(net,'ar')}. "
                f"(هذا تدفق نقدي من كشف البنك — وليس صافي ربح؛ الربح الفعلي يحتاج فواتيرك ومصاريفك المستحقة.)")
    kind = "net cash surplus" if net >= 0 else "net cash deficit"
    return (f"Over the period, {money(inc,'en')} came into your account and {money(exp,'en')} went out — "
            f"a {kind} of {money(net,'en')}. "
            f"(This is cash flow from your bank statement — not net profit; true profit needs your invoices and accruals.)")


def runway_sentence(r, lang) -> str:
    if lang == "ar":
        return (f"نقدك ينخفض حوالي {money(r['burn'],'ar')} شهرياً. برصيدك الحالي "
                f"({money(r['cash'],'ar')})، المتوقع أن يصل النقد لحد الخطر خلال "
                f"~{r['days']:.0f} يوم إذا استمر الاتجاه على ما هو عليه.")
    return (f"Your cash is falling about {money(r['burn'],'en')} per month. At your current balance "
            f"({money(r['cash'],'en')}), you're on track to hit a danger point in "
            f"~{r['days']:.0f} days if the trend continues.")


def resilience_sentence(a, lang) -> str:
    """وسادة التدفق: كم يتحمّل انخفاض الوارد قبل أن يصير التدفق سالباً."""
    dp = a.breakeven_drop_pct
    if lang == "ar":
        strong = "وسادة قوية" if dp >= 0.30 else "وسادة متوسطة" if dp >= 0.20 else "وسادة رقيقة — انتبه"
        return (f"وسادة التدفق: يتحمّل الوارد إلى حسابك انخفاضاً حتى {pct(dp)} قبل أن يصبح تدفقك النقدي سالباً "
                f"({strong}).")
    strong = "strong" if dp >= 0.30 else "moderate" if dp >= 0.20 else "thin — watch out"
    return (f"Cash cushion: your inflows can drop up to {pct(dp)} before your cash flow turns negative "
            f"({strong}).")


def buffer_sentence(a, lang) -> str:
    """شهور تغطية النقد لو توقّف الوارد تماماً."""
    b = a.buffer_months
    if lang == "ar":
        return (f"برصيدك الحالي ({money(a.cash,'ar')}) تغطّي ~{b:.1f} شهر من مدفوعاتك "
                f"حتى لو توقّف الوارد تماماً.")
    return (f"Your current balance ({money(a.cash,'en')}) covers ~{b:.1f} months of "
            f"outflows even if all inflows stopped.")


def period_label(first_ym, last_ym, lang) -> str:
    if first_ym == last_ym:
        return first_ym
    return f"{first_ym} {'إلى' if lang=='ar' else 'to'} {last_ym}"


# ---------- الأرقام الأبطال ----------
def safety_label(band, lang) -> str:
    m = {"good": ("جيد", "Good"), "medium": ("متوسط", "Fair"),
         "high_risk": ("خطر مرتفع", "High risk")}
    return m.get(band, ("", ""))[0 if lang == "ar" else 1]


def survival_sentence(days, lang) -> str:
    if lang == "ar":
        return f"شركتك تقدر تستمر ~{days:.0f} يوم بهذا المعدل من الإنفاق."
    return f"Your business can keep running ~{days:.0f} days at this spending rate."


def savings_sentence(amount, lang) -> str:
    if lang == "ar":
        return f"تنفيذ التوصيات يوفّر لك حوالي {money(amount,'ar')} سنوياً."
    return f"Acting on the recommendations saves you about {money(amount,'en')} per year."


def salary_sentence(a, lang) -> str:
    """ملخص الرواتب المستخرج من الكشف — يظهر دائماً حين توجد رواتب."""
    if lang == "ar":
        return (f"رواتبك ~{money(a.salary_monthly,'ar')} شهرياً لـ{a.salary_count} مستفيد، "
                f"أي {pct(a.salary_ratio)} من الوارد إلى حسابك.")
    return (f"Payroll is ~{money(a.salary_monthly,'en')}/month for {a.salary_count} recipients — "
            f"{pct(a.salary_ratio)} of your inflows.")


def recurring_sentence(a, lang) -> str:
    """ملخص الالتزامات المتكررة الصامتة."""
    if lang == "ar":
        return (f"رصدنا {len(a.recurring)} التزاماً متكرراً يُسحب تلقائياً بإجمالي "
                f"~{money(a.recurring_yearly,'ar')} سنوياً — راجعها فقد يكون فيها ما لا تستخدمه.")
    return (f"We found {len(a.recurring)} recurring auto-charges totaling "
            f"~{money(a.recurring_yearly,'en')} per year — review them for anything you no longer use.")


# ---------- نصوص التقرير الثابتة ----------
REPORT = {
    "ar": {
        "brand": "المدير المالي",
        "report_of": "تقرير", "period": "الفترة",
        "decision_kicker": "قرار هذا الأسبوع",
        "flip": "التقرير الكامل في الصفحات التالية",
        "overview": "الوضع النقدي", "healthy": "تدفق نقدي موجب", "caution": "مستقر — مع تحفّظات",
        "risk": "التدفق النقدي يحتاج تدخّلاً",
        "cash_warn": "تحذير سيولة",
        "survival": "ساعة بقاء الشركة", "savings": "التوفير الممكن", "safety": "مؤشر الأمان النقدي",
        "days": "يوم", "of100": "من 100",
        "earn": "من أين يدخل النقد", "bleed": "إلى أين يخرج النقد",
        "payroll": "قراءة الرواتب", "recurring": "التزامات متكررة صامتة",
        "emp": "موظف", "per_month": "شهرياً", "per_year": "سنوياً", "of_income": "من الوارد",
        "risks": "المخاطر المخفية", "todo": "ماذا تفعل الآن",
        "footer": "تحليل تدفق نقدي مبني على كشف حسابك البنكي — يكشف حركة نقدك ومخاطرها، وليس صافي "
                  "الربح المحاسبي (الذي يحتاج فواتيرك ومصاريفك المستحقة). أداة استرشادية لا تغني عن "
                  "مراجعة محاسب مختص. — المدير المالي",
    },
    "en": {
        "brand": "The Financial Director",
        "report_of": "Report ·", "period": "Period",
        "decision_kicker": "This week's decision",
        "flip": "The full report is on the following pages",
        "overview": "Cash position", "healthy": "Positive cash flow", "caution": "Stable — with caveats",
        "risk": "Cash flow needs action",
        "cash_warn": "Cash warning",
        "survival": "Business survival clock", "savings": "Possible savings", "safety": "Cash safety score",
        "days": "days", "of100": "of 100",
        "earn": "Where cash comes in", "bleed": "Where cash goes out",
        "payroll": "Payroll read", "recurring": "Silent recurring charges",
        "emp": "staff", "per_month": "per month", "per_year": "per year", "of_income": "of inflows",
        "risks": "Hidden risks", "todo": "What to do now",
        "footer": "A cash-flow analysis based on your bank statement — it surfaces how your cash moves "
                  "and its risks, not accounting net profit (which needs your invoices and accruals). "
                  "A guidance tool, not a substitute for a qualified accountant. — The Financial Director",
    },
}


# ---------- نصوص الواجهة (الموقع) ----------
def ui(lang):
    lang = norm_lang(lang)
    ar = {
        "dir": "rtl", "lang": "ar", "other": "en", "other_name": "English",
        "brand": "المدير المالي",
        "meta_title": "المدير المالي — حوّل أرقام شركتك إلى قرار مالي واضح",
        "meta_desc": "ارفع كشف حساب شركتك واحصل خلال دقائق على تقرير عربي يكشف أين تكسب، "
                     "أين تنزف، ومتى تنتهي سيولتك — بأرقام دقيقة وتوصيات مسعّرة بالريال.",
        "meta_kw": "تحليل مالي, مدير مالي, تقرير مالي, تدفق نقدي, شركات صغيرة, السعودية, تحليل كشف حساب",
        "eyebrow": "مديرك المالي الذكي — بالعربي",
        "tagline": "حوّل أرقام شركتك إلى قرار — لا مجرد تقرير.",
        "sub": "ارفع كشف حسابك، ويكشف لك خلال دقائق: أين تكسب، أين تنزف، ومتى تنتهي سيولتك — "
               "بتوصيات مسعّرة بالريال. أرقام دقيقة، لا تخمين.",
        "upload": "ارفع ملف العمليات",
        "upload_hint": "اسحب الملف هنا أو اضغط للاختيار",
        "formats": "Excel · CSV · PDF · Word · نص",
        "formats_note": "قريباً: صور كشوف الحسابات",
        "company": "اسم الشركة",
        "company_ph": "مثال: مؤسسة الإتقان",
        "cash": "الرصيد البنكي الحالي (ريال)",
        "cash_hint": "اختياري — يفعّل تنبؤ السيولة",
        "cash_ph": "مثال: 120000",
        "btn": "اكتشف أين تنزف أموالك",
        "steps": "⏳ نقرأ كشفك…|🔎 نصنّف العمليات…|📊 نحسب المخاطر والسيولة…|📝 نجهّز قرارك… (لحظات)",
        "preview_title": "تقريرك يكشف لك:",
        "p1": "قرار هذا الأسبوع — مسعّراً بالريال",
        "p2": "أعلى 5 مواطن تهدر فيها فلوسك",
        "p3": "هل تعتمد على عميل واحد بخطورة؟",
        "p4": "توقّع السيولة: كم يوم تكفيك؟",
        "p5": "مصاريف تنمو بصمت وتأكل صافي تدفقك",
        "p6": "مؤشر أمان لشركتك من 100",
        "p7": "توصيات تنفيذية + إجمالي التوفير الممكن",
        "sec_title": "أرقامك بأمان",
        "sec_line": "يُقرأ ملفك برمجياً ويُحذف فوراً بعد توليد التقرير. لا نخزّنه، ولا نبيعه، ولا نشاركه.",
        "trust1": "أرقامك تبقى عندك", "trust1d": "لا نبيع بياناتك ولا نشاركها.",
        "trust2": "نتيجة خلال دقيقة", "trust2d": "تحليل فوري وتقرير جاهز للتحميل.",
        "trust3": "دقة مضمونة", "trust3d": "كل حساب بالكود، لا تخمين.",
        "feats_t": "ماذا يكشف لك المدير المالي؟",
        "feats_sub": "ستّ قراءات يستخرجها من كشف حسابك — لا يعطيك أحدها نظامك المحاسبي.",
        "f1": "قرار الأسبوع", "f1d": "أهم خطوة مالية هذا الأسبوع، مسعّرة بالريال — تنفّذها فوراً.",
        "f2": "ساعة البقاء", "f2d": "كم يوماً تكفيك سيولتك بمعدل إنفاقك الحالي، قبل أن تصل لحد الرواتب.",
        "f3": "كاشف النزيف", "f3d": "أين تتسرّب أموالك بالضبط — أعلى بنود المصاريف ومَن يستنزفك.",
        "f4": "قراءة الرواتب", "f4d": "إجمالي رواتبك ونسبتها من الوارد — وهل هي عبء يهدّد سيولتك.",
        "f5": "الالتزامات الصامتة", "f5d": "اشتراكات وخدمات تُسحب تلقائياً كل شهر وقد نسيتها — نرصدها لك.",
        "f6": "مؤشر الأمان النقدي", "f6d": "درجة أمان تدفقك من 100، ووسادة الأمان: كم يتحمّل الوارد قبل أن يصير التدفق سالباً.",
        "why_t": "لماذا المدير المالي؟",
        "w1": "قرار لا مجرد أرقام", "w1d": "نبدأ بأهم قرار هذا الأسبوع مسعّراً بالريال — لا صفحات أرقام.",
        "w2": "دقة بالكود لا تخمين", "w2d": "كل رقم محسوب برمجياً؛ الذكاء الاصطناعي يشرح فقط، لا يخمّن أرقامك.",
        "w3": "عربي وسعودي أصيل", "w3d": "يفهم كشوف بنوكك، الزكاة، وسياقك المحلي — لا أداة أجنبية مترجمة.",
        "how_t": "كيف يعمل؟",
        "s1": "ارفع كشف حسابك", "s1d": "Excel أو PDF أو Word — أي صيغة فيها عملياتك.",
        "s2": "نحلّل حركة نقدك", "s2d": "محرك يحسب تدفقك النقدي والمخاطر والاتجاهات في ثوانٍ.",
        "s3": "احصل على قرارك", "s3d": "تقرير واضح + توصيات تنفّذها هذا الأسبوع.",
        "footer_tag": "المدير المالي — تحليل تدفق نقدي وكشف مخاطر للشركات الصغيرة.",
        "footer_disc": "تحليل تدفق نقدي من كشف البنك، وليس صافي ربح محاسبي. أداة استرشادية لا تغني عن محاسب مختص. "
                       "الحسابات النقدية دقيقة؛ التقديرات المستقبلية افتراضية تعتمد على استمرار الاتجاه.",
        "result": "تقريرك جاهز", "decision": "قرار هذا الأسبوع",
        "download": "تحميل التقرير الكامل (PDF)", "again": "تحليل ملف آخر",
        "income": "الوارد", "expenses": "الصادر", "net": "صافي التدفق", "margin": "نسبة الصافي",
        "safety": "مؤشر الأمان النقدي", "survival": "أيام بقاء السيولة", "savings": "توفير ممكن سنوياً",
        "healthy": "تدفق نقدي موجب", "caution": "مستقر — مع تحفّظات", "risk": "التدفق يحتاج تدخّلاً",
        "hidden": "المخاطر المخفية", "todo_t": "ماذا تفعل الآن", "payroll_t": "قراءة الرواتب",
        "recurring_t": "الالتزامات الصامتة", "summary_t": "ملخص الوضع النقدي",
        "cashflow_note": "هذه أرقام تدفق نقدي من كشف البنك — وليست صافي ربح محاسبي.",
        "err_generic": "تعذّرت معالجة الملف. تأكد أنه يحتوي جدول عمليات واضح وحاول مرة أخرى.",
        "err_nofile": "اختر ملفاً أولاً.",
        "err_toobig": "الملف كبير جداً. الحد الأقصى 25 ميجابايت.",
        "err_badformat": "صيغة غير مدعومة. استخدم Excel أو CSV أو PDF أو Word أو نص.",
    }
    en = {
        "dir": "ltr", "lang": "en", "other": "ar", "other_name": "العربية",
        "brand": "The Financial Director",
        "meta_title": "The Financial Director — Turn your numbers into a clear financial decision",
        "meta_desc": "Upload your company's statement and get a report in minutes: where you earn, "
                     "where you bleed, and when your cash runs out — exact numbers, recommendations priced in SAR.",
        "meta_kw": "financial analysis, virtual CFO, cash flow, small business, Saudi Arabia, "
                   "bank statement analysis, financial report",
        "eyebrow": "Your AI financial director — Arabic-first",
        "tagline": "Turn your numbers into a decision — not just a report.",
        "sub": "Upload your statement and in minutes see where you earn, where you bleed, and when "
               "your cash runs out — with recommendations priced in SAR. Exact numbers, no guessing.",
        "upload": "Upload your transactions file",
        "upload_hint": "Drag your file here or click to choose",
        "formats": "Excel · CSV · PDF · Word · Text",
        "formats_note": "Coming soon: photos of statements",
        "company": "Company name",
        "company_ph": "e.g. Al-Itqan Co.",
        "cash": "Current bank balance (SAR)",
        "cash_hint": "Optional — enables the cash forecast",
        "cash_ph": "e.g. 120000",
        "btn": "Find out where you're bleeding money",
        "steps": "⏳ Reading your statement…|🔎 Classifying transactions…|📊 Computing risks & cash…|📝 Preparing your decision… (a moment)",
        "preview_title": "Your report reveals:",
        "p1": "This week's decision — priced in SAR",
        "p2": "Your top 5 money leaks",
        "p3": "Are you dangerously dependent on one client?",
        "p4": "Cash forecast: how many days you have left",
        "p5": "Costs quietly growing and eating your profit",
        "p6": "A safety score for your business out of 100",
        "p7": "Actionable recommendations + total possible savings",
        "sec_title": "Your data is safe",
        "sec_line": "Your file is read programmatically and deleted immediately after the report is generated. We never store, sell, or share it.",
        "trust1": "Your data stays yours", "trust1d": "We never sell or share it.",
        "trust2": "Results in a minute", "trust2d": "Instant analysis, report ready to download.",
        "trust3": "Guaranteed accuracy", "trust3d": "Every calculation in code, no guessing.",
        "feats_t": "What does The Financial Director reveal?",
        "feats_sub": "Six reads pulled from your statement — none of which your accounting system gives you.",
        "f1": "Decision of the Week", "f1d": "The single most important money move this week, priced in SAR — act on it now.",
        "f2": "Survival Clock", "f2d": "How many days your cash lasts at today's spending — before you hit payroll.",
        "f3": "Bleed Detector", "f3d": "Exactly where your money leaks — top expense lines and who drains you most.",
        "f4": "Payroll Read", "f4d": "Your total payroll and its share of inflows — and whether it threatens your cash.",
        "f5": "Silent Commitments", "f5d": "Subscriptions and services auto-charging every month that you may have forgotten.",
        "f6": "Cash Safety Score", "f6d": "Your cash-flow safety out of 100, plus the cushion: how far inflows can fall before cash flow turns negative.",
        "why_t": "Why The Financial Director?",
        "w1": "A decision, not numbers", "w1d": "We lead with this week's most important decision, priced in SAR — not pages of numbers.",
        "w2": "Exact by code, no guessing", "w2d": "Every figure computed in code; AI only explains — it never guesses your numbers.",
        "w3": "Truly Arabic & Saudi", "w3d": "It understands your bank statements, zakat, and local context — not a translated foreign tool.",
        "how_t": "How it works",
        "s1": "Upload your statement", "s1d": "Excel, PDF or Word — any format with your transactions.",
        "s2": "We analyze your cash movement", "s2d": "An engine computes your cash flow, risks and trends in seconds.",
        "s3": "Get your decision", "s3d": "A clear report plus recommendations to act on this week.",
        "footer_tag": "The Financial Director — cash-flow analysis & risk detection for small business.",
        "footer_disc": "A cash-flow analysis from your bank statement, not accounting net profit. A guidance tool, not a substitute "
                       "for a qualified accountant. Cash figures are exact; forward estimates assume the current trend continues.",
        "result": "Your report is ready", "decision": "This week's decision",
        "download": "Download full report (PDF)", "again": "Analyze another file",
        "income": "Cash in", "expenses": "Cash out", "net": "Net cash flow", "margin": "Net ratio",
        "safety": "Cash safety score", "survival": "Cash survival days", "savings": "Possible yearly savings",
        "healthy": "Positive cash flow", "caution": "Stable — with caveats", "risk": "Cash flow needs action",
        "hidden": "Hidden risks", "todo_t": "What to do now", "payroll_t": "Payroll read",
        "recurring_t": "Silent commitments", "summary_t": "Cash situation summary",
        "cashflow_note": "These are cash-flow figures from your bank statement — not accounting net profit.",
        "err_generic": "We couldn't process the file. Make sure it has a clear transactions table and try again.",
        "err_nofile": "Please choose a file first.",
        "err_toobig": "File is too large. Maximum size is 25 MB.",
        "err_badformat": "Unsupported format. Use Excel, CSV, PDF, Word or text.",
    }
    return ar if lang == "ar" else en
