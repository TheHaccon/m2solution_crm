from decimal import Decimal

from fpdf import FPDF

from app.core.config import settings
from app.models.invoice import Invoice


def _txt(value: str | None) -> str:
    if not value:
        return ""
    return value.encode("latin-1", "replace").decode("latin-1")


def _money(value: Decimal | str | int | float) -> str:
    return f"${Decimal(value):,.2f}"


def build_invoice_pdf(invoice: Invoice) -> bytes:
    client = invoice.client
    pdf = FPDF(format="Letter", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)

    navy = (10, 22, 40)
    gold = (196, 163, 90)
    muted = (80, 90, 105)

    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 10, _txt(settings.company_name), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*muted)
    if settings.company_address:
        for line in settings.company_address.splitlines():
            pdf.cell(0, 5, _txt(line), new_x="LMARGIN", new_y="NEXT")
    if settings.company_email:
        pdf.cell(0, 5, _txt(settings.company_email), new_x="LMARGIN", new_y="NEXT")
    if settings.company_phone:
        pdf.cell(0, 5, _txt(settings.company_phone), new_x="LMARGIN", new_y="NEXT")

    y = pdf.get_y()
    pdf.set_xy(120, 18)
    pdf.set_text_color(*gold)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(72, 6, "INVOICE", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(120)
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(72, 8, _txt(invoice.number), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(120)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*muted)
    pdf.cell(72, 5, invoice.status.upper(), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(max(y, pdf.get_y()) + 6)

    pdf.set_draw_color(220, 220, 220)
    pdf.line(18, pdf.get_y(), 198, pdf.get_y())
    pdf.ln(8)

    left = pdf.get_y()
    pdf.set_text_color(*muted)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(90, 5, "BILL TO", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(90, 6, _txt(client.name), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*muted)
    if client.email:
        pdf.cell(90, 5, _txt(client.email), new_x="LMARGIN", new_y="NEXT")
    if client.address:
        for line in client.address.splitlines():
            pdf.cell(90, 5, _txt(line), new_x="LMARGIN", new_y="NEXT")
    after_bill = pdf.get_y()

    pdf.set_xy(120, left)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*muted)
    pdf.cell(40, 6, "Issue date", new_x="END", new_y="TOP")
    pdf.set_text_color(*navy)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(32, 6, invoice.issue_date.isoformat(), align="R", new_x="LMARGIN", new_y="NEXT")
    if invoice.due_date:
        pdf.set_x(120)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*muted)
        pdf.cell(40, 6, "Due", new_x="END", new_y="TOP")
        pdf.set_text_color(*navy)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(32, 6, invoice.due_date.isoformat(), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(max(after_bill, pdf.get_y()) + 10)

    col_desc, col_qty, col_rate, col_amt = 90, 22, 34, 34
    pdf.set_fill_color(246, 243, 238)
    pdf.set_text_color(*muted)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_desc, 8, "DESCRIPTION", fill=True)
    pdf.cell(col_qty, 8, "QTY", align="R", fill=True)
    pdf.cell(col_rate, 8, "RATE", align="R", fill=True)
    pdf.cell(col_amt, 8, "AMOUNT", align="R", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*navy)
    for item in invoice.line_items:
        pdf.cell(col_desc, 8, _txt(item.description)[:60])
        pdf.cell(col_qty, 8, f"{Decimal(item.quantity):g}", align="R")
        pdf.cell(col_rate, 8, _money(item.unit_price), align="R")
        pdf.cell(col_amt, 8, _money(item.amount), align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    pdf.set_x(120)
    pdf.set_text_color(*muted)
    pdf.cell(40, 6, "Subtotal", new_x="END", new_y="TOP")
    pdf.set_text_color(*navy)
    pdf.cell(32, 6, _money(invoice.subtotal), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(120)
    pdf.set_draw_color(10, 22, 40)
    pdf.line(120, pdf.get_y(), 192, pdf.get_y())
    pdf.ln(2)
    pdf.set_x(120)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(40, 8, "Total", new_x="END", new_y="TOP")
    pdf.cell(32, 8, _money(invoice.total), align="R", new_x="LMARGIN", new_y="NEXT")

    if invoice.notes:
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*muted)
        pdf.cell(0, 5, "NOTES", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*navy)
        pdf.multi_cell(0, 5, _txt(invoice.notes))

    pdf.ln(16)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*muted)
    pdf.cell(0, 5, "Thank you for your business.", align="C")

    return bytes(pdf.output())
