"""
Sample PDF Generator

Creates three realistic contract/policy PDFs with embedded risk clauses
for testing the compliance scanning pipeline.

Usage:
    python scripts/generate_sample_pdfs.py
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf(filename: str, title: str, paragraphs: list):
    """Generate a professional-looking PDF from title and paragraph list."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        spaceAfter=20,
        textColor="#1a365d",
    )

    heading_style = ParagraphStyle(
        "DocHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceBefore=15,
        spaceAfter=10,
        textColor="#2b6cb0",
    )

    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        spaceAfter=10,
        textColor="#2d3748",
    )

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))

    for item in paragraphs:
        if item.startswith("### "):
            story.append(Paragraph(item.replace("### ", ""), heading_style))
        else:
            story.append(Paragraph(item, body_style))

    doc.build(story)
    print(f"Generated PDF: {filename}")


def main():
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "sample_documents",
    )
    os.makedirs(output_dir, exist_ok=True)

    # ── 1. HR Policy Document (Low Risk) ─────────────────────────────
    hr_content = [
        "### Section 1: Introduction",
        "Welcome to the company. This Employee Handbook serves as a guide to the general policies, practices, and benefits of our company. All staff are expected to read and comply with these rules.",
        "### Section 2: Working Hours",
        "Our standard office hours are 9:00 AM to 5:00 PM, Monday through Friday. Flex-time options may be negotiated directly with supervisors.",
        "### Section 3: Governing Law",
        "This agreement is governed by the laws of the State of Delaware. Any disputes arising from employment terms shall be handled in accordance with local regulations.",
        "### Section 4: Confidentiality",
        "Each party shall keep all confidential information strictly secret and confidential. Employees must not share corporate code, trade secrets, or client data with unauthorized external parties.",
        "### Section 5: Notifications",
        "All notices under this agreement shall be sent via certified mail. Any amendments to this contract must be made in writing and signed by both parties.",
    ]
    generate_pdf(
        os.path.join(output_dir, "hr_policy.pdf"),
        "Global HR Policies &amp; Guidelines",
        hr_content,
    )

    # ── 2. Vendor Contract (High Risk) ──────────────────────────────
    vendor_content = [
        "### Clause 1: Scope of Work",
        "The Vendor agrees to provide cloud hosting, maintenance, and technical support services as detailed in the attached statement of work.",
        "### Clause 2: Financial Terms",
        "The Customer shall pay all invoices within thirty (30) days of receipt. Delayed payments will accrue a standard interest rate of 1.5% per month.",
        "### Clause 3: Audit Exclusions (High Risk Clause)",
        "The supplier excludes all rights of audit or inspections by the customer. The customer shall have no right to audit the books or security of the vendor. Auditing of the system, data, or financial records by the client is strictly prohibited.",
        "### Clause 4: Limitation of Liability (High Risk Clause)",
        "The Supplier's total liability under this Agreement shall be completely unlimited under any circumstances. Neither party limits its liability for any damages or breaches. The vendor will be liable for all direct and indirect damages without limitation.",
    ]
    generate_pdf(
        os.path.join(output_dir, "vendor_contract.pdf"),
        "Vendor Master Services Agreement",
        vendor_content,
    )

    # ── 3. Security SOP (Medium Risk) ───────────────────────────────
    sop_content = [
        "### Standard Operating Procedure: InfoSec compliance",
        "This document describes the standard operating procedures for information security controls, auditing processes, and server monitoring.",
        "### Clause A: Server Inspections",
        "Information security teams will perform routine scans and vulnerability assessments on all production systems every Friday night.",
        "### Clause B: Term &amp; Extensions (Medium Risk Clause)",
        "This contract shall automatically renew for successive one-year terms unless cancelled. At the end of the initial term, the agreement will auto-renew. The service agreement extends automatically unless written notice is given 30 days prior.",
        "### Clause C: Policy Violation &amp; Termination (Medium Risk Clause)",
        "Either party may terminate this agreement immediately and without notice upon any breach. This agreement may be terminated by the vendor immediately without prior written notice.",
    ]
    generate_pdf(
        os.path.join(output_dir, "security_sop.pdf"),
        "Information Security Standard Operating Procedure",
        sop_content,
    )


if __name__ == "__main__":
    main()
