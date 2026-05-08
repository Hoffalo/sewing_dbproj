"""
Staff PDF export for workshop tickets (ReportLab — pure Python, container-friendly).
"""

from io import BytesIO

from django.contrib.admin.views.decorators import staff_member_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from apps.production.models import Ticket


@staff_member_required
def ticket_pdf(request, ticket_id: int):
    ticket = get_object_or_404(
        Ticket.objects.select_related(
            "current_stage",
            "assigned_to__user",
            "order_item__order__customer",
        ).prefetch_related(
            "order_item__measurements",
            "order_item__material_links__material",
        ),
        pk=ticket_id,
    )
    oi = ticket.order_item
    order = oi.order
    customer = order.customer

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleCL",
        parent=styles["Title"],
        textColor=colors.HexColor("#C84B31"),
        spaceAfter=12,
    )
    story = []

    story.append(Paragraph("Costuras Lucía", title_style))
    story.append(Paragraph("Costuras Lucía — " + timezone.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"<b>{ticket.code}</b> &nbsp;|&nbsp; Etapa: {ticket.current_stage.name}", styles["Heading3"]))
    story.append(Spacer(1, 0.3 * cm))

    ci_data = [
        ["Cliente", f"{customer.first_name} {customer.last_name}"],
        ["Teléfono", customer.phone or "—"],
        ["Pedido", f"#{order.pk} — vence {order.due_date}"],
        ["Prenda", oi.get_garment_type_display()],
        ["Descripción", oi.description],
    ]
    if oi.fabric:
        ci_data.append(["Tela", oi.fabric])
    if oi.color:
        ci_data.append(["Color", oi.color])

    t1 = Table(ci_data, colWidths=[4 * cm, 12 * cm])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#fdf6f4")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t1)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("<b>Medidas (cm)</b>", styles["Heading4"]))
    meas_data = [["Medida", "Valor", "Notas"]]
    for m in oi.measurements.all().order_by("name"):
        meas_data.append([m.get_name_display(), str(m.value_cm), m.notes or ""])
    t2 = Table(meas_data, colWidths=[4 * cm, 3 * cm, 9 * cm])
    t2.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.beige)]))
    story.append(t2)
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("<b>Materiales</b>", styles["Heading4"]))
    mat_data = [["Material", "Cantidad"]]
    for link in oi.material_links.all():
        mat_data.append([str(link.material), str(link.quantity_used)])
    if len(mat_data) == 1:
        mat_data.append(["—", "—"])
    t3 = Table(mat_data, colWidths=[12 * cm, 4 * cm])
    t3.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    story.append(t3)
    story.append(Spacer(1, 0.4 * cm))

    deadline = ticket.deadline or order.due_date
    story.append(Paragraph(f"<b>Fecha límite:</b> {deadline}", styles["Normal"]))
    if ticket.assigned_to:
        story.append(
            Paragraph(
                f"<b>Asignado a:</b> {ticket.assigned_to.user.get_full_name() or ticket.assigned_to.user.get_username()}",
                styles["Normal"],
            )
        )

    doc.build(story)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f"{ticket.code}.pdf")
