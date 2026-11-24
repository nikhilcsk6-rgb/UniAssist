"""PDF export (ReportLab). For Kannada/Hindi text set PDF_FONT_PATH to a Unicode TTF
(e.g. Noto Sans Kannada / Noto Sans Devanagari); the default Helvetica only covers Latin text."""
import io
import os
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0B1F4B")


def _font():
    path = os.getenv("PDF_FONT_PATH")
    if path and os.path.exists(path):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("UniFont", path))
        return "UniFont"
    return "Helvetica"


def _styles():
    f = _font()
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=ss["Title"], fontName=f, textColor=NAVY, fontSize=18),
        "h": ParagraphStyle("h", parent=ss["Heading2"], fontName=f, textColor=NAVY, fontSize=13),
        "body": ParagraphStyle("b", parent=ss["BodyText"], fontName=f, fontSize=10.5, leading=14),
        "ans": ParagraphStyle("a", parent=ss["BodyText"], fontName=f, fontSize=10, leading=13,
                              textColor=colors.HexColor("#4C1D95"), leftIndent=14),
        "font": f,
    }


def _p(text, style):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def question_paper_pdf(title, questions, include_answers=False):
    s, buf = _styles(), io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                            bottomMargin=2 * cm, title=title)
    total = sum(q.get("marks") or 0 for q in questions)
    story = [_p(title, s["title"]), _p(f"Total questions: {len(questions)}    Total marks: {total}", s["body"]),
             Spacer(1, 10)]
    groups = [("mcq", "Section A - Multiple Choice"), ("true_false", "Section B - True or False"),
              ("short", "Section C - Short Answer"), ("long", "Section D - Long Answer")]
    n = 0
    for t, heading in groups:
        qs = [q for q in questions if q["type"] == t]
        if not qs:
            continue
        story.append(_p(heading, s["h"]))
        for q in qs:
            n += 1
            story.append(_p(f"Q{n}. {q['question']}  [{q.get('marks') or 1} mark(s)] ({q['difficulty']})", s["body"]))
            for i, o in enumerate(q.get("options") or []):
                story.append(_p(f"{chr(65 + i)}. {o}", s["body"]))
            if include_answers:
                story.append(_p(f"Answer: {q['answer']}", s["ans"]))
            story.append(Spacer(1, 6))
    doc.build(story)
    return buf.getvalue()


def research_pdf(exp, summary, satisfaction, rows):
    s, buf = _styles(), io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.8 * cm,
                            bottomMargin=1.8 * cm, title=f"Experiment {exp.id}")
    label = "SAMPLE (illustrative) data" if exp.is_sample else "MEASURED results"
    story = [_p("UniAssist - RAG vs Non-RAG Evaluation", s["title"]),
             _p(f"Experiment: {exp.name} | Dataset: {exp.dataset_name} | Model: {exp.llm_model} | "
                f"temperature {exp.temperature} | top-k {exp.top_k} | {label}", s["body"]), Spacer(1, 10)]

    def fmt(v, pct=False, ms=False):
        if v is None:
            return "n/a"
        return f"{v:.0f} ms" if ms else (f"{v * 100:.1f}%" if pct else f"{v:.3f}")

    keys = [("Answer accuracy", "accuracy", 0), ("Response relevance", "relevance", 0),
            ("Hallucination rate", "hallucination_rate", 1), ("Abstention rate", "abstention_rate", 1),
            ("Avg response time", "avg_time_ms", 2), ("Citation accuracy", "citation_accuracy", 1),
            ("Retrieval precision", "retrieval_precision", 1)]
    a, b = summary.get("A_no_rag", {}), summary.get("B_rag", {})
    data = [["Metric", "Model A (no RAG)", "Model B (RAG)"]]
    for label_, k, mode in keys:
        data.append([label_, fmt(a.get(k), mode == 1, mode == 2), fmt(b.get(k), mode == 1, mode == 2)])
    data.append(["User satisfaction (avg rating /5)", "not collected",
                 fmt(satisfaction.get("average_rating")) + f" (n={satisfaction.get('count', 0)})"])
    t = Table(data, colWidths=[7 * cm, 5 * cm, 5 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("FONTNAME", (0, 0), (-1, -1), s["font"]),
                           ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    story += [t, Spacer(1, 12),
              _p(f"Questions evaluated: {a.get('n', 0)}. Accuracy/relevance/hallucination are judged by the same LLM "
                 "against verified reference answers (LLM-as-judge) and should be spot-checked manually.", s["body"])]
    doc.build(story)
    return buf.getvalue()
