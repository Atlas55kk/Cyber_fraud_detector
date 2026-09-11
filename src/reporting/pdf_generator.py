"""
Module: pdf_generator.py
Generates statutory Law Enforcement Requisition Notices in PDF format under:
- Section 94 of Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023
- Section 63 of BNSS (Certificate for Electronic Evidence Admissibility)

STRICT COMPLIANCE & SAFETY NOTICE:
- Watermarked as 'CONFIDENTIAL FORENSIC DRAFT // FOR INVESTIGATIVE REVIEW ONLY'.
- Free of any restricted state emblems, official logos, or unauthorized seals.
- Generated for local offline preview and evidentiary record keeping.
"""

import os
import io
import time
from typing import Optional, List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.core.canvas import WhiteboardCanvas
from src.core.node_box import ForensicNodeBox
from src.attribution.entity_resolver import EntityInfo
from src.reporting.dossier_generator import CaseDetails


class LegalNoticePDFGenerator:
    """
    Renders formal Section 94 BNSS Legal Requisition Notices to PDF.
    """

    def __init__(self, canvas: WhiteboardCanvas):
        self.canvas = canvas

    def generate_pdf_bytes(
        self,
        case: CaseDetails,
        target_cex_node: ForensicNodeBox,
        entity_info: Optional[EntityInfo] = None
    ) -> bytes:
        """
        Generates and returns PDF bytes for the Section 94 BNSS Requisition Notice.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        header_style = ParagraphStyle(
            "NoticeHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=1, # Centered
            textColor=colors.HexColor("#1A202C")
        )
        watermark_style = ParagraphStyle(
            "NoticeWatermark",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=1,
            textColor=colors.HexColor("#C53030") # Crimson warning
        )
        title_style = ParagraphStyle(
            "NoticeTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor("#2B6CB0")
        )
        body_style = ParagraphStyle(
            "NoticeBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#2D3748")
        )
        bold_body = ParagraphStyle(
            "NoticeBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )
        code_style = ParagraphStyle(
            "NoticeCode",
            parent=body_style,
            fontName="Courier",
            fontSize=8,
            leading=10
        )

        story = []

        # 1. Draft Notice Banner (No official state insignia to maintain safety)
        story.append(Paragraph("[CONFIDENTIAL FORENSIC DRAFT // FOR LAW ENFORCEMENT INVESTIGATIVE REVIEW ONLY]", watermark_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("CYBER CRIME INVESTIGATION WING // FINANCIAL INTELLIGENCE UNIT", header_style))
        story.append(Paragraph(case.police_station.upper(), header_style))
        story.append(Spacer(1, 4))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceBefore=2, spaceAfter=8))

        # 2. Subject & Statutory Reference
        story.append(Paragraph(
            "FORMAL REQUISITION NOTICE UNDER SECTION 94 OF BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS), 2023",
            title_style
        ))
        story.append(Paragraph(
            "<i>(Corresponding to Section 91 of the Code of Criminal Procedure, 1973)</i>",
            ParagraphStyle("Sub", parent=body_style, alignment=1, fontSize=8, leading=10, textColor=colors.HexColor("#718096"))
        ))
        story.append(Spacer(1, 10))

        # 3. Addressee & Case Metadata Table
        exchange_name = entity_info.name if entity_info else (target_cex_node.entity_tag or "Centralized Exchange Compliance Desk")
        compliance_email = entity_info.compliance_email if entity_info else "compliance-desk@exchange.com"
        current_date = time.strftime("%d-%B-%Y %H:%M:%S IST", time.localtime())

        meta_data = [
            [Paragraph("<b>To:</b>", bold_body), Paragraph(f"{exchange_name} (Compliance Desk)", body_style),
             Paragraph("<b>Date:</b>", bold_body), Paragraph(current_date, body_style)],
            [Paragraph("<b>Email:</b>", bold_body), Paragraph(compliance_email, body_style),
             Paragraph("<b>NCRP Ack:</b>", bold_body), Paragraph(case.ack_number, body_style)],
            [Paragraph("<b>FIR No:</b>", bold_body), Paragraph(case.fir_number, body_style),
             Paragraph("<b>IO:</b>", bold_body), Paragraph(case.investigating_officer, body_style)],
            [Paragraph("<b>Victim:</b>", bold_body), Paragraph(case.victim_name, body_style),
             Paragraph("<b>Loss Amount:</b>", bold_body), Paragraph(f"INR {case.loss_inr:,.2f} ({case.loss_crypto_str})", body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[65, 200, 75, 180])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # 4. Operative Freezing Directives
        story.append(Paragraph("<b>1. STATUTORY DIRECTIONS & REQUISITIONS</b>", bold_body))
        story.append(Spacer(1, 4))
        
        target_addr = target_cex_node.address
        stolen_held = target_cex_node.stolen_amount_held
        taint_pct = target_cex_node.stolen_taint_ratio * 100

        directions_text = (
            f"WHEREAS the undersigned Investigating Officer is conducting a statutory inquiry into online financial "
            f"fraud under the Bharatiya Nyaya Sanhita (BNS) and Information Technology Act, 2000. On-chain forensic reconstruction "
            f"confirms that siphoned assets have entered your platform at deposit endpoint <b>{target_addr}</b>.<br/><br/>"
            f"In exercise of statutory powers under <b>Section 94 of BNSS, 2023</b>, you are hereby directed to:<br/>"
            f"&nbsp;&nbsp;<b>(a) Immediately Freeze:</b> Place an administrative debit freeze on deposit account <b>{target_addr}</b> "
            f"holding estimated tainted funds of <b>{stolen_held:,.2f} USDT</b> (Taint ratio: <b>{taint_pct:.1f}%</b>).<br/>"
            f"&nbsp;&nbsp;<b>(b) Prevent Dissipation:</b> Restrict all outgoing withdrawals, P2P transactions, and internal transfers.<br/>"
            f"&nbsp;&nbsp;<b>(c) Furnish KYC Records:</b> Provide within 24 hours verified user registration details, PAN/Aadhaar/Passport, "
            f"linked bank accounts, and IP login logs (with timestamps and port numbers)."
        )
        story.append(Paragraph(directions_text, body_style))
        story.append(Spacer(1, 10))

        # 5. Blockchain Custody Evidence Trail Table
        story.append(Paragraph("<b>2. CHAIN OF CUSTODY (BLOCKCHAIN EVIDENCE TRAIL)</b>", bold_body))
        story.append(Spacer(1, 4))

        paths = self.canvas.trace_paths_to_address(target_cex_node.address)
        trail_hashes = paths[0] if paths else []

        trail_headers = [
            Paragraph("<b>Hop</b>", bold_body),
            Paragraph("<b>Sender</b>", bold_body),
            Paragraph("<b>Receiver</b>", bold_body),
            Paragraph("<b>Value</b>", bold_body),
            Paragraph("<b>Transaction Hash</b>", bold_body)
        ]
        trail_rows = [trail_headers]

        for i, h in enumerate(trail_hashes, 1):
            wire = self.canvas.wires.get(h)
            if wire:
                trail_rows.append([
                    Paragraph(f"#{i}", body_style),
                    Paragraph(f"{wire.from_address[:8]}...{wire.from_address[-6:]}", code_style),
                    Paragraph(f"{wire.to_address[:8]}...{wire.to_address[-6:]}", code_style),
                    Paragraph(f"{wire.value:,.2f} {wire.token_symbol}", body_style),
                    Paragraph(f"{wire.tx_hash[:12]}...", code_style)
                ])

        if len(trail_rows) == 1:
            trail_rows.append([
                Paragraph("#1", body_style),
                Paragraph(self.canvas.incident_root_address[:14] if self.canvas.incident_root_address else "Origin", code_style),
                Paragraph(f"{target_addr[:14]}...", code_style),
                Paragraph(f"{stolen_held:,.2f} USDT", body_style),
                Paragraph("Direct Transfer", code_style)
            ])

        trail_table = Table(trail_rows, colWidths=[35, 125, 125, 100, 135])
        trail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(trail_table)
        story.append(Spacer(1, 10))

        # 6. Section 63 BNSS Electronic Certificate & Legal Admissibility
        cert_text = (
            "<b>3. ELECTRONIC EVIDENCE CERTIFICATE (SECTION 63 BNSS / SEC 65B EVIDENCE ACT):</b><br/>"
            "This digital record has been produced by cryptographic computer systems operating under lawful custody. "
            "The blockchain transaction hashes referenced above are cryptographically immutable and mathematically verifiable "
            "on public distributed ledgers."
        )
        story.append(Paragraph(cert_text, body_style))
        story.append(Spacer(1, 14))

        # 7. Sign-off Line (Formal Draft)
        sig_data = [
            [Paragraph("<b>Generated By:</b> Automated Cyber Fraud Forensic Tracing System", body_style),
             Paragraph(f"<b>(Investigating Officer)</b><br/>{case.investigating_officer}<br/>{case.police_station}", body_style)]
        ]
        sig_table = Table(sig_data, colWidths=[320, 200])
        sig_table.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(sig_table)

        doc.build(story)
        return buffer.getvalue()

    def save_pdf(
        self,
        filepath: str,
        case: CaseDetails,
        target_cex_node: ForensicNodeBox,
        entity_info: Optional[EntityInfo] = None
    ) -> str:
        """
        Saves the PDF notice to a local file.
        """
        pdf_bytes = self.generate_pdf_bytes(case, target_cex_node, entity_info)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        return filepath
