from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)

OUT = Path("docs/Md_Nafim_Alam_Professional_Resume.pdf")

DARK = colors.HexColor("#181818")
MUTED = colors.HexColor("#555555")
ACCENT = colors.HexColor("#8F2027")
LINE = colors.HexColor("#D8DADD")
LINK = colors.HexColor("#1A5FB4")

doc = SimpleDocTemplate(
    str(OUT),
    pagesize=letter,
    rightMargin=0.52*inch,
    leftMargin=0.52*inch,
    topMargin=0.40*inch,
    bottomMargin=0.40*inch,
)

styles = {
    "name": ParagraphStyle(
        "name", fontName="Helvetica-Bold", fontSize=18, leading=20,
        textColor=DARK, alignment=TA_CENTER, spaceAfter=2
    ),
    "subtitle": ParagraphStyle(
        "subtitle", fontName="Helvetica-Bold", fontSize=9.5, leading=11,
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=3
    ),
    "contact": ParagraphStyle(
        "contact", fontName="Helvetica", fontSize=8.5, leading=10,
        textColor=LINK, alignment=TA_CENTER, spaceAfter=3
    ),
    "section": ParagraphStyle(
        "section", fontName="Helvetica-Bold", fontSize=10, leading=11,
        textColor=ACCENT, spaceBefore=4, spaceAfter=2
    ),
    "body": ParagraphStyle(
        "body", fontName="Helvetica", fontSize=9.0, leading=10.6,
        textColor=DARK, spaceAfter=1
    ),
    "small": ParagraphStyle(
        "small", fontName="Helvetica", fontSize=8.4, leading=9.6,
        textColor=DARK, spaceAfter=0
    ),
    "role": ParagraphStyle(
        "role", fontName="Helvetica-Bold", fontSize=9.4, leading=10.5,
        textColor=DARK, spaceAfter=0
    ),
    "bullet": ParagraphStyle(
        "bullet", fontName="Helvetica", fontSize=8.8, leading=10.2,
        textColor=DARK, leftIndent=9, firstLineIndent=-7, spaceAfter=1
    ),
}

def section(title):
    t = Table([[Paragraph(title.upper(), styles["section"])]], colWidths=[7.45*inch])
    t.setStyle(TableStyle([
        ("LINEBELOW",(0,0),(-1,-1),0.6,LINE),
        ("BOTTOMPADDING",(0,0),(-1,-1),1),
        ("TOPPADDING",(0,0),(-1,-1),0),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    return t

def bullet(text):
    return Paragraph("&#8226; " + text, styles["bullet"])

story = [
    Paragraph("Md Nafim Alam", styles["name"]),
    Paragraph("Information Systems & Analytics | Business Analytics | Data & Technology", styles["subtitle"]),
    Paragraph(
        '<link href="mailto:mdnafimalam@gmail.com">mdnafimalam@gmail.com</link>'
        ' &nbsp;|&nbsp; '
        '<link href="https://mdnafimalam.github.io/mdnafimalam/">Portfolio</link>'
        ' &nbsp;|&nbsp; '
        '<link href="https://www.linkedin.com/in/md-nafim-alam-129624404/">LinkedIn</link>'
        ' &nbsp;|&nbsp; '
        '<link href="https://github.com/mdnafimalam">GitHub</link>',
        styles["contact"]
    ),

    section("Professional Summary"),
    Paragraph(
        "Management Information Systems student at Emporia State University with hands-on experience "
        "building analytics applications using SQL, Python, SQLite, Pandas, Streamlit, and GitHub Actions. "
        "Combines technical project work with front-of-house leadership experience in team coordination, "
        "customer service, operations, and day-to-day problem solving.",
        styles["body"]
    ),

    section("Technical Skills"),
]

skill_data = [
    [
        Paragraph("<b>Data & Analytics:</b> SQL, SQLite, Pandas, KPI analysis, aggregations, trend analysis", styles["small"]),
        Paragraph("<b>Development:</b> Python, Streamlit, modular application structure, GitHub", styles["small"]),
    ],
    [
        Paragraph("<b>Databases:</b> Relational design, normalization, joins, subqueries, views", styles["small"]),
        Paragraph("<b>Testing & Quality:</b> Unit tests, integration tests, data validation, GitHub Actions", styles["small"]),
    ],
    [
        Paragraph("<b>Information Systems:</b> Business processes, systems thinking, operational analysis", styles["small"]),
        Paragraph("<b>Security Foundations:</b> HTTPS/TLS, session security, CSRF, firewalls, Linux permissions", styles["small"]),
    ],
]
skill_table = Table(skill_data, colWidths=[3.72*inch,3.72*inch])
skill_table.setStyle(TableStyle([
    ("VALIGN",(0,0),(-1,-1),"TOP"),
    ("LEFTPADDING",(0,0),(-1,-1),0),
    ("RIGHTPADDING",(0,0),(-1,-1),8),
    ("TOPPADDING",(0,0),(-1,-1),1),
    ("BOTTOMPADDING",(0,0),(-1,-1),2),
]))
story.append(skill_table)

story += [
    section("Selected Projects"),
    Paragraph("Retail Intelligence - SQL Business Analytics Dashboard", styles["role"]),
    Paragraph("SQL | Python | SQLite | Pandas | Streamlit | GitHub Actions", styles["small"]),
    bullet("Built a live retail analytics application covering revenue, customer behavior, product performance, regional trends, KPI reporting, and data-quality checks."),
    bullet("Used a normalized SQLite model, SQL reporting, a Pandas analytics layer, automated tests, GitHub Actions, and CSV export to support repeatable analysis."),
    Spacer(1,2),
    Paragraph("SignalScope - Pattern Intelligence", styles["role"]),
    Paragraph("Python | Streamlit | Plotly | Validation | Explainable Analytics", styles["small"]),
    bullet("Developed a privacy-aware analytics application for repeated communication activity using pseudonymized metadata, temporal analysis, and explainable source-level scoring."),
    bullet("Implemented global filters, weekday-by-hour heatmaps, source drilldowns, data-quality review, CSV export, and automated test coverage with CI."),

    section("Experience"),
    Paragraph("Front-of-House Lead / Supervisor | Fresh Ideas Management, Emporia State University | June 2024 - Present", styles["role"]),
    bullet("Support front-of-house operations, team coordination, customer service, and day-to-day operational problem solving in a university environment."),
    bullet("Build practical leadership, communication, and service-management experience while supporting consistent daily execution."),
    Spacer(1,2),
    Paragraph("Management Intern | Fresh Ideas Management, Emporia State University | August 2025 - December 2025", styles["role"]),
    bullet("Gained practical exposure to management, service operations, team coordination, and day-to-day business execution."),

    section("Education"),
    Paragraph("Emporia State University | BSB - Information Systems & Analytics | Expected December 2027", styles["role"]),
    Paragraph("<b>Relevant study:</b> Database systems, information systems, cybersecurity, finance, and quantitative problem solving.", styles["small"]),

]

doc.build(story)
print(OUT)
