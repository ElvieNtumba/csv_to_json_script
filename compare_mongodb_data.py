from pymongo import MongoClient
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import json

# --- CONFIGURATION ---
DB1_URI = "mongodb+srv://activeteams:helloactiveteams@active-teams.ykghvqr.mongodb.net/"
DB1_NAME = "testing-data-active-teams"
DB2_NAME = "old-active-teams-data"
COLLECTION_TO_COMPARE = "people"
PDF_FILENAME = "comparison_report_exact.pdf"

# --- PEOPLE TO COMPARE ---
PEOPLE_TO_COMPARE = [
    {"Name": "Elvie", "Surname": "Ntumba"},
    {"Name": "Miradi", "Surname": "Lumbayi"},
    {"Name": "Sasha-Lee", "Surname": "Enslin"},
    {"Name": "Kayla", "Surname": "Enslin"},
    {"Name": "Blessing", "Surname": "Mbele"},
    {"Name": "Shane", "Surname": "van der Walt"},
    {"Name": "Kenny", "Surname": "Bebel"},
]

# --- CONNECT TO DATABASES ---
client = MongoClient(DB1_URI)
db1 = client[DB1_NAME][COLLECTION_TO_COMPARE]
db2 = client[DB2_NAME][COLLECTION_TO_COMPARE]

# --- HELPER FUNCTIONS ---
def fetch_person_data(db, name, surname):
    person = db.find_one({"Name": name, "Surname": surname})
    if person:
        person.pop("_id", None)
    return person

def format_doc(doc):
    """Nicely format JSON for PDF display"""
    if not doc:
        return "—"
    return json.dumps(doc, indent=2, ensure_ascii=False, default=str).replace("\n", "<br/>")

# --- PDF SETUP ---
styles = getSampleStyleSheet()
doc = SimpleDocTemplate(PDF_FILENAME, pagesize=A4,
                        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
elements = []

elements.append(Paragraph("<b>Database Comparison Report</b>", styles["Title"]))
elements.append(Spacer(1, 16))

# --- GENERATE COMPARISON TABLES ---
for person in PEOPLE_TO_COMPARE:
    name, surname = person["Name"], person["Surname"]
    data1 = fetch_person_data(db1, name, surname)
    data2 = fetch_person_data(db2, name, surname)

    elements.append(Paragraph(f"<b>{name} {surname}</b>", styles["Heading2"]))
    elements.append(Spacer(1, 8))

    if not data1 and not data2:
        elements.append(Paragraph("❌ Not found in either database.", styles["Normal"]))
        elements.append(Spacer(1, 16))
        continue

    # Prepare the two columns (as-is, not aligned by field)
    db1_text = format_doc(data1)
    db2_text = format_doc(data2)

    # Create table with only two columns
    table_data = [
        [f"<b>{DB1_NAME}</b>", f"<b>{DB2_NAME}</b>"],
        [Paragraph(db1_text, styles["Normal"]), Paragraph(db2_text, styles["Normal"])]
    ]

    table = Table(table_data, colWidths=["*", "*"])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

# --- BUILD PDF ---
doc.build(elements)
print(f"✅ Exact comparison report created: {PDF_FILENAME}")
