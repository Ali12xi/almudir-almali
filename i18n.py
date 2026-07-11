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


# ---------- ترتيب المخاطر بالأولوية (طلب المستثمر: 🔴 عاجل / 🟠 متوسط / 🟢 مراقبة) ----------
def priority_badge(severity, lang) -> str:
    m = {"high": ("🔴 عاجل", "🔴 Urgent"),
         "medium": ("🟠 متوسط", "🟠 Moderate"),
         "low": ("🟢 مراقبة", "🟢 Watch")}
    return m.get(severity, m["medium"])[0 if lang == "ar" else 1]


def priority_word(severity, lang) -> str:
    """كلمة الأولوية بلا إيموجي — للتقرير PDF (خط Amiri لا يصيّر إيموجي ملوّناً)."""
    m = {"high": ("عاجل", "Urgent"),
         "medium": ("متوسط", "Moderate"),
         "low": ("مراقبة", "Watch")}
    return m.get(severity, m["medium"])[0 if lang == "ar" else 1]


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
    if k == "payroll_ratio":
        return "نسبة الرواتب من الدخل" if lang == "ar" else "Payroll-to-income ratio"
    if k == "hire_impact":
        return "أثر توظيف موظف جديد" if lang == "ar" else "Impact of a new hire"
    if k == "salary_concentration":
        return "تركّز الرواتب في موظف" if lang == "ar" else "Salary concentration"
    if k == "receivables_crisis":
        return "أزمة تحصيل (ذمم متراكمة)" if lang == "ar" else "Collection crisis (piling receivables)"
    if k == "large_asset_purchase":
        return "شراء أصل كبير في وقت حسّاس" if lang == "ar" else "Large asset purchase at a tight time"
    if k == "fixed_obligations":
        return "التزامات ثابتة تفوق نقدك الداخل" if lang == "ar" else "Fixed commitments exceed cash coming in"
    if k == "overdraft":
        return "سحب على المكشوف — الحساب دخل السالب" if lang == "ar" else "Overdraft — the account went negative"
    if k == "operating_bleed":
        return "نزيف تشغيلي متكرر" if lang == "ar" else "Recurring operating loss"
    if k == "unknown_inflows":
        return "وارد غير مُوضّح يحتاج توضيحك" if lang == "ar" else "Unexplained inflows need your input"
    if k == "marketing_spike":
        return "قفزة في التسويق — راجع الجدوى" if lang == "ar" else "Marketing jumped — review its return"
    if k == "duplicate_payment":
        return "دفعة مكررة محتملة — تحقّق" if lang == "ar" else "Possible duplicate payment — verify"
    if k == "escalating_payments":
        return "مدفوعات متصاعدة لجهة واحدة" if lang == "ar" else "Escalating payments to one party"
    if k == "client_vanished":
        return "عميل منتظم توقّف" if lang == "ar" else "A regular client went quiet"
    if k == "penalties":
        return "غرامات ومخالفات قابلة للتفادي" if lang == "ar" else "Avoidable fines & penalties"
    if k == "cash_buffer_risk":
        return "تعمل بلا وسادة نقدية" if lang == "ar" else "Operating with no cash cushion"
    if k == "recurring_payees":
        return "مدفوعات متكررة لأفراد وجهات — حدّدها" if lang == "ar" else "Recurring payments to people — clarify them"
    if k == "client_paying_partial":
        return "عميلك الأكبر بدأ يدفع جزئياً" if lang == "ar" else "Your top client started paying partially"
    return ""


# ---------- نص المخاطرة ----------
def finding_text(f, lang) -> str:
    k, d = f["key"], f["data"]
    if k == "customer_concentration":
        days = d.get("days_if_lost")
        if lang == "ar":
            s = (f"أكبر مصدر وارد ({d['name']}) يمثّل {pct(d['share'])} من الوارد إلى حسابك. "
                 f"لو توقّف، ينقص وارِدك حوالي {money(d['monthly'], 'ar')} شهرياً")
            return s + (f" — وسيولتك تكفي ~{days:.0f} يوم فقط بعد فقده." if days else ".")
        s = (f"Your largest inflow source ({d['name']}) makes up {pct(d['share'])} of money coming in. "
             f"If it stops, your inflows drop about {money(d['monthly'], 'en')} per month")
        return s + (f" — and your cash would last only ~{days:.0f} days after losing it." if days else ".")
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
    if k == "payroll_ratio":
        band = ("مرتفعة — خطر" if d['ratio'] >= 0.55 else "مرتفعة نسبياً" if d['ratio'] >= 0.40 else "ضمن المعقول")
        if lang == "ar":
            return (f"رواتبك {money(d['monthly'],'ar')} شهرياً لـ{d['count']} موظف = {pct(d['ratio'])} "
                    f"من دخلك الشهري ({money(d['income'],'ar')}). النسبة {band}. "
                    f"(المعتاد للشركات الصحية أقل من 30–40%.)")
        band_en = ("high — risky" if d['ratio'] >= 0.55 else "somewhat high" if d['ratio'] >= 0.40 else "reasonable")
        return (f"Payroll is {money(d['monthly'],'en')}/month for {d['count']} staff = {pct(d['ratio'])} "
                f"of your monthly income ({money(d['income'],'en')}). That's {band_en}. "
                f"(Healthy firms usually stay under 30–40%.)")
    if k == "hire_impact":
        if lang == "ar":
            s = (f"توظيف موظف جديد بمتوسط راتبك ({money(d['avg'],'ar')}) يرفع رواتبك إلى "
                 f"{money(d['new_total'],'ar')} شهرياً")
            if d.get('new_ratio'):
                s += f" — أي {pct(d['new_ratio'])} من دخلك"
            return s + "."
        s = (f"Hiring one more at your average salary ({money(d['avg'],'en')}) raises payroll to "
             f"{money(d['new_total'],'en')}/month")
        if d.get('new_ratio'):
            s += f" — {pct(d['new_ratio'])} of income"
        return s + "."
    if k == "salary_concentration":
        if lang == "ar":
            return (f"أعلى راتب ({d['name']}) يمثّل {pct(d['share'])} من إجمالي رواتبك "
                    f"({money(d['amount'],'ar')}). اعتماد كبير على شخص واحد.")
        return (f"Your highest salary ({d['name']}) is {pct(d['share'])} of total payroll "
                f"({money(d['amount'],'en')}). Heavy dependence on one person.")
    if k == "receivables_crisis":
        if lang == "ar":
            return (f"أصدرت فواتير بـ{money(d['invoiced'],'ar')} لكن حصّلت {money(d['collected'],'ar')} فقط "
                    f"({pct(d['rate'])}). الفرق {money(d['receivables'],'ar')} عالق كذمم عند عملائك — "
                    f"أرباحك على الورق جيدة، لكن نقدك الفعلي مضغوط. لاحق التحصيل قبل أن تخنقك السيولة.")
        return (f"You invoiced {money(d['invoiced'],'en')} but collected only {money(d['collected'],'en')} "
                f"({pct(d['rate'])}). The {money(d['receivables'],'en')} gap is stuck as receivables — "
                f"profit looks fine on paper, but real cash is tight. Chase collections before cash chokes you.")
    if k == "large_asset_purchase":
        if lang == "ar":
            mo = d.get("months_expense", 0)
            return (f"رصدنا شراء أصل بـ{money(d['amount'],'ar')} ({d['party']}) — يعادل ~{mo:.0f} أشهر من "
                    f"مصاريفك. شراء كبير لمرة في فترة فيها التزامات ثابتة؛ تأكد أنه لم يضغط سيولتك التشغيلية.")
        mo = d.get("months_expense", 0)
        return (f"We spotted a {money(d['amount'],'en')} asset purchase ({d['party']}) — ~{mo:.0f} months of "
                f"your expenses. A big one-off during fixed commitments; make sure it didn't strain operating cash.")
    if k == "fixed_obligations":
        comp = _fixed_components(d, lang)
        if lang == "ar":
            s = (f"التزاماتك النقدية الثابتة ~{money(d['fixed'],'ar')} شهرياً ({comp}) تُدفع نقداً "
                 f"مهما تأخّر التحصيل — بينما يدخل حسابك فعلياً ~{money(d['cash_in'],'ar')} شهرياً. "
                 f"أي أن التزاماتك الثابتة وحدها تعادل {pct(d['ratio'])} من نقدك الداخل.")
            if d['fixed'] > d['cash_in']:
                s += " الفرق يُغطّى من رصيدك كل شهر — ولو تراجع تحصيلك أكثر لن يصمد الرصيد طويلاً."
            return s
        s = (f"Your fixed cash commitments are ~{money(d['fixed'],'en')}/month ({comp}), paid in cash "
             f"regardless of collections — while only ~{money(d['cash_in'],'en')}/month actually comes in. "
             f"Fixed costs alone equal {pct(d['ratio'])} of your incoming cash.")
        if d['fixed'] > d['cash_in']:
            s += " The gap is covered from your balance every month — if collections slip further, it won't hold long."
        return s
    if k == "overdraft":
        if lang == "ar":
            return (f"رصيدك بدأ الفترة عند {money(d['opening'],'ar')} وانتهى عند {money(d['closing'],'ar')} "
                    f"(سالب)، وبلغ أدنى نقطة {money(d['min'],'ar')}. الحساب دخل السحب على المكشوف فعلاً — "
                    f"الرصيد بقي موجباً فترةً فقط بفضل التمويل، لا لأن النشاط رابح. هذه أخطر إشارة في الكشف.")
        return (f"Your balance started the period at {money(d['opening'],'en')} and ended at {money(d['closing'],'en')} "
                f"(negative), hitting a low of {money(d['min'],'en')}. The account actually went into overdraft — "
                f"it stayed positive for a while only thanks to financing, not because the business was profitable. "
                f"This is the most serious signal in the statement.")
    if k == "operating_bleed":
        if lang == "ar":
            return (f"تدفقك التشغيلي (وارد النشاط ناقص مصروفه) كان سالباً في {d['neg']} من {d['total']} أشهر. "
                    f"النشاط نفسه يخسر نقداً معظم السنة؛ ما ستره هو التمويل والتحويلات، وهي تنتهي.")
        return (f"Your operating cash flow (activity income minus its costs) was negative in {d['neg']} of {d['total']} months. "
                f"The business itself loses cash most of the year; financing and transfers masked it, and those run out.")
    if k == "unknown_inflows":
        if lang == "ar":
            return (f"رصدنا {d['count']} حركة وارِدة بإجمالي {money(d['total'],'ar')} بمراجع بنكية مبهمة بلا جهة واضحة. "
                    f"لم نصنّفها «مبيعات» تخميناً — وضّح مصدرها: إن كانت تمويلاً أو تحويلاً داخلياً فهي ليست إيراداً.")
        return (f"We found {d['count']} incoming transactions totaling {money(d['total'],'en')} with vague bank references and no clear source. "
                f"We did not guess them as «sales» — please clarify: if they're financing or internal transfers, they aren't revenue.")
    if k == "marketing_spike":
        if lang == "ar":
            return (f"مصروف «{d['category']}» ارتفع من ~{money(d['early'],'ar')} إلى ~{money(d['late'],'ar')} شهرياً. "
                    f"قد يكون استثماراً مجدياً أو إنفاقاً بلا عائد — راجع أثره على المبيعات قبل الاستمرار "
                    f"(لا نفترض أنه هدر، ولا نعدك بتوفير مضمون).")
        return (f"Your «{d['category']}» spend rose from ~{money(d['early'],'en')} to ~{money(d['late'],'en')}/month. "
                f"It may be a worthwhile investment or spend with no return — check its effect on sales before continuing "
                f"(we don't assume it's waste, nor promise guaranteed savings).")
    if k == "duplicate_payment":
        if lang == "ar":
            return (f"دفعتان متطابقتان لـ«{d['party']}» بمبلغ {money(d['amount'],'ar')} لكلٍّ منهما، "
                    f"بفارق {d['days']} أيام فقط ({d['date1']} و{d['date2']}). قد تكون فاتورة دُفعت مرتين — "
                    f"تحقّق منها؛ إن كانت مكررة فهذا مبلغ يمكن استرداده كاملاً.")
        return (f"Two identical payments to «{d['party']}» of {money(d['amount'],'en')} each, "
                f"just {d['days']} days apart ({d['date1']} and {d['date2']}). Possibly the same invoice paid twice — "
                f"verify it; if duplicated, the full amount is recoverable.")
    if k == "escalating_payments":
        if lang == "ar":
            return (f"مدفوعات لـ«{d['party']}» تتصاعد باطّراد: من {money(d['first'],'ar')} إلى "
                    f"{money(d['last'],'ar')} عبر {d['n']} دفعات (إجمالي {money(d['total'],'ar')}). "
                    f"نمط يستدعي المراجعة: من هذه الجهة؟ وما مقابل هذه المبالغ المتنامية؟")
        return (f"Payments to «{d['party']}» climb steadily: from {money(d['first'],'en')} to "
                f"{money(d['last'],'en')} across {d['n']} payments (total {money(d['total'],'en')}). "
                f"A pattern worth reviewing: who is this party, and what are these growing amounts for?")
    if k == "client_vanished":
        if lang == "ar":
            return (f"«{d['party']}» كان يدفع لك بانتظام (~{money(d['monthly'],'ar')} شهرياً لمدة "
                    f"{d['months_active']} أشهر) ثم توقّف تماماً منذ {d['last_seen']}. "
                    f"فقدت عميلاً؟ تواصل معه قبل أن يذهب دخله لمنافسك.")
        return (f"«{d['party']}» paid you regularly (~{money(d['monthly'],'en')}/month for "
                f"{d['months_active']} months) then stopped completely since {d['last_seen']}. "
                f"Lost a client? Reach out before that income goes to a competitor.")
    if k == "client_paying_partial":
        if lang == "ar":
            return (f"«{d['party']}» كان يدفع لك ~{money(d['usual_monthly'],'ar')} شهرياً، "
                    f"وفي آخر شهرين ظهرت منه {d['n_partials']} دفعات جزئية بإجمالي "
                    f"{money(d['partial_total'],'ar')} — عميلك الأكبر بدأ يماطل. "
                    f"تواصل معه اليوم واطلب جدولة المستحقات قبل أن يكبر المتأخر.")
        return (f"«{d['party']}» used to pay you ~{money(d['usual_monthly'],'en')}/month; "
                f"in the last two months, {d['n_partials']} partial payments appeared totaling "
                f"{money(d['partial_total'],'en')} — your top client is starting to stall. "
                f"Contact them today and schedule the outstanding amounts before they grow.")
    if k == "penalties":
        if lang == "ar":
            return (f"دفعت {money(d['total'],'ar')} غرامات ومخالفات ({d['count']} حركة: تأخير سداد/مخالفات). "
                    f"هذا مبلغ قابل للتفادي بالكامل — جدولة السداد قبل الاستحقاق توقفه من المصدر.")
        return (f"You paid {money(d['total'],'en')} in fines and penalties ({d['count']} items: late payments/violations). "
                f"This is fully avoidable — scheduling payments before due dates stops it at the source.")
    if k == "cash_buffer_risk":
        if lang == "ar":
            s = f"رصيدك لامس {d['min']:,.2f} ريال"
            if d.get("pct_5k") is not None:
                s += f"، وبقي تحت 5,000 ريال في {pct(d['pct_5k'])} من حركاتك"
            s += ". شركتك تعمل بلا وسادة نقدية — أي تأخر تحصيل ليوم واحد يعني ارتداد مدفوعات"
            if d.get("cover") is not None:
                s += f". وسيط رصيدك ({money(d['median'],'ar')}) يغطي ~{d['cover']:.0f} يوم من الصادر فقط"
            return s + "."
        s = f"Your balance touched SAR {d['min']:,.2f}"
        if d.get("pct_5k") is not None:
            s += f", and stayed below SAR 5,000 in {pct(d['pct_5k'])} of your transactions"
        s += ". You operate with no cash cushion — a single day's collection delay means bounced payments"
        if d.get("cover") is not None:
            s += f". Your median balance ({money(d['median'],'en')}) covers only ~{d['cover']:.0f} days of outflows"
        return s + "."
    if k == "recurring_payees":
        top = "، ".join(f"{n} ({c} دفعة)" for n, c in d.get("top", []))
        if lang == "ar":
            return (f"{money(d['total'],'ar')} ({pct(d['share'])} من مصروفاتك) تخرج بانتظام "
                    f"لـ{d['n']} جهة. أكبرها: {top}. "
                    f"هل هذه رواتب عمالة، أم موردون، أم شيء آخر؟ حدّدها لنحسبها بدقة.")
        top_en = ", ".join(f"{n} ({c} payments)" for n, c in d.get("top", []))
        return (f"{money(d['total'],'en')} ({pct(d['share'])} of your expenses) goes out regularly "
                f"to {d['n']} payees. Largest: {top_en}. "
                f"Are these labour wages, suppliers, or something else? Classify them so we compute precisely.")
    return ""


def _fixed_components(d, lang) -> str:
    """يبني وصف مكوّنات الالتزامات الثابتة، ويعرض ما هو > 0 فقط."""
    labels = [("salary", "رواتب", "payroll"), ("rent", "إيجار", "rent"), ("loan", "قرض", "loan")]
    parts = []
    for key, ar, en in labels:
        v = d.get(key, 0) or 0
        if v > 0:
            name = ar if lang == "ar" else en
            parts.append(f"{name} {money(v, lang)}")
    sep = " + "
    return sep.join(parts) if parts else ("ثابتة" if lang == "ar" else "fixed")


# ---------- قرار الأسبوع ----------
def decision_headline(sar, tf, lang, kind="save") -> str:
    tw = timeframe_word(tf, lang)
    if kind == "collect":   # الرقم نقد عالق كذمم — نُحرّره لا نوفّره
        if lang == "ar":
            return f"قرار واحد هذا الأسبوع يمكن أن يُحرّر ~{money(sar,'ar')} عالقة كذمم لدى عملائك."
        return f"One decision this week can free up ~{money(sar,'en')} stuck as receivables with your clients."
    if kind == "recover":   # دفعة مكررة — استرداد محتمل بعد التحقق (لا وعد مؤكد)
        if lang == "ar":
            return f"تحقّق واحد هذا الأسبوع قد يسترد لك ~{money(sar,'ar')} — دفعة يبدو أنها كُررت."
        return f"One verification this week could recover ~{money(sar,'en')} — a payment that looks duplicated."
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
    if k == "act_stop_bleed":
        if lang == "ar":
            base = ("حسابك دخل السالب (سحب على المكشوف). " if d.get("overdraft")
                    else f"نشاطك خسر نقداً في {d['neg']} من {d['total']} أشهر. ")
            return (base + "أوقف النزيف قبل أي شيء: راجع أكبر بنود المصروف الثابت (رواتب/إيجار/أقساط)، "
                    "أعد جدولة أقساط التمويل مع البنك، وأوقف أي إنفاق غير أساسي هذا الأسبوع. "
                    "لا تعتمد على أن التمويل سيغطّي الفجوة — فهو ينتهي.")
        base = ("Your account went into overdraft. " if d.get("overdraft")
                else f"Your activity lost cash in {d['neg']} of {d['total']} months. ")
        return (base + "Stop the bleed first: review your largest fixed costs (payroll/rent/installments), "
                "reschedule financing installments with the bank, and halt any non-essential spend this week. "
                "Don't rely on financing to cover the gap — it runs out.")
    if k == "act_chase_collections":
        if lang == "ar":
            return (f"لديك {money(d['receivables'],'ar')} عالقة كذمم لم تُحصّل (نسبة تحصيلك {pct(d['rate'])} فقط). "
                    f"ابدأ حملة تحصيل فورية: اتصل بأكبر العملاء المتأخرين، اطلب دفعات مقدّمة، "
                    f"وأوقف التوريد الآجل للمتعثّرين — كل ريال تُحصّله يطيل عمر سيولتك مباشرة.")
        return (f"You have {money(d['receivables'],'en')} stuck as uncollected receivables (only {pct(d['rate'])} collected). "
                f"Launch a collection push now: call your largest overdue clients, ask for advances, "
                f"and pause credit sales to late payers — every riyal collected directly extends your runway.")
    if k == "act_cut_burn":
        if lang == "ar":
            return (f"قلّص مصاريفك بما لا يقل عن {money(d['burn'],'ar')} شهرياً لوقف نزيف "
                    f"السيولة — ابدأ بأكبر بند غير أساسي هذا الأسبوع.")
        return (f"Cut expenses by at least {money(d['burn'],'en')} per month to stop the cash "
                f"bleed — start with your largest non-essential line this week.")
    if k == "act_diversify":
        if lang == "ar":
            if d.get("monthly_new"):
                return (f"اعتمادك على مصدر وارد واحد ({pct(d['share'])}) خطر. استهدف إضافة "
                        f"~{money(d['monthly_new'],'ar')} شهرياً من مصادر وارد جديدة خلال 90 يوماً "
                        f"لتنزيل الحصة تحت 50%.")
            return (f"اعتمادك على مصدر وارد واحد ({pct(d['share'])}) خطر. ابدأ خلال 90 يوماً "
                    f"بإضافة عميلين جديدين على الأقل حتى لا يتوقف دخلك بتوقف جهة واحدة.")
        if d.get("monthly_new"):
            return (f"Depending on one inflow source ({pct(d['share'])}) is risky. Aim to add "
                    f"~{money(d['monthly_new'],'en')} per month from new inflow sources within 90 days "
                    f"to bring the share under 50%.")
        return (f"Depending on one inflow source ({pct(d['share'])}) is risky. Within 90 days, "
                f"add at least two new clients so one party stopping doesn't stop your income.")
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


# ---------- ملاحظات جودة البيانات (فحوصات السلامة) ----------
def dq_text(item, lang) -> str:
    k, d = item["key"], item["data"]
    if k == "utility_daily":
        if lang == "ar":
            return (f"غير منطقي: {d['n']} فاتورة لـ«{d['vendor']}» في شهر واحد ({d['ym']}) "
                    f"بإجمالي {money(d['total'],'ar')} — فاتورة المرفق تتكرر شهرياً لا يومياً. تحقق من بياناتك.")
        return (f"Implausible: {d['n']} bills to «{d['vendor']}» in one month ({d['ym']}) "
                f"totaling {money(d['total'],'en')} — utility bills recur monthly, not daily. Check your data.")
    if k == "category_dominant":
        if lang == "ar":
            return (f"بند «{d['cat']}» يمثل {pct(d['pct'])} من دخلك ({money(d['amount'],'ar')}) — "
                    f"نسبة كبيرة جداً لبند واحد؛ تأكد أن البيانات صحيحة ومقصودة.")
        return (f"«{d['cat']}» equals {pct(d['pct'])} of your income ({money(d['amount'],'en')}) — "
                f"unusually large for one line; confirm the data is correct and intended.")
    if k == "gap_pattern":
        if lang == "ar":
            return (f"«{d['cat']}» يظهر في {d['m']} أشهر فقط من {d['total']} — "
                    f"بيانات ناقصة أم نمط موسمي؟ وضّح حتى لا تنحرف الاتجاهات.")
        return (f"«{d['cat']}» appears in only {d['m']} of {d['total']} months — "
                f"missing data or seasonal? Clarify so trends don't skew.")
    return ""


# ---------- الجملة الصادمة (أول سطر في التقرير — تُشتق من أعلى خطر، لا من قالب) ----------
def shock_sentence(a, lang) -> str | None:
    keys = {f["key"]: f for f in a.findings}
    if "overdraft" in keys:
        d = keys["overdraft"]["data"]
        return (f"حسابك دخل السالب: الرصيد الختامي سالب {money(d['closing'],'ar')}. التمويل كان يستر النزيف."
                if lang == "ar" else
                f"Your account went negative: closing balance minus {money(d['closing'],'en')}. Financing was masking the bleed.")
    if "cash_buffer_risk" in keys:
        d = keys["cash_buffer_risk"]["data"]
        if lang == "ar":
            return f"رصيدك لامس {d['min']:,.2f} ريال. تعمل بلا وسادة نقدية."
        return f"Your balance touched SAR {d['min']:,.2f}. You operate with no cash cushion."
    if "receivables_crisis" in keys:
        d = keys["receivables_crisis"]["data"]
        return (f"{money(d['receivables'],'ar')} من مبيعاتك عالقة عند عملائك — حصّلت {pct(d['rate'])} فقط."
                if lang == "ar" else
                f"{money(d['receivables'],'en')} of your sales is stuck with clients — only {pct(d['rate'])} collected.")
    if "operating_bleed" in keys:
        d = keys["operating_bleed"]["data"]
        return (f"نشاطك خسر نقداً في {d['neg']} من {d['total']} شهراً."
                if lang == "ar" else
                f"Your operations lost cash in {d['neg']} of {d['total']} months.")
    if "customer_concentration" in keys:
        d = keys["customer_concentration"]["data"]
        return (f"{pct(d['share'])} من وارِدك معلّق على جهة واحدة: {d['name']}."
                if lang == "ar" else
                f"{pct(d['share'])} of your inflows ride on one source: {d['name']}.")
    return None


# ---------- أفضل خبر (توازن نفسي — إلزامي حين يوجد خبر صادق) ----------
def best_news(a, lang) -> str | None:
    # مبيعات نقدية موزّعة عبر فروع = قاعدة دخل لا تعتمد على عميل
    if a.cash_sales_share >= 0.35 and a.cash_branches >= 2:
        return (f"{pct(a.cash_sales_share)} من دخلك مبيعات نقدية عبر {a.cash_branches} فروع — "
                f"قاعدة دخل موزّعة لا تعتمد على عميل واحد."
                if lang == "ar" else
                f"{pct(a.cash_sales_share)} of your income is cash sales across {a.cash_branches} branches — "
                f"a distributed income base with no single-client dependency.")
    # تنويع مصادر حقيقي
    real = [s for s in a.income_by_customer if s[2] >= 0.30]
    if a.income_by_customer and not real and a.operating_income > 0:
        return ("لا تعتمد على عميل واحد — أكبر مصدر وارد أقل من 30% من دخلك."
                if lang == "ar" else
                "No single-client dependency — your largest source is under 30% of income.")
    if a.buffer_months is not None and a.buffer_months >= 3:
        return (f"وسادتك النقدية تغطي ~{a.buffer_months:.1f} شهراً من مصاريفك حتى لو توقف الدخل."
                if lang == "ar" else
                f"Your cash cushion covers ~{a.buffer_months:.1f} months of expenses even if income stopped.")
    if a.net_profit > 0 and a.avg_margin >= 0.10:
        return (f"تدفقك النقدي موجب: يبقى في حسابك {pct(a.avg_margin)} من كل ريال يدخل."
                if lang == "ar" else
                f"Your cash flow is positive: {pct(a.avg_margin)} of every riyal in stays in your account.")
    if 0 < a.salary_ratio < 0.30:
        return (f"رواتبك تحت السيطرة: {pct(a.salary_ratio)} فقط من وارِدك."
                if lang == "ar" else
                f"Payroll is under control: only {pct(a.salary_ratio)} of your inflows.")
    return None


# ---------- سلسلة السبب والنتيجة (محرك العلاقات المالية) ----------
def risk_chain_sentences(a, lang) -> list:
    """يحوّل سلاسل a.risk_chain إلى فقرات سردية سبب→نتيجة. هذا هو الفرق بين
    «قارئ كشف» يعرض نقاطاً منفصلة و«مستشار» يشرح كيف تتصل الأحداث ببعضها."""
    out = []
    for link in getattr(a, "risk_chain", []):
        kind, d = link["kind"], link["data"]
        if kind == "accrual_squeeze":
            comp = _fixed_components(d, lang)
            if lang == "ar":
                s = (f"مبيعاتك على الورق قوية ({money(d['invoiced'],'ar')})، "
                     f"لكنك لم تُحصّل منها إلا {pct(d['rate'])} ({money(d['collected'],'ar')})؛ "
                     f"فالنقد الفعلي الداخل إلى حسابك ~{money(d['cash_in_m'],'ar')} شهرياً فقط. "
                     f"وفي المقابل تخرج التزامات ثابتة ~{money(d['fixed_m'],'ar')} شهرياً ({comp}) "
                     f"تُدفع نقداً مهما تأخّر التحصيل. النتيجة: يخرج نقد أكثر مما يدخل بـ~{money(d['gap_m'],'ar')} "
                     f"شهرياً، وأي تأخّر إضافي في التحصيل يقصّر عمر سيولتك مباشرة")
                if d.get("survival_days"):
                    s += f" — وبالمعدل الحالي تكفيك السيولة ~{d['survival_days']:.0f} يوم فقط."
                else:
                    s += "."
                out.append(s)
            else:
                s = (f"On paper your sales are strong ({money(d['invoiced'],'en')}), "
                     f"but you collected only {pct(d['rate'])} of them ({money(d['collected'],'en')}); "
                     f"so real cash coming in is just ~{money(d['cash_in_m'],'en')}/month. "
                     f"Meanwhile fixed commitments of ~{money(d['fixed_m'],'en')}/month ({comp}) "
                     f"are paid in cash no matter what. The result: more cash leaves than arrives, by "
                     f"~{money(d['gap_m'],'en')}/month, and any further delay in collections directly shortens your runway")
                if d.get("survival_days"):
                    s += f" — at the current rate your cash lasts only ~{d['survival_days']:.0f} days."
                else:
                    s += "."
                out.append(s)
        elif kind == "concentration_burn":
            if lang == "ar":
                s = (f"يعتمد {pct(d['share'])} من وارِدك على {d['name']}؛ لو تأخّر أو توقّف، "
                     f"يسقط دخلك ~{money(d['monthly'],'ar')} شهرياً")
                if d.get("days_if_lost"):
                    s += f"، وتنتهي سيولتك خلال ~{d['days_if_lost']:.0f} يوم فقط. مصدر واحد يحمل خطر الشركة كله."
                else:
                    s += ". اعتماد على مصدر واحد يركّز خطر الشركة في نقطة واحدة."
                out.append(s)
            else:
                s = (f"{pct(d['share'])} of your inflows ride on {d['name']}; if it slows or stops, "
                     f"your income drops ~{money(d['monthly'],'en')}/month")
                if d.get("days_if_lost"):
                    s += f", and your cash runs out in ~{d['days_if_lost']:.0f} days. One source carries the whole company's risk."
                else:
                    s += ". Depending on one source concentrates all your risk in a single point."
                out.append(s)
    return out


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


def operating_note(a, lang) -> str | None:
    """يوضّح بشفافية أن رأس المال/التمويل/السحوبات استُبعدت من الإيراد التشغيلي الحقيقي."""
    if a.non_operating_in <= 0 and a.non_operating_out <= 0:
        return None
    if lang == "ar":
        return (f"إيرادك التشغيلي الحقيقي {money(a.operating_income,'ar')} "
                f"(بعد استبعاد {money(a.non_operating_in,'ar')} رأس مال/تمويل/تحويلات غامضة). "
                f"ومصروفك التشغيلي {money(a.operating_expense,'ar')} "
                f"(بعد استبعاد {money(a.non_operating_out,'ar')} سحوبات شخصية/سداد قروض/تحويلات داخلية). "
                f"هذي الأرقام التشغيلية هي أساس كل التحليل أدناه — لا الإجمالي الخام.")
    return (f"Your real operating income is {money(a.operating_income,'en')} "
            f"(after excluding {money(a.non_operating_in,'en')} of capital/financing/ambiguous transfers). "
            f"Operating expense is {money(a.operating_expense,'en')} "
            f"(after excluding {money(a.non_operating_out,'en')} of owner draws/loan repayments/internal transfers). "
            f"These operating figures are the basis for everything below — not the raw totals.")


def payroll_summary(a, lang) -> str:
    """ملخص كشف الرواتب (وضع تحليل الرواتب)."""
    if lang == "ar":
        return (f"كشف رواتب: إجمالي {money(a.salary_total,'ar')} شهرياً لـ{a.salary_count} موظف، "
                f"بمتوسط راتب {money(a.avg_salary,'ar')}.")
    return (f"Payroll file: total {money(a.salary_total,'en')}/month for {a.salary_count} staff, "
            f"average salary {money(a.avg_salary,'en')}.")


def salary_sentence(a, lang) -> str:
    """ملخص الرواتب المستخرج من الكشف — يظهر دائماً حين توجد رواتب."""
    if lang == "ar":
        return (f"رواتبك ~{money(a.salary_monthly,'ar')} شهرياً لـ{a.salary_count} مستفيد، "
                f"أي {pct(a.salary_ratio)} من الوارد إلى حسابك.")
    return (f"Payroll is ~{money(a.salary_monthly,'en')}/month for {a.salary_count} recipients — "
            f"{pct(a.salary_ratio)} of your inflows.")


def recurring_sentence(a, lang) -> str:
    """ملخص الالتزامات المتكررة الصامتة + إعادة تأطير الأكبر منها إلى «ألم» ملموس.
    الرقم السنوي تقدير مبني على استمرار المعدل الحالي — نقولها صراحة."""
    monthly_total = sum(r["monthly"] for r in a.recurring)
    top = max(a.recurring, key=lambda r: r["yearly"], default=None)
    if lang == "ar":
        s = (f"رصدنا {len(a.recurring)} التزاماً متكرراً بإجمالي ~{money(monthly_total,'ar')} شهرياً "
             f"(~{money(a.recurring_yearly,'ar')} سنوياً لو استمر بمعدله الحالي).")
        if top and top["yearly"] >= 6000:
            s += (f" الأكبر منها «{top['party']}» وحده يسحب ~{money(top['yearly'],'ar')} سنوياً — "
                  f"مبلغ يكفي لتوظيف مساعد بدوام جزئي. لم نجد في حركتك ما يدل على أنه ما زال مستخدماً، "
                  f"فتأكّد من قيمته قبل التجديد القادم.")
        else:
            s += " راجعها فقد يكون فيها ما لا تستخدمه فعلاً."
        return s
    s = (f"We found {len(a.recurring)} recurring commitments totaling ~{money(monthly_total,'en')}/month "
         f"(~{money(a.recurring_yearly,'en')}/year if it continues at this rate).")
    if top and top["yearly"] >= 6000:
        s += (f" The largest, «{top['party']}» alone, drains ~{money(top['yearly'],'en')}/year — "
              f"enough to hire a part-time assistant. We saw no other activity suggesting it's still in use, "
              f"so confirm its value before the next renewal.")
    else:
        s += " Review them for anything you no longer truly use."
    return s


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
        "chain": "سلسلة السبب والنتيجة", "priority": "الأولوية", "score_why": "لماذا هذا المؤشر؟",
        "dq": "ملاحظات على جودة البيانات", "best": "أفضل خبر", "clarify": "يحتاج توضيحك",
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
        "chain": "Cause & effect", "priority": "Priority", "score_why": "Why this score?",
        "dq": "Data quality notes", "best": "Best news", "clarify": "Needs your clarification",
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
        "hidden": "المخاطر المخفية", "chain_t": "سلسلة السبب والنتيجة", "todo_t": "ماذا تفعل الآن", "payroll_t": "قراءة الرواتب",
        "dq_t": "ملاحظات على جودة البيانات — راجعها قبل الاعتماد على الأرقام",
        "best_t": "أفضل خبر", "clarify_t": "يحتاج توضيحك",
        "recurring_t": "الالتزامات الصامتة", "summary_t": "ملخص الوضع النقدي",
        "cashflow_note": "هذه أرقام تدفق نقدي من كشف البنك — وليست صافي ربح محاسبي.",
        "payroll_mode": "تحليل الرواتب", "employees_t": "كشف الموظفين",
        "non_op_t": "تدفقات غير تشغيلية (مستبعدة من التحليل أعلاه)",
        "payroll_income_tip": "أدخل دخلك الشهري في خانة الرصيد لتعرف نسبة الرواتب من الدخل.",
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
        "hidden": "Hidden risks", "chain_t": "Cause & effect", "todo_t": "What to do now", "payroll_t": "Payroll read",
        "dq_t": "Data quality notes — review before relying on the numbers",
        "best_t": "Best news", "clarify_t": "Needs your clarification",
        "recurring_t": "Silent commitments", "summary_t": "Cash situation summary",
        "cashflow_note": "These are cash-flow figures from your bank statement — not accounting net profit.",
        "payroll_mode": "Payroll analysis", "employees_t": "Employees",
        "non_op_t": "Non-operating flows (excluded from the analysis above)",
        "payroll_income_tip": "Enter your monthly income in the balance field to see payroll-to-income ratio.",
        "err_generic": "We couldn't process the file. Make sure it has a clear transactions table and try again.",
        "err_nofile": "Please choose a file first.",
        "err_toobig": "File is too large. Maximum size is 25 MB.",
        "err_badformat": "Unsupported format. Use Excel, CSV, PDF, Word or text.",
    }
    return ar if lang == "ar" else en
