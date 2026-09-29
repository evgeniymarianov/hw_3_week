from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas import EventDashboard


FONT_DIR = Path(__file__).parent / "assets" / "fonts"
REGULAR_FONT_PATH = FONT_DIR / "FiraCode-Regular.ttf"
BOLD_FONT_PATH = FONT_DIR / "FiraCode-Bold.ttf"
HEADING_FONT_PATH = FONT_DIR / "IBMPlexSans-Regular.ttf"
HEADING_BOLD_FONT_PATH = FONT_DIR / "IBMPlexSans-Bold.ttf"
PAGE_BACKGROUND_PATHS = {
    1: Path(__file__).parent / "assets" / "report_background_cover.jpg",
    2: Path(__file__).parent / "assets" / "report_background_sales.jpg",
    3: Path(__file__).parent / "assets" / "report_background_occupancy.jpg",
}


class OccupancyBar(Flowable):
    def __init__(self, percent: float, width: int = 160 * mm, height: int = 12 * mm):
        super().__init__()
        self.percent = max(0, min(percent, 100))
        self.width = width
        self.height = height

    def draw(self) -> None:
        fill_width = self.width * self.percent / 100
        self.canv.setFillColor(colors.HexColor("#153026"))
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        self.canv.setFillColor(colors.HexColor("#33D17A"))
        self.canv.roundRect(0, 0, fill_width, self.height, 4, fill=1, stroke=0)


def generate_event_dashboard_pdf(
    dashboard: EventDashboard,
    output_path: str | Path,
    generated_at: datetime | None = None,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = generated_at or datetime.now()

    font_name, bold_font_name, heading_font_name, heading_bold_font_name = _register_fonts()
    styles = _build_styles(
        font_name,
        bold_font_name,
        heading_font_name,
        heading_bold_font_name,
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=24 * mm,
        bottomMargin=24 * mm,
        title=f"Отчет: {dashboard.event_title}",
        author="Afisha",
    )

    sales = dashboard.sales
    occupancy = dashboard.occupancy

    story = [
        Spacer(1, 80 * mm),
        Paragraph("Отчет по мероприятию", styles["title"]),
        Spacer(1, 8 * mm),
        Paragraph(dashboard.event_title, styles["subtitle"]),
        Spacer(1, 5 * mm),
        Paragraph(f"Дата мероприятия: {_format_datetime(dashboard.starts_at)}", styles["muted"]),
        Paragraph(f"Дата генерации отчета: {_format_datetime(generated_at)}", styles["muted"]),
        PageBreak(),
        Paragraph("Отчет по продажам", styles["pageTitle"]),
        Spacer(1, 12 * mm),
        _summary_cards(
            [
                ("Продажи", str(sales.paid_orders)),
                ("Продано билетов", str(sales.sold_tickets)),
                ("Выручка", _format_money(sales.revenue)),
                ("Средний чек", _format_money(sales.average_order)),
            ],
            styles,
        ),
        Spacer(1, 14 * mm),
        _sales_table(dashboard, styles),
        PageBreak(),
        Paragraph("Отчет по заполняемости", styles["pageTitle"]),
        Spacer(1, 12 * mm),
        OccupancyBar(occupancy.occupancy_percent),
        Spacer(1, 4 * mm),
        Paragraph(f"{occupancy.occupancy_percent:.1f}% мест занято", styles["muted"]),
        Spacer(1, 14 * mm),
        _occupancy_table(dashboard, styles),
    ]

    doc.build(story, onFirstPage=_draw_background, onLaterPages=_draw_background)
    return output_path


def _draw_background(canvas, doc) -> None:
    background_path = PAGE_BACKGROUND_PATHS[canvas.getPageNumber()]
    if not background_path.exists():
        raise FileNotFoundError(f"Не найден фон отчета {background_path}.")

    page_width, page_height = A4
    canvas.saveState()
    canvas.drawImage(
        str(background_path),
        0,
        0,
        width=page_width,
        height=page_height,
        preserveAspectRatio=False,
        mask=None,
    )
    canvas.restoreState()


def _register_fonts() -> tuple[str, str, str, str]:
    if not REGULAR_FONT_PATH.exists():
        raise FileNotFoundError(
            f"Не найден шрифт {REGULAR_FONT_PATH}. "
            "Положите FiraCode-Regular.ttf и FiraCode-Bold.ttf в app/assets/fonts."
        )
    if not HEADING_FONT_PATH.exists():
        raise FileNotFoundError(
            f"Не найден шрифт {HEADING_FONT_PATH}. "
            "Положите IBMPlexSans-Regular.ttf и IBMPlexSans-Bold.ttf в app/assets/fonts."
        )

    pdfmetrics.registerFont(TTFont("AfishaRegular", str(REGULAR_FONT_PATH)))
    pdfmetrics.registerFont(TTFont("AfishaHeading", str(HEADING_FONT_PATH)))

    if BOLD_FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont("AfishaBold", str(BOLD_FONT_PATH)))
        bold_font_name = "AfishaBold"
    else:
        bold_font_name = "AfishaRegular"

    if HEADING_BOLD_FONT_PATH.exists():
        pdfmetrics.registerFont(TTFont("AfishaHeadingBold", str(HEADING_BOLD_FONT_PATH)))
        heading_bold_font_name = "AfishaHeadingBold"
    else:
        heading_bold_font_name = "AfishaHeading"

    return "AfishaRegular", bold_font_name, "AfishaHeading", heading_bold_font_name


def _build_styles(
    font_name: str,
    bold_font_name: str,
    heading_font_name: str,
    heading_bold_font_name: str,
) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "AfishaTitle",
            parent=base["Title"],
            fontName=heading_bold_font_name,
            fontSize=34,
            leading=42,
            textColor=colors.white,
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "subtitle": ParagraphStyle(
            "AfishaSubtitle",
            parent=base["Heading2"],
            fontName=heading_bold_font_name,
            fontSize=17,
            leading=22,
            textColor=colors.HexColor("#D9FBE7"),
            alignment=TA_CENTER,
            spaceAfter=0,
        ),
        "pageTitle": ParagraphStyle(
            "AfishaPageTitle",
            parent=base["Heading1"],
            fontName=heading_bold_font_name,
            fontSize=26,
            leading=32,
            textColor=colors.white,
            spaceAfter=0,
        ),
        "section": ParagraphStyle(
            "AfishaSection",
            parent=base["Heading3"],
            fontName=heading_bold_font_name,
            fontSize=14,
            leading=18,
            textColor=colors.white,
            spaceAfter=0,
        ),
        "cardLabel": ParagraphStyle(
            "AfishaCardLabel",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#A8B8AF"),
            alignment=TA_CENTER,
        ),
        "cardValue": ParagraphStyle(
            "AfishaCardValue",
            parent=base["Normal"],
            fontName=bold_font_name,
            fontSize=14,
            leading=18,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "tableHeader": ParagraphStyle(
            "AfishaTableHeader",
            parent=base["Normal"],
            fontName=bold_font_name,
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#D9FBE7"),
        ),
        "tableCell": ParagraphStyle(
            "AfishaTableCell",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#F5FFF8"),
        ),
        "tableNumber": ParagraphStyle(
            "AfishaTableNumber",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#F5FFF8"),
            alignment=TA_RIGHT,
        ),
        "muted": ParagraphStyle(
            "AfishaMuted",
            parent=base["Normal"],
            fontName=font_name,
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#A8B8AF"),
            alignment=TA_CENTER,
        ),
    }


def _summary_cards(
    items: list[tuple[str, str]],
    styles: dict[str, ParagraphStyle],
) -> Table:
    data = [
        [Paragraph(label, styles["cardLabel"]) for label, _value in items],
        [Paragraph(value, styles["cardValue"]) for _label, value in items],
    ]
    table = Table(data, colWidths=[40 * mm] * len(items), rowHeights=[11 * mm, 15 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#07110D")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#24513C")),
                ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#24513C")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _sales_table(
    dashboard: EventDashboard,
    styles: dict[str, ParagraphStyle],
) -> Table:
    sales = dashboard.sales
    rows = [
        ("Количество продаж", sales.paid_orders),
        ("Количество проданных билетов", sales.sold_tickets),
        ("Выручка", _format_money(sales.revenue)),
        ("Средний чек", _format_money(sales.average_order)),
    ]

    return _metrics_table(rows, styles)


def _occupancy_table(
    dashboard: EventDashboard,
    styles: dict[str, ParagraphStyle],
) -> Table:
    occupancy = dashboard.occupancy
    rows = [
        ("Всего мест", occupancy.total),
        ("Доступно", occupancy.available),
        ("Забронировано", occupancy.reserved),
        ("Продано", occupancy.sold),
    ]

    return _metrics_table(rows, styles)


def _metrics_table(
    rows: list[tuple[str, int | str]],
    styles: dict[str, ParagraphStyle],
) -> Table:
    table = Table(
        [
            [
                Paragraph("Показатель", styles["tableHeader"]),
                Paragraph("Значение", styles["tableHeader"]),
            ],
            *[
                [Paragraph(label, styles["tableCell"]), Paragraph(str(value), styles["tableNumber"])]
                for label, value in rows
            ],
        ],
        colWidths=[112 * mm, 48 * mm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0E2218")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#07110D"), colors.HexColor("#0A1711")]),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#24513C")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#1C3E2F")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def _format_money(value: int) -> str:
    return f"{value / 100:,.2f} ₽".replace(",", " ")


def _format_datetime(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M")
