# report/generator.py
"""
PDF report generation for interview scorecards.

Attempts to use the `reportlab` library when available to produce a
formatted PDF.  Falls back to a plain-text `.txt` file if reportlab is
not installed, so the rest of the application is never blocked by a
missing optional dependency.

Inputs
------
scorecard_dict : dict – the scorecard data (ScorecardOutput.model_dump())
filepath       : str  – destination file path (e.g. "reports/abc123.pdf")
"""

import logging
import os

logger = logging.getLogger("scorecard.report")


def _write_text_fallback(scorecard_dict: dict, filepath: str) -> None:
    """Write a plain-text summary when reportlab is unavailable."""
    txt_path = filepath.replace(".pdf", ".txt") if filepath.endswith(".pdf") else filepath + ".txt"
    os.makedirs(os.path.dirname(txt_path) or ".", exist_ok=True)
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write("AI Interview Scorecard\n")
        fh.write("=" * 40 + "\n")
        fh.write(f"Timestamp  : {scorecard_dict.get('timestamp', 'N/A')}\n")
        fh.write(f"Request ID : {scorecard_dict.get('request_id', 'N/A')}\n")
        fh.write(f"Overall    : {scorecard_dict.get('overall_score', 'N/A')}\n\n")
        fh.write("Metrics\n")
        fh.write("-" * 40 + "\n")
        for dim, detail in scorecard_dict.get("metrics", {}).items():
            fh.write(f"  {dim.capitalize():12s}: {detail.get('score', 'N/A'):>5}  |  {detail.get('insights', '')}\n")
        fh.write("\nSuggestions\n")
        fh.write("-" * 40 + "\n")
        for i, s in enumerate(scorecard_dict.get("improvement_suggestions", []), 1):
            fh.write(f"  {i}. {s}\n")
    logger.info("Scorecard written to %s (text fallback)", txt_path)


def _write_pdf(scorecard_dict: dict, filepath: str) -> None:
    """Write a formatted PDF using reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("AI Interview Scorecard", styles["Title"]))
    story.append(Spacer(1, 0.4 * cm))

    # Meta
    story.append(Paragraph(f"<b>Timestamp:</b> {scorecard_dict.get('timestamp', 'N/A')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Request ID:</b> {scorecard_dict.get('request_id', 'N/A')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Overall Score:</b> {scorecard_dict.get('overall_score', 'N/A')} / 100", styles["Heading2"]))
    story.append(Spacer(1, 0.4 * cm))

    # Metrics table
    story.append(Paragraph("Dimension Breakdown", styles["Heading3"]))
    table_data = [["Dimension", "Score", "Insights"]]
    for dim, detail in scorecard_dict.get("metrics", {}).items():
        table_data.append([
            dim.capitalize(),
            str(detail.get("score", "")),
            detail.get("insights", ""),
        ])
    tbl = Table(table_data, colWidths=[3.5 * cm, 2 * cm, 11 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f2f2f2"), colors.white]),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("PADDING",     (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.5 * cm))

    # Suggestions
    story.append(Paragraph("Improvement Suggestions", styles["Heading3"]))
    for i, suggestion in enumerate(scorecard_dict.get("improvement_suggestions", []), 1):
        story.append(Paragraph(f"{i}. {suggestion}", styles["Normal"]))
        story.append(Spacer(1, 0.15 * cm))

    doc.build(story)
    logger.info("Scorecard PDF written to %s", filepath)


def generate_pdf(scorecard_dict: dict, filepath: str) -> None:
    """
    Generate a scorecard report at *filepath*.

    Uses reportlab for a formatted PDF when available; silently falls back
    to a plain-text file otherwise.  Errors are logged rather than raised
    so a report failure never crashes the main evaluation endpoint.
    """
    try:
        _write_pdf(scorecard_dict, filepath)
    except ImportError:
        logger.debug("reportlab not installed – falling back to plain-text report")
        try:
            _write_text_fallback(scorecard_dict, filepath)
        except Exception as exc:
            logger.warning("Could not write text fallback report: %s", exc)
    except Exception as exc:
        logger.warning("PDF generation failed: %s", exc)
