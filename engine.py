"""
محرك التحليل المالي — كل الحسابات هنا حتمية (بالكود)، بدون ذكاء اصطناعي.
المدخل: كشف عمليات موحّد من extractors (التاريخ، البيان، النوع، التصنيف، الطرف، المبلغ).
المخرج: كائن Analysis يحمل بياناتٍ رقمية ومفاتيح — بلا نصوص لغوية.
الصياغة اللغوية كلها في i18n.py (يخدم العربي والإنجليزي معاً).

قاعدة المصداقية: الأرقام الدقيقة فقط حيث الرياضيات تسندها؛ التقديرات كنطاق متحفظ.
"""
from __future__ import annotations
import re
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
    score_breakdown: list = field(default_factory=list)  # [(reason, points)] تفكيك مؤشر الأمان
    risk_chain: list = field(default_factory=list)  # [{kind, data}] سلسلة السبب والنتيجة (محرك العلاقات المالية)
    fixed_monthly: float = 0.0       # إجمالي الالتزامات النقدية الثابتة شهرياً (رواتب+إيجار+قرض)
    fixed_components: dict = field(default_factory=dict)  # {salary, rent, loan} تفكيك الالتزامات
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
    # --- استحقاق مقابل نقد (أزمة التدفق النقدي) ---
    # لو الملف يفرّق الفاتورة الآجلة عن التحصيل: الفاتورة إيراد محاسبي وليست نقداً داخلاً.
    is_accrual: bool = False          # هل الملف دفتر استحقاق (فيه فواتير + تحصيل منفصل)؟
    invoiced_total: float = 0.0       # إجمالي الفواتير المصدرة (مبيعات آجلة)
    collected_total: float = 0.0      # إجمالي التحصيل النقدي الفعلي
    receivables: float = 0.0          # الذمم المدينة المتراكمة = فواتير - تحصيل
    collection_rate: float = 0.0      # نسبة التحصيل من الفواتير
    # --- الرصيد الجاري والسحب على المكشوف (الرصيد يخدع؛ نُعيد بناءه لنكشف الحقيقة) ---
    opening_balance: float = 0.0     # الرصيد الافتتاحي (لُقط من الكشف، ليس عملية)
    closing_balance: float | None = None  # الرصيد الختامي المُعاد بناؤه = افتتاحي + صافي الحركة
    min_balance: float | None = None      # أدنى رصيد بلغه الحساب خلال الفترة
    overdraft: bool = False          # هل دخل الحساب السالب (سحب على المكشوف)؟
    # --- وسادة الرصيد (من عمود الرصيد الحقيقي حركةً بحركة — العطل الأخطر سابقاً) ---
    median_balance: float | None = None   # وسيط الرصيد (المستوى المعتاد للنقد)
    pct_below_5k: float | None = None     # نسبة الحركات التي كان الرصيد فيها < 5,000
    pct_below_1k: float | None = None     # نسبة الحركات التي كان الرصيد فيها < 1,000
    days_of_cover: float | None = None    # وسيط الرصيد ÷ متوسط الصادر اليومي (وسادة بالأيام)
    cash_branches: int = 0                # عدد فروع الإيداع النقدي (مبيعات نقدية عبر N فروع)
    cash_sales_share: float = 0.0         # حصة المبيعات النقدية من الوارد
    recurring_payees: list = field(default_factory=list)  # [{payee,count,months,total}] مدفوعات متكررة لأفراد
    data_quality: list = field(default_factory=list)      # [{key,data}] ملاحظات سلامة البيانات
    neg_op_months: int = 0           # عدد الأشهر ذات التدفق التشغيلي السالب
    op_months_total: int = 0         # إجمالي الأشهر (للنسبة)
    unknown_inflows: dict = field(default_factory=dict)  # {count, total} وارد غير مُوضّح (نعترف لا نخمّن)
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
    # أرصدة الكشف (تُلتقط مبكراً — عمليات النسخ اللاحقة قد تُسقط attrs)
    opening = df.attrs.get("opening_balance", 0.0)
    closing = df.attrs.get("closing_balance")
    min_bal = df.attrs.get("min_balance")
    balances = df.attrs.get("balances")
    branches = df.attrs.get("cash_branches", 0)
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
    keep = {k: v for k, v in (("opening_balance", opening),
                              ("closing_balance", closing),
                              ("min_balance", min_bal),
                              ("balances", balances),
                              ("cash_branches", branches)) if v is not None}
    df.attrs["ftype"] = ftype
    df.attrs.update(keep)
    return df


# علامات الفاتورة الآجلة (استحقاق، ليست نقداً) مقابل التحصيل النقدي الفعلي
_INVOICE_RE = r"فاتورة|invoice|مبيعات\s*آجل|آجل|billed|accrual|مستحق\b"
_COLLECT_RE = r"تحصيل|تسديد عميل|collect|receipt|سداد عميل|مقبوضات"


def _detect_accrual(income_df):
    """يكتشف إن كان الدخل يفرّق الفواتير الآجلة عن التحصيل النقدي.
    يُرجع (is_accrual, invoiced, collected, cash_income_df)."""
    if income_df.empty:
        return False, 0.0, 0.0, income_df
    blob = (income_df["التصنيف"].astype(str) + " " + income_df["البيان"].astype(str))
    inv_mask = blob.str.contains(_INVOICE_RE, regex=True, case=False, na=False)
    col_mask = blob.str.contains(_COLLECT_RE, regex=True, case=False, na=False)
    invoiced = float(income_df[inv_mask]["المبلغ"].sum())
    collected = float(income_df[col_mask]["المبلغ"].sum())
    # استحقاق فعلي: توجد فواتير وتحصيل، والفواتير أكبر جوهرياً من التحصيل (تراكم ذمم)
    is_accrual = bool(inv_mask.any() and col_mask.any() and invoiced > collected * 1.3)
    if is_accrual:
        # النقد الداخل = التحصيل فقط (+أي دخل غير فاتورة/تحصيل). الفواتير تُستبعد كـ"نقد".
        cash_income_df = income_df[~inv_mask]
    else:
        cash_income_df = income_df
    return is_accrual, invoiced, collected, cash_income_df


# فئات التحويل التي قد تخفي راتباً موصوفاً بـ«تحويل - فلان» بدل «راتب - فلان»
_TRANSFERISH = {"تحويلات", "تحويل", "حوالة صادرة", "مدفوعات لأفراد وجهات",
                "مصروفات أخرى", "تحويل غير مسمّى (يحتاج توضيح)"}


def _pool_salaries_by_person(df):
    """راتب الشخص يبقى راتباً مهما تغيّر الوصف — «ابحث عن الشخص، مو الكلمة».
    شهرٌ يُكتب «راتب محمد عبدالله» وشهرٌ «تحويل - محمد عبدالله» (يتغيّر موظف البنك):
    كان النصف الثاني يذوب في «تحويلات/أخرى» فتظهر الرواتب نصف حقيقتها (فخ أبو فيصل).
    القاعدة: من ثبت أنه يستلم راتباً (وصفٌ فيه «راتب» باسمه)، تُحسب تحويلاته الأخرى
    المشابهة راتباً — بشرط مبلغ قريب من راتبه المعتاد (0.5×–1.5× الوسيط) لعدم ابتلاع سُلفة."""
    exp = df["النوع"].astype(str).str.contains("دخل|إيراد|مبيع", regex=True) == False
    sal_mask = (df["التصنيف"].astype(str).str.contains(_SALARY_RE, regex=True, case=False)
                | df["البيان"].astype(str).str.contains(_SALARY_RE, regex=True, case=False)) & exp
    if not sal_mask.any():
        return df
    for payee, g in df[sal_mask].groupby("الطرف"):
        name = str(payee).strip()
        if len(name) < 5 or name.lower() in _GENERIC_EMP or name in extractors.GENERIC_SOURCES:
            continue
        med = float(g["المبلغ"].median())
        if med <= 0:
            continue
        # تحويلات لنفس الاسم (في البيان) بفئة تحويل/غامضة وبمبلغ ضمن نطاق راتبه
        pat = r"(?<![\w؀-ۿ])" + re.escape(name) + r"(?![\w؀-ۿ])"
        cand = (exp & ~sal_mask
                & df["التصنيف"].astype(str).isin(_TRANSFERISH)
                & df["البيان"].astype(str).str.contains(pat, regex=True)
                & df["المبلغ"].between(0.5 * med, 1.5 * med))
        if cand.any():
            df.loc[cand, "التصنيف"] = "رواتب"
            df.loc[cand, "الطرف"] = name
    return df


def analyze(path: str, current_cash: float | None = None) -> Analysis:
    df = load_ledger(path)
    df = _pool_salaries_by_person(df)
    inc_mask = df["النوع"].astype(str).str.contains("دخل|إيراد|مبيع", regex=True)
    income_df_all = df[inc_mask]
    expense_df = df[~inc_mask]

    # استحقاق مقابل نقد: لو الملف يفرّق الفاتورة عن التحصيل، النقد الداخل = التحصيل فقط
    is_accrual, invoiced, collected, income_df = _detect_accrual(income_df_all)

    months = []
    for ym in sorted(df["ym"].unique()):
        inc = float(income_df[income_df["ym"] == ym]["المبلغ"].sum())
        exp = float(expense_df[expense_df["ym"] == ym]["المبلغ"].sum())
        net = inc - exp
        months.append({"ym": ym, "income": inc, "expense": exp, "net": net,
                       "margin": (net / inc) if inc else 0.0})

    total_income = float(income_df["المبلغ"].sum())          # النقد الداخل الفعلي
    total_expense = float(expense_df["المبلغ"].sum())
    net_profit = total_income - total_expense
    avg_margin = (net_profit / total_income) if total_income else 0.0

    a = Analysis(
        n_transactions=len(df), months=months,
        total_income=total_income, total_expense=total_expense,
        net_profit=net_profit, avg_margin=avg_margin,
        income_by_customer=[], expense_by_category=[],
    )
    a.is_accrual = is_accrual
    if is_accrual:
        a.invoiced_total = invoiced
        a.collected_total = collected
        a.receivables = invoiced - collected
        a.collection_rate = collected / invoiced if invoiced else 0.0
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
    non_op = extractors.NON_OPERATING | {"تحويل وارد غامض (غير تشغيلي)", "وارد غير مُوضّح (يحتاج توضيح)"}
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

    # المدفوعات لأفراد: نفصل المتكرر (علاقة مستمرة تحتاج تصنيف المستخدم) عن المتفرق —
    # كتلة واحدة باسم مبهم تطغى على الفئات الحقيقية وتخفي أكبر مصروف فعلي.
    _detect_recurring_payees(a, expense_df)
    person_mask = op_expense_df["التصنيف"] == "مدفوعات لأفراد وجهات"
    if person_mask.any():
        rec_names = {p["payee"] for p in a.recurring_payees}
        op_expense_df = op_expense_df.copy()
        is_rec = person_mask & op_expense_df["الطرف"].astype(str).isin(rec_names)
        op_expense_df.loc[is_rec, "التصنيف"] = "مدفوعات متكررة لأفراد (تحتاج تصنيفك)"
        op_expense_df.loc[person_mask & ~is_rec, "التصنيف"] = "حوالات لأفراد (متفرقة)"

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

    # الرصيد يخدع: نُعيد بناء الرصيد الجاري من الافتتاحي + كل الحركات (بما فيها التمويل)
    # لنكشف إن كان الحساب دخل السالب فعلاً — أوضح إشارة خطر في أي كشف، وكان النظام يعبرها.
    a.opening_balance = float(df.attrs.get("opening_balance", 0.0) or 0.0)
    _analyze_balance_and_bleed(a, df, op_income_df, op_expense_df)

    # المبيعات النقدية عبر الفروع (قراءة إيجابية: قاعدة دخل موزّعة لا «عميل واحد»)
    a.cash_branches = int(df.attrs.get("cash_branches", 0) or 0)
    cash_sales = float(income_df[income_df["التصنيف"] == "مبيعات نقدية (إيداع صراف)"]["المبلغ"].sum())
    a.cash_sales_share = cash_sales / total_income if total_income else 0.0

    # الرصيد الختامي من الكشف = النقد الحالي تلقائياً (حين لا يُدخله المستخدم يدوياً)
    if current_cash is None and a.closing_balance is not None and a.closing_balance > 0:
        current_cash = a.closing_balance

    _analyze_payroll(a, expense_df)
    # حارس «اعترف لا تخمّن»: على كشف بنكي، «رواتب 1,036 لمستفيد واحد» لشركة تمرّر
    # الملايين تخمينٌ واثق لا معلومة — نكتمه، وكاشف المدفوعات المتكررة يحل محله.
    if a.salary_total > 0 and a.salary_ratio < 0.02:
        a.salary_total = a.salary_monthly = a.salary_ratio = 0.0
        a.salary_count = 0
    _compute_fixed_obligations(a, expense_df)
    _detect_recurring(a, expense_df)
    _sanity_checks(a, df, income_df, expense_df)
    _detect_findings(a, income_df, expense_df)
    _forecast_runway(a, current_cash)
    _compute_buffer(a, current_cash)
    _build_decision_and_recs(a)
    _compute_scores(a)
    _build_risk_chain(a, expense_df)
    return a


def _analyze_payroll_file(a: Analysis, expense_df, monthly_income: float | None):
    """تحليل مخصّص لكشف رواتب: إجمالي، لكل موظف، متوسط، والنسبة والقرار عند معرفة الدخل.
    (current_cash يُعاد استخدامه كـ'الدخل الشهري' في وضع الرواتب.)"""
    a.salary_total = a.total_expense
    a.salary_count = _count_employees(expense_df["الطرف"])
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

# تسميات مجمّعة/عامة ليست أسماء موظفين حقيقية — تُستبعد من عدّ الموظفين
_GENERIC_EMP = {"مدد", "موظف", "غير محدد", "رواتب", "راتب", "ملف رواتب",
                "الموظفون", "الموظفين", "موظفون", "موظفين",
                "payroll", "staff", "employee", "مستفيد", ""}


def _count_employees(series) -> int:
    """يعدّ الموظفين المميّزين، مستبعداً التسميات المجمّعة (دفعة 'مدد'/'موظف' ليست شخصاً)."""
    names = {str(x).strip() for x in series}
    real = {n for n in names if n and n.lower() not in _GENERIC_EMP}
    return len(real) or len(names)


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
    # الرقم الشهري = وسيط مجاميع الشهور، لا المتوسط: شهر فيه «مكافآت نهاية العام»
    # يرفع المتوسط فيصير «رواتبك 68,900» لصاحبٍ يعرف رقمه غيباً (64,700) — يفقد الثقة.
    by_month = sal.groupby("ym")["المبلغ"].sum()
    a.salary_monthly = float(by_month.median()) if len(by_month) >= 3 else a.salary_total / n
    # النسبة من حجم النشاط الحقيقي: في وضع الاستحقاق نستخدم الفواتير (حجم الشركة)،
    # لا التحصيل النقدي الصغير — وإلا تطلع نسبة مضلّلة (190%!) بسبب تأخر التحصيل.
    base = a.invoiced_total if a.is_accrual and a.invoiced_total else (a.operating_income or a.total_income)
    a.salary_ratio = (a.salary_total / base) if base else 0.0
    a.salary_count = _count_employees(sal["الطرف"])


# أنماط الالتزامات النقدية الثابتة (تُدفع نقداً كل شهر بغضّ النظر عن التحصيل)
_RENT_RE = r"إيجار|ايجار|rent|lease"
_LOAN_RE = r"قرض|قسط|أقساط|اقساط|تمويل|loan|installment|repayment"


def _compute_fixed_obligations(a: Analysis, expense_df):
    """يجمع الالتزامات النقدية الثابتة شهرياً (رواتب + إيجار + سداد قرض).
    هذه تُدفع نقداً كل شهر مهما تأخّر التحصيل — لذلك تُقاس مقابل النقد الداخل الفعلي."""
    if expense_df.empty:
        return
    n = max(1, len(a.months))
    cat = expense_df["التصنيف"].astype(str)
    ben = expense_df["البيان"].astype(str)
    rent_mask = cat.str.contains(_RENT_RE, case=False, regex=True) | ben.str.contains(_RENT_RE, case=False, regex=True)
    loan_mask = cat.str.contains(_LOAN_RE, case=False, regex=True) | ben.str.contains(_LOAN_RE, case=False, regex=True)
    rent_m = float(expense_df[rent_mask]["المبلغ"].sum()) / n
    loan_m = float(expense_df[loan_mask]["المبلغ"].sum()) / n
    salary_m = a.salary_monthly
    a.fixed_components = {"salary": salary_m, "rent": rent_m, "loan": loan_m}
    a.fixed_monthly = salary_m + rent_m + loan_m


def _analyze_balance_and_bleed(a: Analysis, df, op_income_df, op_expense_df):
    """يكشف نزيف التشغيل شهرياً + يُعيد بناء الرصيد الجاري لكشف السحب على المكشوف.
    الدرس الذي طلبه المراجع: الرصيد الموجب فترة طويلة بفضل القرض يخدع — والحقيقة أن
    الحساب دخل السالب. أوضح إشارة خطر، وكان النظام يعبرها."""
    yms = sorted(df["ym"].unique())
    a.op_months_total = len(yms)
    neg = 0
    for ym in yms:
        oi = float(op_income_df[op_income_df["ym"] == ym]["المبلغ"].sum())
        oe = float(op_expense_df[op_expense_df["ym"] == ym]["المبلغ"].sum())
        if oi - oe < 0:
            neg += 1
    a.neg_op_months = neg

    # وارد غير مُوضّح (نعترف لا نخمّن) — نجمعه للعرض والمطالبة بالتوضيح
    unk = df[(df["النوع"].astype(str).str.contains("دخل", regex=True)) &
             (df["التصنيف"] == "وارد غير مُوضّح (يحتاج توضيح)")]
    if not unk.empty:
        a.unknown_inflows = {"count": int(len(unk)), "total": float(unk["المبلغ"].sum())}

    # الرصيد: نفضّل عمود «الرصيد» الحقيقي من الكشف إن وُجد (أدق)؛ وإلا نعيد بناءه
    # من الافتتاحي + الحركات. (دفتر الاستحقاق لا رصيد بنكي له — نتجاوزه.)
    balances = df.attrs.get("balances")
    explicit_closing = df.attrs.get("closing_balance")
    explicit_min = df.attrs.get("min_balance")
    if explicit_closing is not None:
        a.closing_balance = float(explicit_closing)
        a.min_balance = float(explicit_min) if explicit_min is not None else a.closing_balance
        a.overdraft = bool(a.min_balance < -1.0)
    elif a.opening_balance and not a.is_accrual:
        d = df.sort_values("التاريخ")
        inc_mask = d["النوع"].astype(str).str.contains("دخل|إيراد|مبيع", regex=True)
        signed = d["المبلغ"].where(inc_mask, -d["المبلغ"])
        running = a.opening_balance + signed.cumsum()
        balances = [float(x) for x in running]
        a.min_balance = float(running.min())
        a.closing_balance = float(running.iloc[-1])
        a.overdraft = bool(a.min_balance < -1.0)

    # وسادة الرصيد حركةً بحركة — كان العطل الأخطر: شركة تمرّر الملايين ورصيدها
    # يلامس الصفر كانت تُقرأ «آمنة» لأن (الوارد ≈ الصادر). الرصيد هو الحقيقة.
    if balances and len(balances) >= 10:
        bl = sorted(balances)
        n = len(bl)
        a.median_balance = float(bl[n // 2])
        a.pct_below_5k = sum(1 for b in balances if b < 5000) / n
        a.pct_below_1k = sum(1 for b in balances if b < 1000) / n
        dates = df["التاريخ"].dropna()
        period_days = max(1, (dates.max() - dates.min()).days)
        avg_daily_out = a.total_expense / period_days
        if avg_daily_out > 0:
            a.days_of_cover = a.median_balance / avg_daily_out


# اشتراك خدمة رقمية "صامت" حقيقي: مبلغ صغير، ثابت شهرياً بالضبط، جهة خدمة/برمجيات.
_SUBSCRIPTION_HINT = (r"google|microsoft|zoom|adobe|canva|hosting|استضافة|slack|notion|"
                      r"aws|azure|dropbox|figma|subscription|اشتراك|licens|رخصة|saas|"
                      r"linkedin|mailchimp|zapier|أداة|منصة|تطبيق")


def _detect_recurring(a: Analysis, expense_df):
    """يكشف الاشتراكات الرقمية الصامتة الصغيرة التي يغفل عنها صاحب الشركة.
    ليست: الموردين المتغيّرين، ولا الأساسيات، ولا غير التشغيلي — تلك معروفة ومقصودة.
    الشرط: ثابت شهرياً بدقة + (جهة خدمة رقمية معروفة أو مبلغ صغير جداً ثابت)."""
    if expense_df.empty or len(a.months) < 2:
        return
    n_months = len(a.months)
    min_months = max(2, round(n_months * 0.5))
    # نستبعد غير التشغيلي + الرسوم/الضرائب — ليست "اشتراكات تُلغى"
    skip_cat = extractors.NON_OPERATING | {"رسوم وضرائب", "رسوم بنكية", "رسوم وخدمات بنكية"}
    non_op_mask = expense_df["التصنيف"].isin(skip_cat)
    ex = expense_df[~non_op_mask].copy()
    # نجمّع بالطرف+التصنيف حتى لا نخلط اشتراك "Google Workspace" بإعلان "Google Ads"
    ex["_key"] = ex["الطرف"].astype(str) + " · " + ex["التصنيف"].astype(str)
    recurring = []
    for key, g in ex.groupby("_key"):
        party = str(g["الطرف"].iloc[0])
        by_month = g.groupby("ym")["المبلغ"].sum()
        if len(by_month) < min_months:
            continue
        mean = float(by_month.mean())
        if mean <= 0:
            continue
        cv = float(by_month.std(ddof=0)) / mean if mean else 1.0    # ثبات المبلغ
        blob = " ".join(g["الطرف"].astype(str)) + " " + " ".join(g["البيان"].astype(str))
        is_service = bool(re.search(_SUBSCRIPTION_HINT, blob, re.I))
        # اشتراك حقيقي: ثابت جداً (cv≤0.15) و(جهة خدمة رقمية معروفة أو مبلغ صغير ≤600 ريال).
        # هذا يستبعد الموردين المتغيّرين وكبار المصروفات — ليست "اشتراكات تُلغى".
        if cv <= 0.15 and mean >= 30.0 and (is_service or mean <= 600):
            recurring.append({"party": party, "monthly": mean,
                              "yearly": mean * 12, "months": int(len(by_month))})
    recurring.sort(key=lambda r: r["monthly"], reverse=True)
    a.recurring = recurring[:10]
    a.recurring_yearly = sum(r["yearly"] for r in recurring)


def _compute_scores(a: Analysis):
    """أرقام أبطال — كلها مشتقّة بشفافية من إشارات حقيقية (لا تخمين)."""
    # 1) التوفير الممكن = الالتزامات المتكررة الصامتة القابلة للإلغاء فعلاً (رقم صادق).
    #    ألغينا فبركة «التوفير من القفزات» — القفزة قد تكون سداد قرض/رأسمالي/موسمية، لا هدراً.
    a.total_savings = a.recurring_yearly

    # 2) أيام بقاء السيولة
    if a.runway and a.runway.get("burning"):
        a.survival_days = a.runway["days"]

    # 3) مؤشر الأمان النقدي (0–100) — بتفكيك شفّاف (كل عامل مبرَّر ويُعرض للمستخدم).
    score = 100.0
    bd = []   # [(السبب، النقاط)]
    def hit(reason, pts):
        nonlocal score
        if any(r == reason for r, _ in bd):    # لا نكرر نفس السبب (شفافية بلا حشو)
            return
        score += pts; bd.append((reason, pts))

    # تركّز مصدر وارد حقيقي — نستبعد المصادر العامة (إيداع/عملاء متنوعون) كما في الكشف؛
    # "عملاء متنوعون" تنويع لا تركّز، فلا نعاقب عليه (وإلا ظهر سبب لا يقابله اكتشاف).
    real_src = [(n, amt, sh) for (n, amt, sh) in a.income_by_customer
                if n not in extractors.GENERIC_SOURCES]
    if real_src:
        top = real_src[0][2]
        p = -40 if top >= 0.60 else -28 if top >= 0.45 else -15 if top >= 0.30 else 0
        if p: hit(f"اعتماد على مصدر واحد ({top*100:.0f}%)", p)
    if a.is_accrual and a.collection_rate < 0.5:               # أزمة تحصيل (تتدرّج مع الحدّة)
        p = -25 if a.collection_rate < 0.4 else -15
        hit(f"تحصيل متأخر ({a.collection_rate*100:.0f}% فقط)", p)
    if a.survival_days is not None:                            # احتراق نقدي فعلي
        d = a.survival_days
        p = -35 if d < 30 else -25 if d < 60 else -12 if d < 120 else 0
        if p: hit(f"السيولة تكفي {d:.0f} يوم فقط", p)
    elif a.runway and a.runway.get("burning"):
        hit("النقد يحترق شهرياً", -15)
    # وسادة الرصيد — خصومات إلزامية من عمود الرصيد الحقيقي (كانت الشركة التي يلامس
    # رصيدها 0.26 ريال تُقرأ «88 جيد» لأن الوارد ≈ الصادر — الرصيد هو الحقيقة).
    if a.overdraft:
        hit("الحساب دخل السالب (سحب على المكشوف)", -40)
    elif a.min_balance is not None and a.min_balance < 1000:
        hit(f"الرصيد لامس {a.min_balance:,.2f} ريال", -30)
    if a.pct_below_5k is not None and a.pct_below_5k > 0.40:
        hit(f"الرصيد تحت 5,000 ريال في {a.pct_below_5k*100:.0f}% من الوقت", -20)
    if a.days_of_cover is not None and a.days_of_cover < 7:
        hit(f"وسيط رصيدك يغطي ~{a.days_of_cover:.0f} أيام من الصادر فقط", -25)

    for f in a.findings:
        if f["key"] == "overdraft":                            # عولج أعلاه (خصم الرصيد الإلزامي)
            pass
        elif f["key"] == "operating_bleed":                    # النشاط يخسر معظم الأشهر
            hit(f"نزيف تشغيلي {f['data']['neg']} من {f['data']['total']} أشهر", -20)
        elif f["key"] in ("margin_erosion", "sales_up_profit_down"):
            hit("اتجاه نقدي يتدهور", -12)
        elif f["key"] == "high_payroll":
            hit("عبء رواتب مرتفع", -8)
        elif f["key"] == "large_asset_purchase":
            hit("شراء أصل كبير في وقت ضغط", -5)
        elif f["key"] == "fixed_obligations":
            hit("التزامات ثابتة تفوق النقد الداخل", -7)
        elif f["key"] == "duplicate_payment":
            hit("دفعة مكررة تحتاج تحققاً", -8)
        elif f["key"] == "escalating_payments":
            hit("مدفوعات متصاعدة لجهة واحدة", -10)
        elif f["key"] == "client_vanished":
            hit("عميل منتظم توقّف", -6)
        elif f["key"] == "client_paying_partial":
            hit("عميل رئيسي بدأ يدفع جزئياً", -12)
        elif f["key"] == "penalties":
            hit("غرامات قابلة للتفادي", -4)
        elif f["key"] == "recurring_crisis" or (f["key"] == "receivables_crisis" and not a.is_accrual):
            pass
    if a.recurring:
        hit(f"اشتراكات صامتة ({len(a.recurring)})", -3)
    if a.buffer_months and a.buffer_months >= 3:              # وسادة نقدية إيجابية
        hit("وسادة نقدية جيدة", +8)
    a.safety_score = int(max(5, min(99, round(score))))
    a.score_breakdown = bd
    a.safety_band = ("high_risk" if a.safety_score < 45
                     else "medium" if a.safety_score < 75 else "good")


# بنود «مرافق/فواتير» — فاتورة المرفق تتكرر شهرياً، وتكرارها اليومي خطأ بيانات شبه مؤكد
_UTILITY_RE = r"كهرب|مرافق|مياه|اتصالات|فاتورة|SEC|electric|utility"


def _sanity_checks(a: Analysis, df, income_df, expense_df):
    """فحوصات سلامة البيانات — تعمل قبل التحليل وتُعرض في صندوق منفصل أعلى التقرير.
    العملاء الحقيقيون يرفعون ملفات معيبة يومياً؛ نظامٌ يقول «بياناتك فيها خلل»
    أوثق من نظامٍ يحلّلها بثقة زائفة. (ميزة بيعية لا تحفّظ.)"""
    notes = []
    n_months = max(1, len(df["ym"].unique()))

    if not expense_df.empty:
        # 1) فاتورة مرفق تتكرر يومياً (>15 لنفس الجهة في شهر واحد) = خطأ بيانات شبه مؤكد
        util = expense_df[expense_df["التصنيف"].astype(str).str.contains(_UTILITY_RE, regex=True, case=False, na=False)
                          | expense_df["البيان"].astype(str).str.contains(_UTILITY_RE, regex=True, case=False, na=False)]
        if not util.empty:
            cnt = util.groupby(["الطرف", "ym"]).size()
            for (vendor, ym), n in cnt.items():
                if n > 15:
                    total = float(util[(util["الطرف"] == vendor) & (util["ym"] == ym)]["المبلغ"].sum())
                    notes.append({"key": "utility_daily",
                                  "data": {"vendor": str(vendor), "n": int(n), "ym": ym, "total": total}})
                    break                                    # ملاحظة واحدة تكفي للتنبيه

        # 2) بند مصروف يتجاوز 30% من الدخل — تحقق من صحته
        for cat, amt, _sh in a.expense_by_category:
            if a.total_income > 0 and amt > 0.30 * a.total_income and amt >= 10000:
                notes.append({"key": "category_dominant",
                              "data": {"cat": cat, "amount": amt,
                                       "pct": amt / a.total_income}})
                break

        # 3) فئة معتبرة تظهر في أقل من نصف الأشهر — ناقصة أم موسمية؟
        if n_months >= 6:
            for cat, amt, sh in a.expense_by_category:
                if sh < 0.05:
                    continue
                m_present = expense_df[expense_df["التصنيف"] == cat]["ym"].nunique()
                if m_present < n_months * 0.5:
                    notes.append({"key": "gap_pattern",
                                  "data": {"cat": cat, "m": int(m_present), "total": n_months}})
                    break

    a.data_quality = notes


def _detect_findings(a: Analysis, income_df, expense_df):
    """كشف المخاطر المخفية — بيانات فقط, بلا نصوص لغوية."""
    findings = []
    n_months = max(1, len(a.months))

    # 00) السحب على المكشوف — الرصيد دخل السالب فعلاً (أخطر إشارة في كشف، وكان يُعبَر).
    #     الدرس: الرصيد الموجب فترةً بفضل القرض يخدع؛ الحقيقة أن الحساب انكشف.
    if a.overdraft and a.closing_balance is not None:
        findings.append({
            "key": "overdraft", "severity": "high",
            "data": {"closing": a.closing_balance, "min": a.min_balance, "opening": a.opening_balance},
            "sar": None, "timeframe": None,
        })

    # 00-أ) وسادة الرصيد — شركة تمرّر الملايين ورصيدها يلامس الصفر تعيش بلا وسادة:
    #      أي تأخر تحصيل ليوم واحد يعني ارتداد مدفوعات. (الوارد ≈ الصادر ≠ أمان.)
    if a.pct_below_5k is not None and not a.overdraft:
        thin = ((a.min_balance is not None and a.min_balance < 1000)
                or a.pct_below_5k > 0.40
                or (a.days_of_cover is not None and a.days_of_cover < 7))
        if thin:
            findings.append({
                "key": "cash_buffer_risk", "severity": "high",
                "data": {"min": a.min_balance, "median": a.median_balance,
                         "closing": a.closing_balance, "pct_5k": a.pct_below_5k,
                         "pct_1k": a.pct_below_1k, "cover": a.days_of_cover},
                "sar": None, "timeframe": None,
            })

    # 00ب) نزيف تشغيلي متكرر — التدفق التشغيلي سالب في معظم الأشهر (النشاط نفسه يخسر).
    if a.op_months_total >= 4 and a.neg_op_months >= max(3, round(a.op_months_total * 0.6)):
        findings.append({
            "key": "operating_bleed", "severity": "high",
            "data": {"neg": a.neg_op_months, "total": a.op_months_total},
            "sar": None, "timeframe": None,
        })

    # 00ج) وارد غير مُوضّح — نعترف ونطلب التوضيح بدل التخمين بثقة (ميزة ثقة، لا ضعف).
    if a.unknown_inflows.get("count", 0) > 0:
        findings.append({
            "key": "unknown_inflows", "severity": "medium",
            "data": dict(a.unknown_inflows),
            "sar": None, "timeframe": None,
        })

    # 00د) مدفوعات متكررة لأفراد وجهات — حقيقة تُعرض وسؤال يُطرح (لا تُسمّى «رواتب»:
    #      المحرّك لا يعرف إن كانوا موظفين أو عمالة أو موردين — المستخدم يحدّد).
    if a.recurring_payees:
        total = sum(p["total"] for p in a.recurring_payees)
        if total >= max(10000, 0.05 * a.total_expense):
            findings.append({
                "key": "recurring_payees", "severity": "medium",
                "data": {"total": total, "n": len(a.recurring_payees),
                         "share": total / a.total_expense if a.total_expense else 0,
                         "top": [(p["payee"], p["count"]) for p in a.recurring_payees[:3]]},
                "sar": None, "timeframe": None,
            })

    # 0) أزمة التدفق: فواتير كثيرة لكن التحصيل متأخر → ذمم مدينة متراكمة (أخطر رؤية)
    if a.is_accrual and a.receivables > 0:
        sev = "high" if a.collection_rate < 0.4 else "medium"
        findings.append({
            "key": "receivables_crisis", "severity": sev,
            "data": {"invoiced": a.invoiced_total, "collected": a.collected_total,
                     "receivables": a.receivables, "rate": a.collection_rate,
                     "monthly_gap": a.receivables / n_months},
            "sar": a.receivables, "timeframe": "total",
        })

    # 0ب) شراء أصل كبير لمرة واحدة في فترة ضغط سيولة (قرار توقيت)
    #    الأصل = بند رأسمالي لمرة، نُنذر منه إذا كان كبيراً مقارنة بالتدفق الشهري الفعلي
    #    (نستخدم النقد الداخل الحقيقي، لا المصاريف — أدق في وضع أزمة التحصيل).
    _ASSET_RE = (r"أصول|أصل|معدات|أثاث|سيارة|مركبة|عقار|asset|equipment|"
                 r"furniture|vehicle|capex")
    asset_mask = (expense_df["التصنيف"].astype(str).str.contains(_ASSET_RE, regex=True, case=False, na=False)
                  | expense_df["البيان"].astype(str).str.contains(
                      r"شراء\s*(?:سيارة|مركبة|معدات|أثاث|عقار|أصل)", regex=True, case=False, na=False))
    if asset_mask.any():
        assets = expense_df[asset_mask]
        top = assets.sort_values("المبلغ", ascending=False).iloc[0]
        amount = float(top["المبلغ"])
        monthly_cash = (a.total_income / n_months) or a.avg_monthly_expense
        # نُنذر إذا الأصل يفوق نصف شهر من النقد الداخل أو 20 ألف (لمرة، قرار توقيت)
        if amount >= max(20000, 0.5 * monthly_cash):
            party = str(top["الطرف"])
            if party in extractors.GENERIC_SOURCES or party.startswith("أصول"):
                party = str(top["البيان"])[:40]        # الوصف أوضح من تسمية تصنيفية
            findings.append({
                "key": "large_asset_purchase", "severity": "medium",
                "data": {"amount": amount, "party": party,
                         "months_expense": amount / monthly_cash if monthly_cash else 0},
                "sar": None, "timeframe": None,
            })

    # 1) تركّز مصدر وارد حقيقي — نستبعد المصادر العامة (إيداع نقدي/تحويلات/رسوم):
    #    الإيداع النقدي ليس "عميلاً" يُخشى فقدانه، بل مبيعات نقدية. لا ننذر خطأً.
    real_sources = [(n, amt, sh) for (n, amt, sh) in a.income_by_customer
                    if n not in extractors.GENERIC_SOURCES]
    if real_sources:
        name, amt, share = real_sources[0]
        if share >= 0.30:
            data = {"name": name, "share": share, "monthly": amt / n_months}
            # تقدير الخطر بالأيام: لو فقدت هذا المصدر، كم يوماً تصمد السيولة؟
            # (نحتاج الرصيد الحالي + معدل الحرق بعد فقده)
            if a.cash and a.avg_monthly_expense > 0:
                monthly_in_after = (a.total_income / n_months) - (amt / n_months)
                burn_after = a.avg_monthly_expense - monthly_in_after
                if burn_after > 0:
                    data["days_if_lost"] = (a.cash / burn_after) * 30
            findings.append({
                "key": "customer_concentration", "severity": "high",
                "data": data, "sar": amt / n_months, "timeframe": "monthly",
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

    # 4) قفزة في مصروف تسويقي فقط — بند تقديري يستحقّ مراجعة الجدوى.
    #    مبدأ حاسم (طلب المراجع): «القفزة ≠ هدر». معظم القفزات سداد قرض/رأسمالي/موسمية/غرامة
    #    مرة واحدة — لا نفبرك «توفيراً» منها ولا نبني عليها قراراً. نقتصر على التسويق (تقديري
    #    حقيقي)، ونعرضه كـ«راجع الجدوى» لا كـ«ستوفّر X مضمونة». (sar=None ← ليس رافعة قرار.)
    if len(a.months) >= 4:
        early = [m["ym"] for m in a.months[:2]]
        late = [m["ym"] for m in a.months[-2:]]
        mkt_re = r"تسويق|إعلان|marketing|ads|دعاية"
        op_exp = expense_df[~expense_df["التصنيف"].isin(extractors.NON_OPERATING)]
        mkt = op_exp[op_exp["التصنيف"].astype(str).str.contains(mkt_re, regex=True, na=False)]
        for cat in mkt["التصنيف"].astype(str).unique():
            c = mkt[mkt["التصنيف"].astype(str) == cat]
            early_avg = c[c["ym"].isin(early)]["المبلغ"].sum() / 2
            late_avg = c[c["ym"].isin(late)]["المبلغ"].sum() / 2
            if early_avg > 0 and late_avg > early_avg * 1.6:
                findings.append({
                    "key": "marketing_spike", "severity": "low",
                    "data": {"category": cat, "early": early_avg, "late": late_avg,
                             "extra_year": (late_avg - early_avg) * 12},
                    "sar": None, "timeframe": None,
                })

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

    # 6) عبء الرواتب مرتفع (الرواتب تلتهم نسبة كبيرة من حجم النشاط)
    if a.salary_total > 0 and a.salary_ratio >= 0.40:
        findings.append({
            "key": "high_payroll",
            "severity": "high" if a.salary_ratio >= 0.55 else "medium",
            "data": {"ratio": a.salary_ratio, "monthly": a.salary_monthly, "count": a.salary_count},
            "sar": None, "timeframe": None,
        })

    # 7) التزامات نقدية ثابتة مرتفعة مقابل النقد الداخل الفعلي (رواتب+إيجار+قرض)
    #    الجوهر: هذه تُدفع نقداً كل شهر مهما تأخّر التحصيل. لو فاقت النقد الداخل، الخطر مباشر.
    if a.fixed_monthly > 0:
        cash_in_m = a.total_income / n_months
        ratio = a.fixed_monthly / cash_in_m if cash_in_m > 0 else 99.0
        if ratio >= 0.5 or a.fixed_monthly > cash_in_m:
            findings.append({
                "key": "fixed_obligations",
                "severity": "high" if a.fixed_monthly > cash_in_m else "medium",
                "data": {"fixed": a.fixed_monthly, "cash_in": cash_in_m, "ratio": ratio,
                         "salary": a.fixed_components.get("salary", 0.0),
                         "rent": a.fixed_components.get("rent", 0.0),
                         "loan": a.fixed_components.get("loan", 0.0)},
                "sar": None, "timeframe": None,
            })

    # 8) الغرامات والمخالفات — كانت تذوب في «رسوم» فيغيب مبلغ قابل للتفادي كلياً
    pen_mask = (expense_df["التصنيف"].astype(str).str.contains("غرامات", na=False)
                | expense_df["البيان"].astype(str).str.contains(
                    r"غرامة|مخالفة|penalty|late\s*fee", regex=True, case=False, na=False))
    if pen_mask.any():
        pen_total = float(expense_df[pen_mask]["المبلغ"].sum())
        if pen_total >= 1000:
            findings.append({
                "key": "penalties", "severity": "medium",
                "data": {"total": pen_total, "count": int(pen_mask.sum())},
                "sar": None, "timeframe": None,
            })

    # كاشف الحالات الشاذة — «مين يسرقني ووين أنزف»: هذا ما يدفع المستخدم مقابله.
    findings.extend(_detect_anomalies(a, income_df, expense_df))

    # ترتيب المخاطر بالأولوية: عاجل (high) ثم متوسط ثم مراقبة — أهم خطر أولاً (طلب المستثمر).
    _sev = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: _sev.get(f.get("severity"), 3))
    a.findings = findings


def _detect_recurring_payees(a: Analysis, expense_df):
    """مدفوعات متكررة لأفراد وجهات — بديل «تخمين الرواتب» على الكشوف البنكية.
    المحرّك لا يعرف إن كانوا موظفين أو عمالة أو موردين — يعرض الحقيقة ويطلب التوضيح
    (اعترف لا تخمّن). الشرط: ≥6 دفعات عبر ≥4 أشهر لنفس المستفيد المسمّى."""
    cats = {"مدفوعات لأفراد وجهات", "تحويل", "حوالة صادرة", "تحويلات"}
    ex = expense_df[expense_df["التصنيف"].isin(cats)]
    payees = []
    for party, g in ex.groupby("الطرف"):
        p = str(party)
        if p in extractors.GENERIC_SOURCES or not p.strip():
            continue
        months = set(g["ym"].unique())
        if len(g) >= 6 and len(months) >= 4:
            payees.append({"payee": p, "count": int(len(g)),
                           "months": int(len(months)), "total": float(g["المبلغ"].sum())})
    payees.sort(key=lambda x: -x["total"])
    a.recurring_payees = payees[:20]


def _detect_anomalies(a: Analysis, income_df, expense_df) -> list:
    """شذوذ يستدعي المراجعة: دفعة مكررة، مدفوعات متصاعدة لجهة واحدة، عميل توقّف.
    كلها حتمية وصياغتها «تحقّق» لا «اتهام» — نعرض النمط والمبلغ ونطلب مراجعته."""
    out = []
    non_op = extractors.NON_OPERATING

    # 1) دفعة مكررة: نفس الجهة + نفس المبلغ + خلال ≤7 أيام + مبلغ معتبر (≥5000).
    #    نستثني العلاقات المتكررة (مستفيد يُدفع له باستمرار): دفعات متقاربة له طبيعية،
    #    وليست «فاتورة دُفعت مرتين» — وإلا أغرقنا الكشوف الحقيقية بإنذارات كاذبة.
    frequent = {p["payee"] for p in a.recurring_payees if p["count"] > 12}
    ex = expense_df[~expense_df["التصنيف"].isin(non_op)].sort_values("التاريخ")
    for (party, amt), g in ex.groupby(["الطرف", "المبلغ"]):
        if (len(g) < 2 or amt < 5000 or str(party) in extractors.GENERIC_SOURCES
                or str(party) in frequent):
            continue
        dts = g["التاريخ"].tolist()
        for i in range(len(dts) - 1):
            gap = (dts[i + 1] - dts[i]).days
            if 0 <= gap <= 7:
                out.append({
                    "key": "duplicate_payment", "severity": "high",
                    "data": {"party": str(party), "amount": float(amt), "days": gap,
                             "date1": dts[i].strftime("%Y-%m-%d"),
                             "date2": dts[i + 1].strftime("%Y-%m-%d")},
                    "sar": float(amt), "timeframe": "total",
                })
                break

    # 2) مدفوعات متصاعدة لجهة واحدة: ≥4 دفعات، كل دفعة أكبر من سابقتها، والأخيرة ≥2.5× الأولى
    ex_named = ex[~ex["التصنيف"].astype(str).str.contains(_SALARY_RE, regex=True, case=False)]
    for party, g in ex_named.groupby("الطرف"):
        if str(party) in extractors.GENERIC_SOURCES or len(g) < 4:
            continue
        amts = g.sort_values("التاريخ")["المبلغ"].tolist()
        increasing = all(b > a_ for a_, b in zip(amts, amts[1:]))
        if increasing and amts[0] > 0 and amts[-1] >= amts[0] * 2.5 and sum(amts) >= 20000:
            out.append({
                "key": "escalating_payments", "severity": "high",
                "data": {"party": str(party), "n": len(amts), "first": float(amts[0]),
                         "last": float(amts[-1]), "total": float(sum(amts))},
                "sar": None, "timeframe": None,
            })

    # 3ب) عميل بدأ يدفع جزئياً — أخطر إشارة مبكرة لفقدان أكبر عميل (طلب أبو فيصل):
    #     ظهور «دفعة جزئية/partial» من مصدر منتظم في آخر شهرين، ولم تظهر منه من قبل.
    inc_all = income_df[~income_df["التصنيف"].isin(non_op)]
    if not inc_all.empty and len(a.months) >= 4:
        last2 = {m["ym"] for m in a.months[-2:]}
        part_mask = inc_all["البيان"].astype(str).str.contains(
            r"جزئي|دفعة\s*جزئية|partial", regex=True, case=False, na=False)
        for party, g in inc_all[part_mask].groupby("الطرف"):
            p = str(party)
            if p in extractors.GENERIC_SOURCES:
                continue
            recent_partials = g[g["ym"].isin(last2)]
            old_partials = g[~g["ym"].isin(last2)]
            hist = inc_all[(inc_all["الطرف"] == p) & ~part_mask]
            if recent_partials.empty or not old_partials.empty or hist.empty:
                continue                       # نمط جديد في آخر شهرين فقط — وإلا فليس تحوّلاً
            hist_monthly = float(hist["المبلغ"].sum()) / max(1, hist["ym"].nunique())
            partial_total = float(recent_partials["المبلغ"].sum())
            if hist_monthly >= 10000:
                out.append({
                    "key": "client_paying_partial", "severity": "high",
                    "data": {"party": p, "partial_total": partial_total,
                             "n_partials": int(len(recent_partials)),
                             "usual_monthly": hist_monthly},
                    "sar": None, "timeframe": None,
                })

    # 3) عميل توقّف: مصدر دخل تشغيلي منتظم (≥4 أشهر) اختفى في آخر شهرين من الفترة
    inc = income_df[~income_df["التصنيف"].isin(non_op)]
    if not inc.empty and len(a.months) >= 6:
        end = inc["التاريخ"].max()
        last_yms = {m["ym"] for m in a.months[-2:]}
        for party, g in inc.groupby("الطرف"):
            if str(party) in extractors.GENERIC_SOURCES:
                continue
            yms = set(g["ym"].unique())
            monthly_avg = float(g["المبلغ"].sum()) / max(1, len(yms))
            if len(yms) >= 4 and monthly_avg >= 5000 and not (yms & last_yms):
                last_seen = g["التاريخ"].max()
                gap_days = (end - last_seen).days
                if gap_days >= 55:
                    out.append({
                        "key": "client_vanished", "severity": "medium",
                        "data": {"party": str(party), "monthly": monthly_avg,
                                 "last_seen": last_seen.strftime("%Y-%m"),
                                 "months_active": len(yms)},
                        "sar": None, "timeframe": None,
                    })
    return out


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
        # نوع القرار يحدّد الصياغة: تركّز العملاء = حماية دخل مهدَّد؛
        # أزمة تحصيل = تحرير نقد عالق (ليس توفيراً)؛ غيرهما = توفير مباشر.
        kind = ("protect" if top["key"] == "customer_concentration"
                else "collect" if top["key"] == "receivables_crisis"
                else "recover" if top["key"] == "duplicate_payment"
                else "save")
        a.decision = {"sar": top["sar"], "timeframe": top["timeframe"], "finding": top, "kind": kind}

    recs = []
    # الأخطر أولاً: حساب مكشوف أو نزيف تشغيلي متكرر — يتقدّم على كل شيء.
    if a.overdraft or (a.op_months_total >= 4 and
                       a.neg_op_months >= max(3, round(a.op_months_total * 0.6))):
        recs.append({"key": "act_stop_bleed",
                     "data": {"neg": a.neg_op_months, "total": a.op_months_total,
                              "closing": a.closing_balance, "overdraft": a.overdraft}})
    # الجذر: أزمة التحصيل هي سبب شحّ النقد — ملاحقة التحصيل تعالج السبب لا العرض.
    rc = next((f for f in a.findings if f["key"] == "receivables_crisis"), None)
    if rc:
        recs.append({"key": "act_chase_collections",
                     "data": {"receivables": rc["data"]["receivables"], "rate": rc["data"]["rate"]}})
    # السيولة ثانياً — وقف النزيف النقدي
    if a.runway and a.runway.get("burning"):
        recs.append({"key": "act_cut_burn", "data": {"burn": a.runway["burn"]}})

    # أفعال مشتقّة من الروافع (لكل خطر فعلٌ مسعّر بهدف رقمي محدّد)
    n = max(1, len(a.months))
    for f in levers:
        if f["key"] == "customer_concentration" and a.income_by_customer:
            top_amt = a.income_by_customer[0][1]                # إجمالي دخل أكبر عميل
            # الدخل الجديد المطلوب لتنزيل حصته تحت 50%:  top/(op+N) < 0.5 → N > 2·top − op
            # (نحسبها من الإيراد التشغيلي — الإجمالي الخام المنتفخ بالتمويل يعطي «أضف 0»)
            base_income = a.operating_income or a.total_income
            need_monthly = max(0.0, (2 * top_amt - base_income)) / n
            # «أضف ~0 ريال» باگ ظاهر — لو الهدف صفر/سالب نصيغ الفعل بلا رقم مكسور
            recs.append({"key": "act_diversify",
                         "data": {"share": f["data"]["share"],
                                  "monthly_new": need_monthly if need_monthly >= 100 else None}})
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


def _build_risk_chain(a: Analysis, expense_df):
    """محرك العلاقات المالية — يربط الإشارات في سلسلة سبب→نتيجة واحدة بدل نقاط منفصلة.
    لا يخترع شيئاً: كل حلقة رقم حقيقي مشتقّ من الكشف. هذا ما يحوّل «قارئ كشف»
    إلى «مستشار» يفهم الشركة (الفرق الذي طلبه المستثمر)."""
    chain = []
    n = max(1, len(a.months))
    cash_in_m = a.total_income / n

    # 1) سلسلة عصر السيولة: مبيعات آجلة كبيرة + تحصيل ضعيف + التزامات ثابتة تُدفع نقداً.
    #    النتيجة الحتمية: النقد الداخل لا يغطّي الالتزامات، فتحترق السيولة.
    if a.is_accrual and a.collection_rate < 0.6 and a.fixed_monthly > 0:
        chain.append({
            "kind": "accrual_squeeze",
            "data": {
                "invoiced": a.invoiced_total, "collected": a.collected_total,
                "rate": a.collection_rate, "receivables": a.receivables,
                "cash_in_m": cash_in_m, "fixed_m": a.fixed_monthly,
                "salary": a.fixed_components.get("salary", 0.0),
                "rent": a.fixed_components.get("rent", 0.0),
                "loan": a.fixed_components.get("loan", 0.0),
                "gap_m": a.fixed_monthly - cash_in_m,
                "survival_days": a.survival_days,
            },
        })

    # 2) سلسلة تركّز مصدر واحد + احتراق: فقد المصدر يُنهي السيولة خلال أيام معدودة.
    real_src = [(nm, amt, sh) for (nm, amt, sh) in a.income_by_customer
                if nm not in extractors.GENERIC_SOURCES]
    if real_src and real_src[0][2] >= 0.30:
        nm, amt, sh = real_src[0]
        days = next((f["data"].get("days_if_lost") for f in a.findings
                     if f["key"] == "customer_concentration"), None)
        chain.append({
            "kind": "concentration_burn",
            "data": {"name": nm, "share": sh, "monthly": amt / n, "days_if_lost": days},
        })

    a.risk_chain = chain
