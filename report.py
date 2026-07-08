"""
مولّد التقرير — PDF ثنائي اللغة: عربي (RTL) وإنجليزي (LTR).
الأرقام والمفاتيح جاهزة من engine.py، والصياغة من i18n.py.
التخطيط واعٍ بالاتجاه: كل عنصر يُرسم من «الحافة القائدة» (يمين للعربي، يسار للإنجليزي).
"""
from __future__ import annotations
import os
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import i18n

# خطوط عربية مرفقة داخل المشروع (Tajawal) — تعمل على ويندوز ولينكس (Render) معاً.
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
pdfmetrics.registerFont(TTFont("Body", os.path.join(_FONT_DIR, "Tajawal-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Bold", os.path.join(_FONT_DIR, "Tajawal-Bold.ttf")))

NAVY = HexColor("#0F2A43"); GREEN = HexColor("#1D9A6C"); RED = HexColor("#C0392B")
AMBER = HexColor("#E08E0B"); GRAY = HexColor("#6B7A8D"); LIGHT = HexColor("#F4F6F8")
LINE = HexColor("#E1E7ED"); MUTE = HexColor("#AEC2D6"); WHITE = HexColor("#FFFFFF")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
RIGHT = PAGE_W - MARGIN
LEFT = MARGIN
COLW = RIGHT - LEFT


def _shape(s):  # تشكيل عربي + bidi (آمن للاتيني — يتركه كما هو)
    return get_display(arabic_reshaper.reshape(str(s)))


class Report:
    def __init__(self, path, company, lang="ar"):
        self.lang = i18n.norm_lang(lang)
        self.rtl = self.lang == "ar"
        self.R = i18n.REPORT[self.lang]
        self.company = company
        self.c = canvas.Canvas(path, pagesize=A4)
        self.c.setTitle(self.R["brand"])
        self.y = PAGE_H - MARGIN

    # ---------- إحداثيات واعية بالاتجاه ----------
    def lead_x(self, off=0):   # الحافة القائدة
        return (RIGHT - off) if self.rtl else (LEFT + off)

    def trail_x(self, off=0):  # الحافة الخلفية
        return (LEFT + off) if self.rtl else (RIGHT - off)

    def lead_text(self, text, size=11, font="Body", color=NAVY, off=0, dy=0):
        self.c.setFont(font, size); self.c.setFillColor(color)
        s = _shape(text)
        if self.rtl:
            self.c.drawRightString(RIGHT - off, self.y - dy, s)
        else:
            self.c.drawString(LEFT + off, self.y - dy, s)

    def trail_text(self, text, size=9, font="Body", color=GRAY, off=0, dy=0):
        self.c.setFont(font, size); self.c.setFillColor(color)
        s = _shape(text)
        if self.rtl:
            self.c.drawString(LEFT + off, self.y - dy, s)
        else:
            self.c.drawRightString(RIGHT - off, self.y - dy, s)

    def wrap(self, text, font, size, max_w):
        words = str(text).split()
        lines, cur = [], ""
        for w in words:
            cand = (cur + " " + w).strip()
            if self.c.stringWidth(_shape(cand), font, size) <= max_w or not cur:
                cur = cand
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        return lines

    def para(self, text, size=11, font="Body", color=NAVY, off=0, leading=6, gap=3):
        for line in self.wrap(text, font, size, COLW - off):
            self.lead_text(line, size, font, color, off=off)
            self.y -= size + leading
        self.y -= gap

    def space(self, n=6): self.y -= n

    def need(self, h):
        if self.y - h < MARGIN:
            self.c.showPage(); self.y = PAGE_H - MARGIN

    def hline(self):
        self.c.setStrokeColor(LINE); self.c.setLineWidth(0.6)
        self.c.line(LEFT, self.y, RIGHT, self.y); self.y -= 8

    def section_title(self, text, color=NAVY):
        self.need(30); self.space(2)
        self.c.setFillColor(color)
        bx = (RIGHT - 4) if self.rtl else LEFT
        self.c.rect(bx, self.y - 14, 4, 18, fill=1, stroke=0)
        self.lead_text(text, 15, "Bold", color, off=10, dy=11)
        self.y -= 22

    def chip(self, text, color):
        self.c.setFont("Bold", 9)
        w = self.c.stringWidth(_shape(text), "Bold", 9) + 16
        x = (RIGHT - w) if self.rtl else LEFT
        self.c.setFillColor(color)
        self.c.roundRect(x, self.y - 4, w, 16, 8, fill=1, stroke=0)
        self.c.setFillColor(WHITE)
        if self.rtl:
            self.c.drawRightString(RIGHT - 8, self.y, _shape(text))
        else:
            self.c.drawString(LEFT + 8, self.y, _shape(text))

    def bar(self, label, value, share, color, label_w=175, value_w=95):
        self.need(24)
        y = self.y
        self.lead_text(label, 10, "Body", NAVY, off=0)
        track_lead = self.lead_x(label_w)
        track_trail = self.trail_x(value_w)
        x0 = min(track_lead, track_trail)
        tw = abs(track_trail - track_lead)
        self.c.setFillColor(LIGHT); self.c.roundRect(x0, y - 2, tw, 11, 3, fill=1, stroke=0)
        fw = max(2, tw * max(0.0, min(1.0, share)))
        fx = (track_lead - fw) if self.rtl else track_lead
        self.c.setFillColor(color); self.c.roundRect(fx, y - 2, fw, 11, 3, fill=1, stroke=0)
        self.trail_text(f"{value:,.0f} ({share*100:.0f}%)", 9, "Body", GRAY, off=0)
        self.y -= 22

    # ---------- الصفحات ----------
    def cover(self, a):
        c = self.c
        c.setFillColor(NAVY); c.rect(0, PAGE_H - 46 * mm, PAGE_W, 46 * mm, fill=1, stroke=0)
        self.y = PAGE_H - 20 * mm
        self.lead_text(self.R["brand"], 24, "Bold", WHITE)
        self.y -= 26
        plabel = i18n.period_label(a.first_ym, a.last_ym, self.lang)
        self.lead_text(f"{self.R['report_of']} {self.company} · {self.R['period']} {plabel}",
                       11, "Body", MUTE)
        self.y = PAGE_H - 62 * mm

        if a.decision:
            box_h = 60 * mm
            c.setFillColor(LIGHT); c.roundRect(LEFT, self.y - box_h, COLW, box_h, 10, fill=1, stroke=0)
            top = self.y - 14; self.y = top
            self.lead_text(self.R["decision_kicker"], 13, "Bold", GREEN, off=12, dy=6)
            self.y -= 26
            head = i18n.decision_headline(a.decision["sar"], a.decision["timeframe"], self.lang,
                                          a.decision.get("kind", "save"))
            for line in self.wrap(head, "Bold", 19, COLW - 24):
                self.lead_text(line, 19, "Bold", NAVY, off=12); self.y -= 27
            self.y -= 6
            detail = i18n.finding_text(a.decision["finding"], self.lang)
            for line in self.wrap(detail, "Body", 12, COLW - 24):
                self.lead_text(line, 12, "Body", GRAY, off=12); self.y -= 19
            self.y = top - box_h + 4

        self.space(26)
        self.lead_text(self.R["flip"], 10, "Body", GRAY)
        c.showPage(); self.y = PAGE_H - MARGIN

    def hero_stats(self, a):
        """شريط أرقام أبطال: مؤشر الأمان · ساعة البقاء · التوفير الممكن."""
        band_col = {"good": GREEN, "medium": AMBER, "high_risk": RED}[a.safety_band]
        items = [(f"{a.safety_score} {self.R['of100']}",
                  f"{self.R['safety']} · {i18n.safety_label(a.safety_band, self.lang)}", band_col)]
        if a.survival_days is not None:
            items.append((f"~{a.survival_days:.0f} {self.R['days']}", self.R["survival"], RED))
        if a.total_savings > 0:
            items.append((i18n.money(a.total_savings, self.lang), self.R["savings"], GREEN))

        n = len(items); gap = 10
        bw = (COLW - gap * (n - 1)) / n
        bh = 50
        self.need(bh + 8)
        top = self.y
        for i, (val, lab, col) in enumerate(items):
            x = LEFT + i * (bw + gap)
            cx = x + bw / 2
            self.c.setFillColor(LIGHT); self.c.roundRect(x, top - bh, bw, bh, 8, fill=1, stroke=0)
            self.c.setFillColor(col); self.c.setFont("Bold", 19)
            self.c.drawCentredString(cx, top - 24, _shape(val))
            self.c.setFillColor(GRAY); self.c.setFont("Body", 8.5)
            self.c.drawCentredString(cx, top - 40, _shape(lab))
        self.y = top - bh - 12

    def overview(self, a):
        self.hero_stats(a)
        self.section_title(self.R["overview"])
        # شارة الحالة تتبع مؤشر الأمان (قصة واحدة متماسكة — لا "صحي" فوق مخاطر)
        band_txt = {"good": self.R["healthy"], "medium": self.R["caution"],
                    "high_risk": self.R["risk"]}[a.safety_band]
        band_col = {"good": GREEN, "medium": AMBER, "high_risk": RED}[a.safety_band]
        self.chip(band_txt, band_col)
        self.y -= 22
        self.para(i18n.summary_sentence(a, self.lang), size=11)
        # وسادة الأمان (نقطة التعادل) — تمييز دائم الظهور
        if a.breakeven_drop_pct is not None:
            cush_col = (GREEN if a.breakeven_drop_pct >= 0.30
                        else AMBER if a.breakeven_drop_pct >= 0.20 else RED)
            self.para(i18n.resilience_sentence(a, self.lang), size=11, color=cush_col)
        # شهور تغطية السيولة — بلون يعكس رقّتها (أقل من شهرين = تحذير)
        if a.buffer_months is not None:
            buf_col = (RED if a.buffer_months < 1 else AMBER if a.buffer_months < 2 else NAVY)
            self.para(i18n.buffer_sentence(a, self.lang), size=11, color=buf_col)
        if a.runway and a.runway.get("known") and a.runway.get("burning"):
            self.space(4)
            self.chip(self.R["cash_warn"], RED); self.y -= 22
            self.para(i18n.runway_sentence(a.runway, self.lang), size=11)
        self.hline()

    def earn_bleed(self, a):
        if a.income_by_customer:
            self.section_title(self.R["earn"], GREEN)
            for name, amt, share in a.income_by_customer[:5]:
                self.bar(name, amt, share, GREEN)
            self.space(6)
        if a.expense_by_category:
            self.section_title(self.R["bleed"], RED)
            for cat, amt, share in a.expense_by_category[:5]:
                self.bar(cat, amt, share, RED)
        self.hline()

    def payroll_recurring(self, a):
        """قراءة الرواتب + الالتزامات المتكررة الصامتة — مستخرجة من الكشف الخام (تمييزنا)."""
        if a.salary_total <= 0 and not a.recurring:
            return
        if a.salary_total > 0:
            self.section_title(self.R["payroll"], NAVY)
            ratio_col = (RED if a.salary_ratio >= 0.55 else AMBER if a.salary_ratio >= 0.40 else NAVY)
            self.para(i18n.salary_sentence(a, self.lang), size=11, color=ratio_col)
            self.space(2)
        if a.recurring:
            self.section_title(self.R["recurring"], AMBER)
            self.para(i18n.recurring_sentence(a, self.lang), size=10.5, color=NAVY, gap=2)
            for r in a.recurring[:5]:
                self.bar(r["party"], r["yearly"], min(1.0, r["yearly"] / max(a.recurring_yearly, 1)),
                         AMBER)
        self.hline()

    def risks(self, a):
        if not a.findings:
            return
        self.section_title(self.R["risks"], AMBER)
        for f in a.findings:
            self.need(30)
            col = RED if f["severity"] == "high" else AMBER
            self.chip(i18n.finding_title(f, self.lang), col); self.y -= 19
            self.para(i18n.finding_text(f, self.lang), size=10.5, leading=5, gap=1)
        self.hline()

    def todo(self, a):
        if not a.recommendations:
            return
        self.section_title(self.R["todo"])
        for i, item in enumerate(a.recommendations, 1):
            self.need(28)
            cx = self.lead_x(8)
            self.c.setFillColor(NAVY); self.c.circle(cx, self.y + 4, 9, fill=1, stroke=0)
            self.c.setFillColor(WHITE); self.c.setFont("Bold", 11)
            self.c.drawCentredString(cx, self.y, str(i))
            for line in self.wrap(i18n.rec_text(item, self.lang), "Body", 11, COLW - 30):
                self.lead_text(line, 11, "Body", NAVY, off=26); self.y -= 18
            self.space(6)
        if a.total_savings > 0:
            self.space(2)
            for line in self.wrap(i18n.savings_sentence(a.total_savings, self.lang), "Bold", 12, COLW):
                self.lead_text(line, 12, "Bold", GREEN); self.y -= 18

    def footer(self):
        self.space(10); self.hline()
        self.para(self.R["footer"], size=8.5, color=GRAY)

    def build(self, a):
        self.cover(a); self.overview(a); self.earn_bleed(a)
        self.payroll_recurring(a); self.risks(a); self.todo(a); self.footer()
        self.c.save()


def generate(analysis, path, company="", lang="ar"):
    company = company or i18n.REPORT[i18n.norm_lang(lang)]["brand"]
    Report(path, company, lang).build(analysis)
    return path
