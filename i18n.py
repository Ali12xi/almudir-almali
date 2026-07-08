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
        return "تآكل الأرباح" if lang == "ar" else "Margin erosion"
    if k == "sales_up_profit_down":
        return "مبيعات تزيد / أرباح تنقص" if lang == "ar" else "Sales up / profit down"
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
            return (f"أكبر عميل ({d['name']}) يمثّل {pct(d['share'])} من إيراداتك. "
                    f"لو توقّف، تخسر حوالي {money(d['monthly'], 'ar')} شهرياً.")
        return (f"Your largest client ({d['name']}) makes up {pct(d['share'])} of revenue. "
                f"If they leave, you lose about {money(d['monthly'], 'en')} per month.")
    if k == "margin_erosion":
        if lang == "ar":
            return (f"هامش ربحك نزل من {pct(d['first'])} إلى {pct(d['last'])} خلال الفترة "
                    f"(انخفاض {d['drop_pts']:.0f} نقطة). أرباحك تتآكل رغم استقرار المبيعات.")
        return (f"Your profit margin fell from {pct(d['first'])} to {pct(d['last'])} over the period "
                f"(a {d['drop_pts']:.0f}-point drop). Profits are eroding even as sales hold steady.")
    if k == "sales_up_profit_down":
        if lang == "ar":
            return "مبيعاتك ترتفع لكن صافي ربحك ينخفض — معناه مصاريفك تكبر أسرع من دخلك."
        return "Your sales are rising but net profit is falling — expenses are growing faster than revenue."
    if k == "expense_spike":
        if lang == "ar":
            return (f"مصروف «{d['category']}» قفز من ~{money(d['early'],'ar')} إلى ~{money(d['late'],'ar')} شهرياً. "
                    f"لو رجع لمستواه الطبيعي، توفّر حوالي {money(d['excess_year'],'ar')} سنوياً.")
        return (f"Your «{d['category']}» expense jumped from ~{money(d['early'],'en')} to ~{money(d['late'],'en')} per month. "
                f"Bringing it back to normal saves about {money(d['excess_year'],'en')} per year.")
    if k == "thin_cushion":
        if lang == "ar":
            return (f"تتحمّل انخفاض مبيعاتك حتى {pct(d['drop_pct'])} فقط قبل أن تبدأ الخسارة — "
                    f"وسادة ضيّقة. أي تراجع مفاجئ في السوق أو خسارة عميل يدخلك منطقة الخطر بسرعة.")
        return (f"Your sales can fall only {pct(d['drop_pct'])} before you start losing money — "
                f"a thin cushion. Any sudden market dip or lost client pushes you into the red fast.")
    if k == "high_payroll":
        if lang == "ar":
            return (f"رواتبك تلتهم {pct(d['ratio'])} من دخلك (~{money(d['monthly'],'ar')} شهرياً "
                    f"لـ{d['count']} موظف). نسبة مرتفعة تجعل أي شهر ضعيف يضغط على سيولتك مباشرة.")
        return (f"Payroll eats {pct(d['ratio'])} of your revenue (~{money(d['monthly'],'en')}/month "
                f"for {d['count']} staff). A high ratio means any slow month squeezes your cash immediately.")
    return ""


# ---------- قرار الأسبوع ----------
def decision_headline(sar, tf, lang, kind="save") -> str:
    tw = timeframe_word(tf, lang)
    if kind == "protect":   # الرقم دخل مهدَّد (تركّز عملاء) — نحميه لا نوفّره
        if lang == "ar":
            return f"قرار واحد هذا الأسبوع يحمي ~{money(sar,'ar')} {tw} من دخلك المعلّق على عميل واحد."
        return f"One decision this week protects ~{money(sar,'en')} {tw} of revenue riding on a single client."
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
            return (f"اعتمادك على عميل واحد ({pct(d['share'])}) خطر. استهدف إضافة "
                    f"~{money(d['monthly_new'],'ar')} شهرياً من دخل عملاء جدد خلال 90 يوماً "
                    f"لتنزيل الحصة تحت 50%.")
        return (f"Depending on one client ({pct(d['share'])}) is risky. Aim to add "
                f"~{money(d['monthly_new'],'en')} per month in new-client revenue within 90 days "
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


# ---------- جُمل التقرير ----------
def summary_sentence(a, lang) -> str:
    inc, exp, net, m = a.total_income, a.total_expense, a.net_profit, a.avg_margin
    if lang == "ar":
        kind = "ربح" if net >= 0 else "خسارة"
        return (f"خلال الفترة، إجمالي دخلك {money(inc,'ar')} ومصاريفك {money(exp,'ar')}، "
                f"أي صافي {kind} {money(net,'ar')} بهامش {pct(m)}.")
    kind = "profit" if net >= 0 else "loss"
    return (f"Over the period, total income was {money(inc,'en')} and expenses {money(exp,'en')}, "
            f"a net {kind} of {money(net,'en')} at a {pct(m)} margin.")


def runway_sentence(r, lang) -> str:
    if lang == "ar":
        return (f"سيولتك تنخفض حوالي {money(r['burn'],'ar')} شهرياً. برصيدك الحالي "
                f"({money(r['cash'],'ar')})، المتوقع أن تصل السيولة لحد الخطر خلال "
                f"~{r['days']:.0f} يوم إذا استمر الوضع على ما هو عليه.")
    return (f"Your cash is falling about {money(r['burn'],'en')} per month. At your current balance "
            f"({money(r['cash'],'en')}), you're on track to hit a danger point in "
            f"~{r['days']:.0f} days if the trend continues.")


def resilience_sentence(a, lang) -> str:
    """وسادة الأمان: كم يتحمّل انخفاض المبيعات قبل الخسارة — تُعرض دائماً (إيجاباً أو تحذيراً)."""
    dp = a.breakeven_drop_pct
    if lang == "ar":
        strong = "وسادة قوية" if dp >= 0.30 else "وسادة متوسطة" if dp >= 0.20 else "وسادة رقيقة — انتبه"
        return f"وسادة الأمان: تتحمّل انخفاض مبيعاتك حتى {pct(dp)} قبل أن تبدأ الخسارة ({strong})."
    strong = "strong" if dp >= 0.30 else "moderate" if dp >= 0.20 else "thin — watch out"
    return f"Safety cushion: sales can drop up to {pct(dp)} before you start losing money ({strong})."


def buffer_sentence(a, lang) -> str:
    """شهور تغطية السيولة لو توقّف الدخل تماماً."""
    b = a.buffer_months
    if lang == "ar":
        return (f"برصيدك الحالي ({money(a.cash,'ar')}) تغطّي ~{b:.1f} شهر من مصاريفك "
                f"حتى لو توقّف دخلك تماماً.")
    return (f"Your current balance ({money(a.cash,'en')}) covers ~{b:.1f} months of "
            f"expenses even if your income stopped completely.")


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
        return (f"رواتبك ~{money(a.salary_monthly,'ar')} شهرياً لـ{a.salary_count} موظف، "
                f"أي {pct(a.salary_ratio)} من دخلك.")
    return (f"Payroll is ~{money(a.salary_monthly,'en')}/month for {a.salary_count} staff — "
            f"{pct(a.salary_ratio)} of your revenue.")


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
        "flip": "اقلب الصفحة للتقرير الكامل ←",
        "overview": "الوضع العام", "healthy": "وضع صحي", "caution": "مستقر — مع تحفّظات",
        "risk": "يحتاج تدخّل عاجل",
        "cash_warn": "تحذير سيولة",
        "survival": "ساعة بقاء الشركة", "savings": "التوفير الممكن", "safety": "مؤشر الأمان",
        "days": "يوم", "of100": "من 100",
        "earn": "من أين تكسب", "bleed": "أين تنزف",
        "payroll": "قراءة الرواتب", "recurring": "التزامات متكررة صامتة",
        "emp": "موظف", "per_month": "شهرياً", "per_year": "سنوياً", "of_income": "من الدخل",
        "risks": "المخاطر المخفية", "todo": "ماذا تفعل الآن",
        "footer": "هذا التقرير مبني على الأرقام التي رفعتها. الحسابات دقيقة؛ "
                  "التقديرات المستقبلية افتراضية تعتمد على استمرار الاتجاه الحالي. — المدير المالي",
    },
    "en": {
        "brand": "The Financial Director",
        "report_of": "Report ·", "period": "Period",
        "decision_kicker": "This week's decision",
        "flip": "→ Turn the page for the full report",
        "overview": "Overview", "healthy": "Healthy", "caution": "Stable — with caveats",
        "risk": "Needs urgent action",
        "cash_warn": "Cash warning",
        "survival": "Business survival clock", "savings": "Possible savings", "safety": "Safety score",
        "days": "days", "of100": "of 100",
        "earn": "Where you earn", "bleed": "Where you bleed",
        "payroll": "Payroll read", "recurring": "Silent recurring charges",
        "emp": "staff", "per_month": "per month", "per_year": "per year", "of_income": "of revenue",
        "risks": "Hidden risks", "todo": "What to do now",
        "footer": "This report is based on the numbers you uploaded. Calculations are exact; "
                  "forward estimates are assumptions based on the current trend. — The Financial Director",
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
        "p5": "مصاريف تنمو بصمت وتأكل أرباحك",
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
        "f4": "قراءة الرواتب", "f4d": "إجمالي رواتبك ونسبتها من دخلك — وهل هي عبء يهدّد سيولتك.",
        "f5": "الالتزامات الصامتة", "f5d": "اشتراكات وخدمات تُسحب تلقائياً كل شهر وقد نسيتها — نرصدها لك.",
        "f6": "مؤشر الأمان", "f6d": "درجة صحة شركتك من 100، ووسادة الأمان: كم تتحمّل قبل الخسارة.",
        "why_t": "لماذا المدير المالي؟",
        "w1": "قرار لا مجرد أرقام", "w1d": "نبدأ بأهم قرار هذا الأسبوع مسعّراً بالريال — لا صفحات أرقام.",
        "w2": "دقة بالكود لا تخمين", "w2d": "كل رقم محسوب برمجياً؛ الذكاء الاصطناعي يشرح فقط، لا يخمّن أرقامك.",
        "w3": "عربي وسعودي أصيل", "w3d": "يفهم كشوف بنوكك، الزكاة، وسياقك المحلي — لا أداة أجنبية مترجمة.",
        "how_t": "كيف يعمل؟",
        "s1": "ارفع كشف حسابك", "s1d": "Excel أو PDF أو Word — أي صيغة فيها عملياتك.",
        "s2": "نحلّل أرقامك", "s2d": "محرك يحسب الأرباح والمخاطر والاتجاهات في ثوانٍ.",
        "s3": "احصل على قرارك", "s3d": "تقرير واضح + توصيات تنفّذها هذا الأسبوع.",
        "footer_tag": "المدير المالي — ذكاء مالي للشركات الصغيرة.",
        "footer_disc": "الحسابات دقيقة؛ التقديرات المستقبلية افتراضية تعتمد على استمرار الاتجاه.",
        "result": "تقريرك جاهز", "decision": "قرار هذا الأسبوع",
        "download": "تحميل التقرير الكامل (PDF)", "again": "تحليل ملف آخر",
        "income": "الدخل", "expenses": "المصاريف", "net": "الصافي", "margin": "الهامش",
        "safety": "مؤشر الأمان", "survival": "أيام بقاء السيولة", "savings": "توفير ممكن سنوياً",
        "healthy": "وضع صحي", "caution": "مستقر — مع تحفّظات", "risk": "يحتاج تدخّل عاجل",
        "hidden": "المخاطر المخفية", "todo_t": "ماذا تفعل الآن", "payroll_t": "قراءة الرواتب",
        "recurring_t": "الالتزامات الصامتة", "summary_t": "ملخص الوضع",
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
        "f4": "Payroll Read", "f4d": "Your total payroll and its share of revenue — and whether it threatens your cash.",
        "f5": "Silent Commitments", "f5d": "Subscriptions and services auto-charging every month that you may have forgotten.",
        "f6": "Safety Score", "f6d": "Your business health out of 100, plus the cushion: how much you can absorb before loss.",
        "why_t": "Why The Financial Director?",
        "w1": "A decision, not numbers", "w1d": "We lead with this week's most important decision, priced in SAR — not pages of numbers.",
        "w2": "Exact by code, no guessing", "w2d": "Every figure computed in code; AI only explains — it never guesses your numbers.",
        "w3": "Truly Arabic & Saudi", "w3d": "It understands your bank statements, zakat, and local context — not a translated foreign tool.",
        "how_t": "How it works",
        "s1": "Upload your statement", "s1d": "Excel, PDF or Word — any format with your transactions.",
        "s2": "We analyze your numbers", "s2d": "An engine computes profits, risks and trends in seconds.",
        "s3": "Get your decision", "s3d": "A clear report plus recommendations to act on this week.",
        "footer_tag": "The Financial Director — financial intelligence for small business.",
        "footer_disc": "Calculations are exact; forward estimates assume the current trend continues.",
        "result": "Your report is ready", "decision": "This week's decision",
        "download": "Download full report (PDF)", "again": "Analyze another file",
        "income": "Income", "expenses": "Expenses", "net": "Net", "margin": "Margin",
        "safety": "Safety score", "survival": "Cash survival days", "savings": "Possible yearly savings",
        "healthy": "Healthy", "caution": "Stable — with caveats", "risk": "Needs urgent action",
        "hidden": "Hidden risks", "todo_t": "What to do now", "payroll_t": "Payroll read",
        "recurring_t": "Silent commitments", "summary_t": "Situation summary",
        "err_generic": "We couldn't process the file. Make sure it has a clear transactions table and try again.",
        "err_nofile": "Please choose a file first.",
        "err_toobig": "File is too large. Maximum size is 25 MB.",
        "err_badformat": "Unsupported format. Use Excel, CSV, PDF, Word or text.",
    }
    return ar if lang == "ar" else en
