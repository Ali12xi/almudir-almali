"""
محرك التحليل المالي — كل الحسابات هنا حتمية (بالكود)، بدون ذكاء اصطناعي.
المدخل: كشف عمليات موحّد من extractors (التاريخ، البيان، النوع، التصنيف، الطرف، المبلغ).
المخرج: كائن Analysis يحمل بياناتٍ رقمية ومفاتيح — بلا نصوص لغوية.
الصياغة اللغوية كلها في i18n.py (يخدم العربي والإنجليزي معاً).

قاعدة المصداقية: الأرقام الدقيقة فقط حيث الرياضيات تسندها؛ التقديرات كنطاق متحفظ.
"""
from __future__ import annotations
import pandas as pd
from dataclasses import dataclass, field
import extractors


@dataclass
class Analysis:
    n_transactions: int
    months: list                      # [{ym, income, expense, net, margin}]
    total_income: float
    total_expense: float
    net_profit: float
    avg_margin: float
    income_by_customer: list          # [(name, amount, share)]
    expense_by_category: list         # [(cat, amount, share)]
    findings: list = field(default_factory=list)   # [{key, severity, data, sar, timeframe}]
    recommendations: list = field(default_factory=list)  # [{key, data, ...}]
    decision: dict | None = None      # {sar, timeframe, finding}
    runway: dict | None = None        # {known, burning, cash, burn, days, recent_net}
    total_savings: float = 0.0        # مجموع التوفير السنوي القابل للتنفيذ
    survival_days: float | None = None  # أيام بقاء السيولة (لو تحترق ومعروف الرصيد)
    safety_score: int = 100           # مؤشر أمان 0–100
    safety_band: str = "good"         # good | medium | high_risk
    avg_monthly_income: float = 0.0   # متوسط الدخل الشهري
    avg_monthly_expense: float = 0.0  # متوسط المصروف الشهري
    breakeven_drop_pct: float | None = None  # كم يتحمّل انخفاض المبيعات قبل الخسارة (وسادة الأمان)
    buffer_months: float | None = None       # شهور تغطية السيولة لو توقّف الدخل (يحتاج الرصيد)
    cash: float | None = None                # الرصيد البنكي الحالي (لو أُدخل)
    # --- فهم الكشف كاملاً (يُشتق من العمليات الخام — هذا ما يميّزنا) ---
    salary_total: float = 0.0        # إجمالي الرواتب في الفترة
    salary_monthly: float = 0.0      # متوسط الرواتب شهرياً
    salary_ratio: float = 0.0        # الرواتب ÷ الدخل
    salary_count: int = 0            # عدد المستفيدين المميّزين (تقدير الموظفين)
    recurring: list = field(default_factory=list)  # [{party, monthly, yearly, months}] التزامات متكررة
    recurring_yearly: float = 0.0    # إجمالي الالتزامات المتكررة سنوياً
    # --- تشغيلي مقابل غير تشغيلي (فخ الربح الجوهري) ---
    # رأس المال/التمويل/سحوبات المالك/سداد القروض/التحويل الداخلي ليست دخلاً أو مصروفاً
    # تشغيلياً — نستبعدها من التركّز والنسب، ونعرضها بشفافية في قسم منفصل.
    operating_income: float = 0.0
    operating_expense: float = 0.0
    non_operating_in: float = 0.0
    non_operating_out: float = 0.0
    non_operating_items: list = field(default_factory=list)  # [(category, amount, direction)]
    # --- توجيه النوع (تحليل مخصّص لكل ملف) ---
    ftype: str = "statement"         # statement | payroll | budget
    employees: list = field(default_factory=list)  # [(name, amount, share)] كشف رواتب
    avg_salary: float = 0.0          # متوسط الراتب (لقرار التوظيف)

    @property
    def first_ym(self):
        return self.months[0]["ym"] if self.months else "-"

    @property
    def last_ym(self):
        return self.months[-1]["ym"] if self.months else "-"

    @property
    def period_label(self):  # محايد لغوياً (للـ CLI)
        if not self.months:
            return "-"
        return self.first_ym if self.first_ym == self.last_ym else f"{self.first_ym} → {self.last_ym}"


def load_ledger(path: str) -> pd.DataFrame:
    df = extractors.extract(path)                     # طبقة موحّدة لكل الصيغ
    ftype = df.attrs.get("ftype", "statement")        # نوع الملف (يوجّه التحليل)
    df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce")
    df["المبلغ"] = pd.to_numeric(df["المبلغ"], errors="coerce").fillna(0.0)
    df = df[df["المبلغ"] > 0].copy()
    if df.empty:
        raise extractors.ExtractionError("ما لقيت مبالغ صالحة في الملف. تأكد أن فيه عمود مبلغ.")
    # تاريخ افتراضي (الشهر الحالي) للملفات بلا تواريخ (كشوف رواتب/قوائم) — لا نرفضها.
    if df["التاريخ"].isna().all():
        df["التاريخ"] = pd.Timestamp.today().normalize()
    else:
        df["التاريخ"] = df["التاريخ"].fillna(df["التاريخ"].dropna().iloc[0])
    df["ym"] = df["التاريخ"].dt.strftime("%Y-%m")
    df.attrs["ftype"] = ftype
    return df


def analyze(path: str, current_cash: float | None = None) -> Analysis:
    df = load_ledger(path)
    inc_mask = df["النوع"].astype(str).str.contains("دخل|إيراد|مبيع", regex=True)
    income_df = df[inc_mask]
    expense_df = df[~inc_mask]

    months = []
    for ym in sorted(df["ym"].unique()):
        inc = float(income_df[income_df["ym"] == ym]["المبلغ"].sum())
        exp = float(expense_df[expense_df["ym"] == ym]["المبلغ"].sum())
        net = inc - exp
        months.append({"ym": ym, "income": inc, "expense": exp, "net": net,
                       "margin": (net / inc) if inc else 0.0})

    total_income = float(income_df["المبلغ"].sum())
    total_expense = float(expense_df["المبلغ"].sum())
    net_profit = total_income - total_expense
    avg_margin = (net_profit / total_income) if total_income else 0.0

    a = Analysis(
        n_transactions=len(df), months=months,
        total_income=total_income, total_expense=total_expense,
        net_profit=net_profit, avg_margin=avg_margin,
        income_by_customer=[], expense_by_category=[],
    )
    a.ftype = df.attrs.get("ftype", "statement")
    n = max(1, len(months))
    a.avg_monthly_income = total_income / n
    a.avg_monthly_expense = total_expense / n

    # توجيه: كشف رواتب/ميزانية له تحليل مخصّص؛ الباقي = تحليل تدفق نقدي.
    if a.ftype == "payroll":
        _analyze_payroll_file(a, expense_df, current_cash)
        return a

    # فخ الربح الجوهري: نستبعد رأس المال/التمويل/سحوبات المالك/سداد القروض/
    # التحويل الداخلي/التحصيل الضريبي من التركّز والنسب التشغيلية — بشفافية كاملة
    # (تُعرض في قسم منفصل، لا تُخفى، لكنها لا تشوّه "الإيراد الحقيقي").
    non_op = extractors.NON_OPERATING | {"تحويل وارد غامض (غير تشغيلي)"}
    op_income_df = income_df[~income_df["التصنيف"].isin(non_op)]
    op_expense_df = expense_df[~expense_df["التصنيف"].isin(extractors.NON_OPERATING)]
    a.operating_income = float(op_income_df["المبلغ"].sum())
    a.operating_expense = float(op_expense_df["المبلغ"].sum())
    a.non_operating_in = total_income - a.operating_income
    a.non_operating_out = total_expense - a.operating_expense

    non_op_rows = pd.concat([
        income_df[income_df["التصنيف"].isin(non_op)],
        expense_df[expense_df["التصنيف"].isin(extractors.NON_OPERATING)],
    ])
    if not non_op_rows.empty:
        grp = non_op_rows.groupby(["التصنيف", "النوع"])["المبلغ"].sum()
        a.non_operating_items = sorted(
            [(str(cat), float(v), "دخل" if typ == "دخل" else "مصروف")
             for (cat, typ), v in grp.items()], key=lambda x: -x[1])

    by_cust = op_income_df.groupby("الطرف")["المبلغ"].sum().sort_values(ascending=False)
    a.income_by_customer = [(str(n), float(v), float(v) / a.operating_income if a.operating_income else 0.0)
                            for n, v in by_cust.items()]

    by_cat = op_expense_df.groupby("التصنيف")["المبلغ"].sum().sort_values(ascending=False)
    a.expense_by_category = [(str(c), float(v), float(v) / a.operating_expense if a.operating_expense else 0.0)
                             for c, v in by_cat.items()]

    # وسادة الأمان: كم يتحمّل انخفاض الوارد التشغيلي قبل نقطة التعادل — نستخدم
    # الأرقام التشغيلية (لا الإجمالي) حتى لا يخفي تمويل/رأس مال لمرة واحدة الخطر الحقيقي.
    avg_monthly_op_income = a.operating_income / n
    avg_monthly_op_expense = a.operating_expense / n
    a.breakeven_drop_pct = (
        (avg_monthly_op_income - avg_monthly_op_expense) / avg_monthly_op_income
        if avg_monthly_op_income > 0 else None)

    _analyze_payroll(a, expense_df)
    _detect_recurring(a, expense_df)
    _detect_findings(a, income_df, expense_df)
    _forecast_runway(a, current_cash)
    _compute_buffer(a, current_cash)
    _build_decision_and_recs(a)
    _compute_scores(a)
    return a


def _analyze_payroll_file(a: Analysis, expense_df, monthly_income: float | None):
    """تحليل مخصّص لكشف رواتب: إجمالي، لكل موظف، متوسط، والنسبة والقرار عند معرفة الدخل.
    (current_cash يُعاد استخدامه كـ'الدخل الشهري' في وضع الرواتب.)"""
    a.salary_total = a.total_expense
    a.salary_count = int(expense_df["الطرف"].astype(str).nunique())
    a.salary_monthly = a.salary_total                    # الملف يمثّل دفعة رواتب شهرية
    a.avg_salary = a.salary_total / max(1, a.salary_count)
    by_emp = expense_df.groupby("الطرف")["المبلغ"].sum().sort_values(ascending=False)
    a.employees = [(str(n), float(v), float(v) / a.salary_total if a.salary_total else 0.0)
                   for n, v in by_emp.items()]

    findings, recs = [], []
    # نسبة الرواتب من الدخل — فقط إذا أدخل المستخدم دخله الشهري
    if monthly_income and monthly_income > 0:
        a.salary_ratio = a.salary_total / monthly_income
        sev = "high" if a.salary_ratio >= 0.55 else "medium" if a.salary_ratio >= 0.40 else "low"
        findings.append({"key": "payroll_ratio", "severity": sev,
                         "data": {"ratio": a.salary_ratio, "monthly": a.salary_monthly,
                                  "count": a.salary_count, "income": monthly_income}})
        if a.salary_ratio >= 0.40:
            recs.append({"key": "act_review_payroll",
                         "data": {"ratio": a.salary_ratio, "monthly": a.salary_monthly}})
    # قرار التوظيف: أثر إضافة موظف بمتوسط الراتب
    findings.append({"key": "hire_impact",
                     "data": {"avg": a.avg_salary, "new_total": a.salary_total + a.avg_salary,
                              "new_ratio": ((a.salary_total + a.avg_salary) / monthly_income)
                              if monthly_income else None}})
    if a.employees:
        top_n, top_v, top_sh = a.employees[0]
        if top_sh >= 0.40 and a.salary_count >= 2:
            findings.append({"key": "salary_concentration",
                             "severity": "medium",
                             "data": {"name": top_n, "share": top_sh, "amount": top_v}})
    a.findings = findings
    a.recommendations = recs[:3]


# أنماط تمييز الرواتب من التصنيف أو البيان (يشمل الأجور والمكافآت)
_SALARY_RE = "روات|راتب|أجور|أجر|مكافأ|salary|payroll|wage"


def _analyze_payroll(a: Analysis, expense_df):
    """يستخرج الرواتب من الكشف الخام: الإجمالي، النسبة للدخل، وعدد الموظفين المقدّر."""
    if expense_df.empty:
        return
    mask = (expense_df["التصنيف"].astype(str).str.contains(_SALARY_RE, regex=True, case=False)
            | expense_df["البيان"].astype(str).str.contains(_SALARY_RE, regex=True, case=False))
    sal = expense_df[mask]
    if sal.empty:
        return
    n = max(1, len(a.months))
    a.salary_total = float(sal["المبلغ"].sum())
    a.salary_monthly = a.salary_total / n
    # النسبة من الإيراد التشغيلي الحقيقي — لا الإجمالي (رأس مال/تمويل يخفّض النسبة كذباً)
    base = a.operating_income or a.total_income
    a.salary_ratio = (a.salary_total / base) if base else 0.0
    a.salary_count = int(sal["الطرف"].astype(str).str.strip().replace("", "غير محدد").nunique())


def _detect_recurring(a: Analysis, expense_df):
    """يكشف الالتزامات المتكررة الصامتة: طرف يتكرر عبر عدة أشهر بمبلغ ثابت تقريباً
    (اشتراكات/خدمات يغفل عنها صاحب الشركة). يستثني الرواتب — ليست 'خفية'."""
    if expense_df.empty or len(a.months) < 2:
        return
    n_months = len(a.months)
    min_months = max(2, round(n_months * 0.5))
    # نستثني الأساسيات (رواتب/إيجار/مرافق) — ليست "خفية"؛ التركيز على الاشتراكات والخدمات المنسية
    essential = _SALARY_RE + "|إيجار|ايجار|rent|كهرباء|ماء|مياه|مرافق|water|electric|اتصالات|إنترنت|انترنت|internet"
    ess_mask = (expense_df["التصنيف"].astype(str).str.contains(essential, regex=True, case=False)
                | expense_df["البيان"].astype(str).str.contains(essential, regex=True, case=False))
    # نستبعد غير التشغيلي (سداد قروض/تحويل داخلي/ضريبة) — ليست "التزامات صامتة" بل معروفة ومقصودة
    non_op_mask = expense_df["التصنيف"].isin(extractors.NON_OPERATING)
    ex = expense_df[~ess_mask & ~non_op_mask]
    recurring = []
    for party, g in ex.groupby(ex["الطرف"].astype(str)):
        by_month = g.groupby("ym")["المبلغ"].sum()
        if len(by_month) < min_months:
            continue
        mean = float(by_month.mean())
        if mean <= 0:
            continue
        cv = float(by_month.std(ddof=0)) / mean if mean else 1.0   # ثبات المبلغ
        # حد أدنى ثابت بسيط: يستبعد ضجيج التقريب فقط، لا الاشتراكات الصغيرة الحقيقية
        # (اشتراك بـ92 ريال شهرياً "خفي" وضار تراكمياً — لا نتجاهله لحجم المصاريف الكلي).
        if cv <= 0.25 and mean >= 30.0:                             # متكرر ومستقر وذو قيمة
            recurring.append({"party": party, "monthly": mean,
                              "yearly": mean * 12, "months": int(len(by_month))})
    recurring.sort(key=lambda r: r["yearly"], reverse=True)
    a.recurring = recurring[:10]
    a.recurring_yearly = sum(r["yearly"] for r in recurring)


def _compute_scores(a: Analysis):
    """أرقام أبطال — كلها مشتقّة بشفافية من إشارات حقيقية (لا تخمين)."""
    # 1) إجمالي التوفير السنوي القابل للتنفيذ (من قفزات المصاريف فقط — قابلة للفعل)
    a.total_savings = sum(f["data"]["excess_year"]
                          for f in a.findings if f["key"] == "expense_spike")

    # 2) أيام بقاء السيولة
    if a.runway and a.runway.get("burning"):
        a.survival_days = a.runway["days"]

    # 3) مؤشر الأمان النقدي (0–100) — يعتمد على مخاطر نقدية حقيقية فقط.
    #    ملاحظة محاسبية: صافي التدفق ~0 (داخل≈خارج) طبيعي لحساب تمرّ منه الأموال،
    #    وليس "خسارة" — فلا نعاقب عليه، ولا نستخدم "الهامش" كإشارة أمان.
    score = 100.0
    if a.income_by_customer:                                    # تركّز مصدر الوارد (أخطر عامل بنيوي)
        top = a.income_by_customer[0][2]
        score -= 40 if top >= 0.60 else 28 if top >= 0.45 else 15 if top >= 0.30 else 0
    if a.survival_days is not None:                            # احتراق نقدي فعلي (السيولة تنزل)
        d = a.survival_days
        score -= 35 if d < 30 else 22 if d < 60 else 10 if d < 120 else 0
    elif a.runway and a.runway.get("burning"):                 # يحترق لكن الرصيد غير معروف
        score -= 15
    for f in a.findings:                                       # اتجاهات نقدية سلبية حقيقية
        if f["key"] in ("margin_erosion", "sales_up_profit_down"):
            score -= 12
        elif f["key"] == "high_payroll":
            score -= 8
    a.safety_score = int(max(5, min(99, round(score))))
    a.safety_band = ("high_risk" if a.safety_score < 45
                     else "medium" if a.safety_score < 75 else "good")


def _detect_findings(a: Analysis, income_df, expense_df):
    """كشف المخاطر المخفية — بيانات فقط، بلا نصوص لغوية."""
    findings = []
    n_months = max(1, len(a.months))

    # 1) تركّز مصدر وارد حقيقي — نستبعد المصادر العامة (إيداع نقدي/تحويلات/رسوم):
    #    الإيداع النقدي ليس "عميلاً" يُخشى فقدانه، بل مبيعات نقدية. لا ننذر خطأً.
    real_sources = [(n, amt, sh) for (n, amt, sh) in a.income_by_customer
                    if n not in extractors.GENERIC_SOURCES]
    if real_sources:
        name, amt, share = real_sources[0]
        if share >= 0.30:
            findings.append({
                "key": "customer_concentration", "severity": "high",
                "data": {"name": name, "share": share, "monthly": amt / n_months},
                "sar": amt / n_months, "timeframe": "monthly",
            })

    # 2) تآكل الهامش
    if len(a.months) >= 3:
        first_m = a.months[0]["margin"]
        last_m = a.months[-1]["margin"]
        if last_m < first_m - 0.03:
            findings.append({
                "key": "margin_erosion", "severity": "high",
                "data": {"first": first_m, "last": last_m, "drop_pts": (first_m - last_m) * 100},
                "sar": None, "timeframe": None,
            })

    # 3) مبيعات تزيد / أرباح تنقص
    if len(a.months) >= 2:
        if a.months[-1]["income"] > a.months[0]["income"] and a.months[-1]["net"] < a.months[0]["net"]:
            findings.append({
                "key": "sales_up_profit_down", "severity": "high",
                "data": {}, "sar": None, "timeframe": None,
            })

    # 4) قفزة في مصروف (متوسط آخر شهرين مقابل أول شهرين لكل تصنيف)
    if len(a.months) >= 4:
        early = [m["ym"] for m in a.months[:2]]
        late = [m["ym"] for m in a.months[-2:]]
        spikes = []
        for cat in expense_df["التصنيف"].astype(str).unique():
            c = expense_df[expense_df["التصنيف"].astype(str) == cat]
            early_avg = c[c["ym"].isin(early)]["المبلغ"].sum() / 2
            late_avg = c[c["ym"].isin(late)]["المبلغ"].sum() / 2
            if early_avg > 0 and late_avg > early_avg * 1.6:
                spikes.append({
                    "key": "expense_spike", "severity": "medium",
                    "data": {"category": cat, "early": early_avg, "late": late_avg,
                             "excess_year": (late_avg - early_avg) * 12},
                    "sar": (late_avg - early_avg) * 12, "timeframe": "yearly",
                })
        spikes.sort(key=lambda f: f["sar"], reverse=True)
        findings.extend(spikes)

    # 5) وسادة تدفق رقيقة — نُظهرها فقط عند احتراق نقدي فعلي (الرصيد ينزل).
    #    صافي تدفق ~0 لحساب متوازن (داخل≈خارج) طبيعي، وليس خطراً — فلا ننذر عبثاً.
    burning = bool(a.runway and a.runway.get("burning"))
    if (burning and a.breakeven_drop_pct is not None and a.breakeven_drop_pct < 0.20):
        findings.append({
            "key": "thin_cushion",
            "severity": "high" if a.breakeven_drop_pct < 0.10 else "medium",
            "data": {"drop_pct": a.breakeven_drop_pct},
            "sar": None, "timeframe": None,
        })

    # 6) عبء الرواتب مرتفع (الرواتب تلتهم نسبة كبيرة من الدخل)
    if a.salary_total > 0 and a.salary_ratio >= 0.40:
        findings.append({
            "key": "high_payroll",
            "severity": "high" if a.salary_ratio >= 0.55 else "medium",
            "data": {"ratio": a.salary_ratio, "monthly": a.salary_monthly, "count": a.salary_count},
            "sar": None, "timeframe": None,
        })

    a.findings = findings


def _forecast_runway(a: Analysis, current_cash: float | None):
    if len(a.months) < 2:
        return
    recent_net = sum(m["net"] for m in a.months[-2:]) / 2
    if current_cash is None:
        a.runway = {"known": False, "recent_net": recent_net}
        return
    if recent_net >= 0:
        a.runway = {"known": True, "burning": False, "recent_net": recent_net, "cash": current_cash}
        return
    burn = -recent_net
    a.runway = {"known": True, "burning": True, "recent_net": recent_net,
                "cash": current_cash, "burn": burn, "days": (current_cash / burn) * 30}


def _compute_buffer(a: Analysis, current_cash: float | None):
    """شهور تغطية السيولة لو توقّف الدخل تماماً — قيمة تظهر حتى للشركة الرابحة."""
    a.cash = current_cash
    if current_cash and a.avg_monthly_expense > 0:
        a.buffer_months = current_cash / a.avg_monthly_expense


def _build_decision_and_recs(a: Analysis):
    """قرار الأسبوع = أعلى رافعة بالريال. التوصيات = أفعال قابلة للتنفيذ (لا تكرار للتشخيص)."""
    levers = [f for f in a.findings if f.get("sar")]
    levers.sort(key=lambda f: f["sar"], reverse=True)

    if levers:
        top = levers[0]
        # نوع القرار: تركّز العملاء = حماية دخل مهدَّد؛ غيره = توفير مباشر. الصياغة تختلف.
        kind = "protect" if top["key"] == "customer_concentration" else "save"
        a.decision = {"sar": top["sar"], "timeframe": top["timeframe"], "finding": top, "kind": kind}

    recs = []
    # السيولة أولاً — أخطر تهديد
    if a.runway and a.runway.get("burning"):
        recs.append({"key": "act_cut_burn", "data": {"burn": a.runway["burn"]}})

    # أفعال مشتقّة من الروافع (لكل خطر فعلٌ مسعّر بهدف رقمي محدّد)
    n = max(1, len(a.months))
    for f in levers:
        if f["key"] == "customer_concentration" and a.income_by_customer:
            top_amt = a.income_by_customer[0][1]                # إجمالي دخل أكبر عميل
            # الدخل الجديد المطلوب لتنزيل حصته تحت 50%:  top/(total+N) < 0.5 → N > 2·top − total
            need_monthly = max(0.0, (2 * top_amt - a.total_income)) / n
            recs.append({"key": "act_diversify",
                         "data": {"share": f["data"]["share"], "monthly_new": need_monthly}})
        elif f["key"] == "expense_spike":
            recs.append({"key": "act_trim",
                         "data": {"category": f["data"]["category"],
                                  "target": f["data"]["early"], "yearly": f["data"]["excess_year"]}})

    # أفعال لمخاطر بلا رقم مباشر
    keys = {f["key"] for f in a.findings}
    if "thin_cushion" in keys:
        dp = next(f["data"]["drop_pct"] for f in a.findings if f["key"] == "thin_cushion")
        recs.append({"key": "act_cushion", "data": {"drop_pct": dp}})
    if keys & {"margin_erosion", "sales_up_profit_down"}:
        recs.append({"key": "act_review_costs", "data": {}})
    if "high_payroll" in keys:
        recs.append({"key": "act_review_payroll",
                     "data": {"ratio": a.salary_ratio, "monthly": a.salary_monthly}})
    # مراجعة الالتزامات المتكررة الصامتة (فرصة توفير محتملة)
    if a.recurring_yearly > 0:
        recs.append({"key": "act_review_recurring",
                     "data": {"yearly": a.recurring_yearly, "count": len(a.recurring)}})

    a.recommendations = recs[:3]
