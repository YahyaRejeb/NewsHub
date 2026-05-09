from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import wrap
from typing import Iterable
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
ASSETS_DIR = REPORTS_DIR / "live_module_documentation_assets"
OUTPUT_PDF = REPORTS_DIR / "live_module_documentation.pdf"


@dataclass(frozen=True)
class ScreenshotSpec:
    slug: str
    relative_path: str
    start_line: int
    end_line: int
    title: str


SCREENSHOTS = [
    ScreenshotSpec(
        slug="routes_live",
        relative_path="frontend/src/app/app.routes.ts",
        start_line=23,
        end_line=30,
        title="Routes Angular du module live",
    ),
    ScreenshotSpec(
        slug="live_model_socket_contract",
        relative_path="frontend/src/app/core/models/live-event.model.ts",
        start_line=43,
        end_line=92,
        title="Contrat de messages WebSocket cote Angular",
    ),
    ScreenshotSpec(
        slug="live_hub_create",
        relative_path="frontend/src/app/features/live/live-hub-page/live-hub-page.ts",
        start_line=76,
        end_line=117,
        title="Creation d'une live room cote hub",
    ),
    ScreenshotSpec(
        slug="room_init_and_access",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        start_line=80,
        end_line=156,
        title="Initialisation et regles d'acces de la room",
    ),
    ScreenshotSpec(
        slug="editor_actions",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        start_line=158,
        end_line=305,
        title="Actions de l'editeur: camera, start, end, updates, chat",
    ),
    ScreenshotSpec(
        slug="socket_orchestration",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        start_line=307,
        end_line=463,
        title="Orchestration des evenements socket dans la room",
    ),
    ScreenshotSpec(
        slug="webrtc_signaling_frontend",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        start_line=465,
        end_line=563,
        title="Signalisation WebRTC cote Angular",
    ),
    ScreenshotSpec(
        slug="socket_service",
        relative_path="frontend/src/app/core/services/live-room-socket.ts",
        start_line=9,
        end_line=39,
        title="Service Angular de connexion WebSocket",
    ),
    ScreenshotSpec(
        slug="backend_models",
        relative_path="backend/models.py",
        start_line=96,
        end_line=127,
        title="Modeles SQLAlchemy LiveEvent et LiveMessage",
    ),
    ScreenshotSpec(
        slug="backend_manager",
        relative_path="backend/main.py",
        start_line=243,
        end_line=302,
        title="Gestionnaire serveur des connexions WebSocket",
    ),
    ScreenshotSpec(
        slug="backend_rest_live",
        relative_path="backend/main.py",
        start_line=410,
        end_line=579,
        title="Endpoints REST du module live",
    ),
    ScreenshotSpec(
        slug="backend_websocket_guard",
        relative_path="backend/main.py",
        start_line=970,
        end_line=1008,
        title="Ouverture et validation de la WebSocket serveur",
    ),
    ScreenshotSpec(
        slug="backend_websocket_messages",
        relative_path="backend/main.py",
        start_line=1010,
        end_line=1085,
        title="Branches chat, update et broadcaster_ready cote serveur",
    ),
    ScreenshotSpec(
        slug="backend_websocket_signaling",
        relative_path="backend/main.py",
        start_line=1087,
        end_line=1114,
        title="Relai du signaling WebRTC et nettoyage serveur",
    ),
]


def choose_existing_path(paths: Iterable[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def register_fonts() -> tuple[str, str, str]:
    regular_path = choose_existing_path(
        [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("C:/Windows/Fonts/calibri.ttf"),
        ]
    )
    bold_path = choose_existing_path(
        [
            Path("C:/Windows/Fonts/arialbd.ttf"),
            Path("C:/Windows/Fonts/segoeuib.ttf"),
            Path("C:/Windows/Fonts/calibrib.ttf"),
        ]
    )
    mono_path = choose_existing_path(
        [
            Path("C:/Windows/Fonts/consola.ttf"),
            Path("C:/Windows/Fonts/cour.ttf"),
            Path("C:/Windows/Fonts/lucon.ttf"),
        ]
    )

    if regular_path and bold_path and mono_path:
        pdfmetrics.registerFont(TTFont("DocRegular", str(regular_path)))
        pdfmetrics.registerFont(TTFont("DocBold", str(bold_path)))
        pdfmetrics.registerFont(TTFont("DocMono", str(mono_path)))
        return "DocRegular", "DocBold", "DocMono"

    return "Helvetica", "Helvetica-Bold", "Courier"


FONT_REGULAR, FONT_BOLD, FONT_MONO = register_fonts()


def build_styles() -> StyleSheet1:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            fontName=FONT_BOLD,
            fontSize=24,
            leading=29,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocSubtitle",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading1"],
            fontName=FONT_BOLD,
            fontSize=17,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubsectionTitle",
            parent=styles["Heading2"],
            fontName=FONT_BOLD,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=9.4,
            leading=14,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#111827"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=8.5,
            leading=12.5,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#334155"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocBullet",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=9.3,
            leading=13.4,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#111827"),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=8.2,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MiniNote",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=8,
            leading=10.6,
            textColor=colors.HexColor("#334155"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeCell",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=8.4,
            leading=11.2,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverNote",
            parent=styles["BodyText"],
            fontName=FONT_REGULAR,
            fontSize=10,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=4,
        )
    )
    return styles


STYLES = build_styles()


def p(text: str, style_name: str = "Body") -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), STYLES[style_name])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"- {escape(text)}", STYLES["DocBullet"])


def line_rule() -> HRFlowable:
    return HRFlowable(color=colors.HexColor("#cbd5e1"), thickness=0.6, width="100%")


def read_lines(relative_path: str) -> list[str]:
    target = ROOT / relative_path
    return target.read_text(encoding="utf-8").splitlines()


def load_font_for_image(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/lucon.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_code_screenshot(spec: ScreenshotSpec) -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    source_lines = read_lines(spec.relative_path)[spec.start_line - 1 : spec.end_line]
    numbered_lines = [f"{line_number:>4}  {content}" for line_number, content in zip(range(spec.start_line, spec.end_line + 1), source_lines)]

    code_font = load_font_for_image(18)
    header_font = load_font_for_image(20)
    small_font = load_font_for_image(15)

    scratch = PILImage.new("RGB", (20, 20), "#0b1220")
    draw = ImageDraw.Draw(scratch)
    max_width = 0
    for line in numbered_lines:
        bbox = draw.textbbox((0, 0), line or " ", font=code_font)
        max_width = max(max_width, bbox[2] - bbox[0])

    padding = 28
    line_height = 28
    header_height = 86
    width = max(1200, min(max_width + padding * 2, 2200))
    height = header_height + padding + line_height * max(len(numbered_lines), 1)

    image = PILImage.new("RGB", (width, height), "#0b1220")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, width - 12, height - 12), radius=20, fill="#111827", outline="#334155", width=2)
    draw.rounded_rectangle((12, 12, width - 12, 70), radius=20, fill="#172554", outline="#334155", width=0)
    draw.ellipse((30, 30, 42, 42), fill="#ef4444")
    draw.ellipse((52, 30, 64, 42), fill="#f59e0b")
    draw.ellipse((74, 30, 86, 42), fill="#22c55e")
    draw.text((110, 25), spec.title, fill="#e2e8f0", font=header_font)
    draw.text((110, 49), f"{spec.relative_path}  |  lignes {spec.start_line}-{spec.end_line}", fill="#93c5fd", font=small_font)

    y = 92
    for line in numbered_lines:
        if not line.strip():
            y += line_height
            continue

        number = line[:4]
        body = line[6:]
        draw.text((34, y), number, fill="#64748b", font=code_font)
        draw.text((100, y), body.replace("\t", "  "), fill="#e5e7eb", font=code_font)
        y += line_height

    output_path = ASSETS_DIR / f"{spec.slug}.png"
    image.save(output_path)
    return output_path


def fit_image(image_path: Path, max_width: float, max_height: float = 21.0 * cm) -> RLImage:
    preview = PILImage.open(image_path)
    width_px, height_px = preview.size
    scale = min(max_width / width_px, max_height / height_px)
    width = width_px * scale
    height = height_px * scale
    return RLImage(str(image_path), width=width, height=height)


def make_table(rows: list[list[str]], column_widths: list[float]) -> LongTable:
    data = []
    for index, row in enumerate(rows):
        style_name = "CodeCell" if index else "MiniNote"
        data.append([Paragraph(escape(cell), STYLES[style_name]) for cell in row])

    table = LongTable(data, colWidths=column_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbeafe")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def make_architecture_drawing() -> Drawing:
    drawing = Drawing(520, 230)

    def box(x: int, y: int, w: int, h: int, title: str, lines: list[str], fill: str, stroke: str) -> None:
        drawing.add(Rect(x, y, w, h, rx=16, ry=16, fillColor=colors.HexColor(fill), strokeColor=colors.HexColor(stroke), strokeWidth=1.6))
        drawing.add(String(x + 14, y + h - 24, title, fontName=FONT_BOLD, fontSize=12, fillColor=colors.HexColor("#0f172a")))
        offset = 42
        for line in lines:
            drawing.add(String(x + 14, y + h - offset, line, fontName=FONT_REGULAR, fontSize=9, fillColor=colors.HexColor("#334155")))
            offset += 15

    box(16, 132, 156, 76, "Frontend Angular", ["Hub live", "Room live", "Etat UI et videos"], "#dbeafe", "#2563eb")
    box(190, 132, 152, 76, "FastAPI REST", ["Creation room", "Start / end / delete", "Chargement initial"], "#e0f2fe", "#0284c7")
    box(190, 28, 152, 76, "FastAPI WebSocket", ["Chat", "Updates", "Viewer count", "Signalisation WebRTC"], "#dcfce7", "#16a34a")
    box(360, 132, 144, 76, "Base de donnees", ["live_events", "live_messages"], "#ede9fe", "#7c3aed")
    box(360, 28, 144, 76, "Flux WebRTC", ["Offer", "Answer", "ICE", "Pistes audio/video"], "#fef3c7", "#d97706")

    drawing.add(Line(172, 170, 190, 170, strokeColor=colors.HexColor("#64748b"), strokeWidth=2))
    drawing.add(Line(342, 170, 360, 170, strokeColor=colors.HexColor("#64748b"), strokeWidth=2))
    drawing.add(Line(270, 132, 270, 104, strokeColor=colors.HexColor("#64748b"), strokeWidth=2))
    drawing.add(Line(342, 66, 360, 66, strokeColor=colors.HexColor("#64748b"), strokeWidth=2))
    drawing.add(String(224, 182, "HTTP", fontName=FONT_BOLD, fontSize=10, fillColor=colors.HexColor("#1d4ed8")))
    drawing.add(String(376, 182, "SQLAlchemy", fontName=FONT_BOLD, fontSize=10, fillColor=colors.HexColor("#7c3aed")))
    drawing.add(String(274, 112, "JSON temps reel", fontName=FONT_BOLD, fontSize=10, fillColor=colors.HexColor("#15803d")))
    drawing.add(String(382, 78, "Media plane", fontName=FONT_BOLD, fontSize=10, fillColor=colors.HexColor("#b45309")))
    return drawing


def make_join_flow_drawing() -> Drawing:
    drawing = Drawing(520, 180)

    steps = [
        ("1", "/live/:id"),
        ("2", "GET detail"),
        ("3", "Acces OK"),
        ("4", "Socket prete"),
        ("5", "Demande flux"),
        ("6", "SDP + ICE"),
        ("7", "Flux recu"),
    ]
    x = 16
    for index, (number, label) in enumerate(steps):
        width = 58
        drawing.add(Rect(x, 74, width, 58, rx=14, ry=14, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#94a3b8"), strokeWidth=1.2))
        drawing.add(String(x + 10, 112, number, fontName=FONT_BOLD, fontSize=12, fillColor=colors.HexColor("#1d4ed8")))
        wrapped = wrap(label, width=12)
        y = 96
        for part in wrapped:
            drawing.add(String(x + 8, y, part, fontName=FONT_REGULAR, fontSize=8.1, fillColor=colors.HexColor("#334155")))
            y -= 11
        if index < len(steps) - 1:
            drawing.add(Line(x + width, 103, x + width + 12, 103, strokeColor=colors.HexColor("#64748b"), strokeWidth=1.8))
        x += width + 12

    drawing.add(String(16, 32, "Le lecteur voit vraiment le direct a l'etape 7, quand le flux WebRTC arrive dans ontrack.", fontName=FONT_BOLD, fontSize=10, fillColor=colors.HexColor("#0f172a")))
    drawing.add(String(16, 16, "Les etapes 1 a 6 preparant l'acces, la socket et la signalisation, mais pas encore l'image.", fontName=FONT_REGULAR, fontSize=9, fillColor=colors.HexColor("#334155")))
    return drawing


def add_screenshot(story: list, slug: str, caption: str) -> None:
    image_path = ASSETS_DIR / f"{slug}.png"
    story.append(fit_image(image_path, max_width=17.2 * cm))
    story.append(p(caption, "Caption"))


def add_function_block(
    story: list,
    title: str,
    relative_path: str,
    line_span: str,
    summary: str,
    notes: list[tuple[str, str]],
    screenshot_slug: str | None = None,
) -> None:
    story.append(p(title, "SubsectionTitle"))
    story.append(p(f"Fichier: {relative_path} | Lignes: {line_span}", "BodySmall"))
    story.append(p(summary))
    if screenshot_slug:
        add_screenshot(story, screenshot_slug, f"Capture de code: {title}")
    table_rows = [["Lignes", "Explication"], *[[lines, description] for lines, description in notes]]
    story.append(make_table(table_rows, [2.2 * cm, 14.7 * cm]))
    story.append(Spacer(1, 0.18 * cm))


def add_endpoint_table(story: list) -> None:
    rows = [
        ["Endpoint", "Role"],
        ["GET /live-events", "Retourne toutes les live rooms, triees avec les rooms live en tete et le viewer_count calcule a chaud."],
        ["GET /live-events/{event_id}", "Charge le detail d'une room: metadonnees, updates recentes et chat recent."],
        ["POST /live-events", "Creation d'une room par un utilisateur ayant le role editor."],
        ["POST /live-events/{event_id}/start", "Passe la room en statut live et notifie les clients via WebSocket."],
        ["POST /live-events/{event_id}/end", "Passe la room en statut ended et emet stream_ended."],
        ["DELETE /live-events/{event_id}", "Supprime la room et ses messages associes."],
        ["WS /ws/live-events/{event_id}?token=...", "Canal temps reel pour chat, updates, viewer_count et signalisation WebRTC."],
    ]
    story.append(make_table(rows, [5.4 * cm, 11.5 * cm]))


def add_socket_message_table(story: list) -> None:
    rows = [
        ["Message", "Emetteur", "Recepteur", "Utilite dans le projet"],
        ["socket_ready", "Serveur", "Client qui vient de se connecter", "Confirme l'ouverture de la socket, attribue clientId et renvoie le status courant de la room."],
        ["viewer_count", "Serveur", "Tous les clients de la room", "Met a jour le compteur de connexions WebSocket actives."],
        ["room_status", "Serveur", "Tous les clients", "Informe qu'une room passe a live ou ended."],
        ["chat_message", "Client -> serveur -> room", "Tous les clients", "Diffuse un message de chat persiste en base."],
        ["live_update", "Editeur -> serveur -> room", "Tous les clients", "Diffuse une update officielle de l'editeur, egalement persistee."],
        ["broadcaster_ready", "Editeur", "Lecteurs", "Annonce que l'editeur a demarre la diffusion camera et que les lecteurs peuvent demander une connexion WebRTC."],
        ["viewer_joined", "Lecteur", "Editeur", "Signale qu'un lecteur veut recevoir un flux video."],
        ["offer", "Editeur", "Lecteur cible", "Premier SDP de negotiation WebRTC."],
        ["answer", "Lecteur", "Editeur cible", "Reponse SDP a l'offre recue."],
        ["ice_candidate", "Editeur ou lecteur", "Pair cible", "Echange des candidats ICE pour trouver un chemin reseau valide."],
        ["stream_ended", "Editeur ou serveur", "Tous les clients", "Indique l'arret du flux camera et provoque le nettoyage cote front."],
    ]
    story.append(make_table(rows, [2.9 * cm, 3.2 * cm, 3.3 * cm, 7.7 * cm]))


def add_persistent_vs_transient_table(story: list) -> None:
    rows = [
        ["Element", "Stockage", "Commentaire"],
        ["LiveEvent", "Base SQL", "La room existe meme hors connexion WebSocket."],
        ["LiveMessage type=chat", "Base SQL", "Les messages de chat sont persists puis rebroadcastes."],
        ["LiveMessage type=update", "Base SQL", "Les updates officielles sont conservees comme historique editorial."],
        ["viewer_count", "Memoire serveur", "Valeur a chaud calculee a partir de live_room_manager.connections."],
        ["clientId socket", "Memoire serveur", "UUID genere a chaque connexion WebSocket."],
        ["RTCPeerConnection", "Memoire navigateur", "Objet purement client pour la negotiation et le transport media."],
        ["MediaStream local/remote", "Memoire navigateur", "Flux camera/micro de l'editeur et flux distant du lecteur."],
    ]
    story.append(make_table(rows, [4.2 * cm, 3.2 * cm, 9.4 * cm]))


def build_story() -> list:
    story: list = []
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    story.append(Spacer(1, 1.4 * cm))
    story.append(p("Documentation technique tres detaillee du module live NewsHub", "DocTitle"))
    story.append(
        p(
            "Explication complete du fonctionnement du live, du moment exact ou un utilisateur rejoint le direct, "
            "du role de chaque fonction, et de l'usage combine de WebSocket et WebRTC.",
            "DocSubtitle",
        )
    )
    story.append(
        p(
            f"Document genere le {generated_at}. Cette documentation cible la partie live du projet present dans "
            f"{ROOT}.",
            "CoverNote",
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(line_rule())
    story.append(Spacer(1, 0.25 * cm))
    story.append(
        p(
            "Ce PDF couvre: le parcours utilisateur depuis /live jusqu'a la reception du flux video, le contrat de "
            "messages temps reel, les endpoints REST, les modeles de donnees, les captures de code les plus "
            "importantes, et une lecture pas a pas de toutes les fonctions pertinentes de la fonctionnalite live.",
            "CoverNote",
        )
    )
    story.append(Spacer(1, 0.6 * cm))
    story.append(
        Table(
            [
                [
                    p("Contenu principal", "MiniNote"),
                    p("Valeur", "MiniNote"),
                ],
                [p("Partie front", "BodySmall"), p("Angular: routes, services, hub live, live room, WebRTC cote navigateur", "BodySmall")],
                [p("Partie back", "BodySmall"), p("FastAPI: endpoints REST, WebSocket, guard d'acces, manager de connexions", "BodySmall")],
                [p("Temps reel", "BodySmall"), p("WebSocket pour le controle; WebRTC pour l'audio/video", "BodySmall")],
                [p("Format de lecture", "BodySmall"), p("Explication architecturale + lecture ligne par ligne des blocs majeurs", "BodySmall")],
            ],
            colWidths=[4.5 * cm, 12.0 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eff6ff")),
                    ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )

    story.append(PageBreak())
    story.append(p("1. Vue d'ensemble de l'architecture live", "SectionTitle"))
    story.append(
        p(
            "Le module live de NewsHub est volontairement separe en deux couches temps reel distinctes. La premiere "
            "couche est WebSocket: elle sert au controle de session, au chat, aux updates editoriales, au compteur de "
            "viewers et a la signalisation WebRTC. La seconde couche est WebRTC: elle sert exclusivement au transport "
            "du media, donc a la camera et au microphone de l'editeur vers les viewers."
        )
    )
    story.append(
        p(
            "Cette separation est importante. Le bouton Start live room ne transporte aucune video. Il bascule "
            "seulement la room en statut live via REST, puis le serveur pousse room_status aux clients connectes. "
            "La video ne demarre que quand l'editeur clique sur Go live with camera. A ce moment, la page met "
            "isBroadcasting a true, envoie broadcaster_ready via WebSocket, puis la sequence Offer / Answer / ICE "
            "du WebRTC peut commencer."
        )
    )
    story.append(make_architecture_drawing())
    story.append(p("Schema simplifie de la separation entre couche de controle et couche media.", "Caption"))

    story.append(p("Fichiers pivots du module", "SubsectionTitle"))
    for item in [
        "frontend/src/app/app.routes.ts ouvre les routes /live et /live/:id.",
        "frontend/src/app/core/models/live-event.model.ts fixe le contrat de donnees et le catalogue de messages socket.",
        "frontend/src/app/core/services/live-events.ts encapsule les appels REST du module.",
        "frontend/src/app/core/services/live-room-socket.ts ouvre le canal WebSocket et publie les evenements au composant.",
        "frontend/src/app/features/live/live-hub-page/live-hub-page.ts gere la creation et la liste des rooms.",
        "frontend/src/app/features/live/live-room-page/live-room-page.ts contient la logique metier centrale du lecteur, de l'editeur et du WebRTC.",
        "backend/models.py contient LiveEvent et LiveMessage.",
        "backend/main.py contient les endpoints REST live, le manager WebSocket et l'endpoint /ws/live-events/{event_id}.",
    ]:
        story.append(bullet(item))

    story.append(Spacer(1, 0.2 * cm))
    story.append(p("API live exposee par le backend", "SubsectionTitle"))
    add_endpoint_table(story)

    story.append(Spacer(1, 0.3 * cm))
    story.append(p("Messages temps reel du projet", "SubsectionTitle"))
    add_socket_message_table(story)

    story.append(Spacer(1, 0.3 * cm))
    story.append(p("Ce qui est persistant et ce qui est seulement en memoire", "SubsectionTitle"))
    add_persistent_vs_transient_table(story)

    story.append(PageBreak())
    story.append(p("2. Moment exact ou un utilisateur rejoint le live", "SectionTitle"))
    story.append(
        p(
            "La question la plus importante du projet live est la suivante: a quel moment le lecteur rejoint-il "
            "vraiment le direct ? Dans ce code, il existe en realite trois niveaux de jonction. Niveau 1: "
            "l'utilisateur ouvre la room sur la route /live/:id. Niveau 2: il rejoint logiquement la room quand la "
            "connexion WebSocket est acceptee et qu'il recoit le message socket_ready. Niveau 3: il rejoint "
            "visuellement le direct quand le flux WebRTC arrive dans le gestionnaire ontrack et que "
            "remoteVideo.srcObject recoit remoteStream."
        )
    )
    story.append(
        p(
            "Autrement dit, une room peut etre live sans que la video soit encore visible. C'est un detail tres "
            "important du projet: le statut de la room, le chat et les updates passent avant la connexion video. "
            "Le lecteur n'obtient le media que si l'editeur a effectivement active la camera et si la sequence "
            "viewer_joined -> offer -> answer -> ice_candidate -> ontrack s'est correctement terminee."
        )
    )
    story.append(make_join_flow_drawing())
    story.append(p("Sequence logique complete qui mene le lecteur jusqu'au flux video.", "Caption"))

    story.append(p("Chronologie detaillee", "SubsectionTitle"))
    for item in [
        "Le lecteur ouvre /live/:id. Angular lit l'id de route puis charge le detail de la room via getLiveEventById.",
        "Le composant evalue canJoinLiveRoom. S'il n'y a pas de session, showLoginGate s'affiche. Si la room est premium et que l'utilisateur n'est pas premium, showPremiumGate s'affiche.",
        "Quand canJoinLiveRoom devient vrai et qu'un JWT valide existe, attemptSocketConnection ouvre la connexion WebSocket.",
        "Le serveur valide le token, verifie que la room existe et controle l'acces premium via can_access_live_event.",
        "Apres accept(), le serveur renvoie socket_ready. A ce stade, le lecteur a rejoint la room logique et recupere clientId, viewerCount et le statut actuel.",
        "Si la room est deja en statut live, handleSocketEvent appelle requestViewerConnection. Sinon, le lecteur attend room_status ou broadcaster_ready.",
        "Quand l'editeur diffuse vraiment sa camera, il envoie broadcaster_ready. Les lecteurs redemandent alors une connexion en envoyant viewer_joined.",
        "L'editeur cree une offre SDP pour ce lecteur, le lecteur renvoie une answer, puis les deux cotes echangent les candidats ICE.",
        "Le moment precis ou le direct apparait est l'evenement ontrack dans createViewerPeerConnection. C'est la que remoteStream est affecte et que la video devient visible.",
    ]:
        story.append(bullet(item))

    story.append(Spacer(1, 0.3 * cm))
    story.append(p("Difference essentielle entre Start live room et Go live with camera", "SubsectionTitle"))
    story.append(
        p(
            "Start live room modifie l'etat metier de la room en base et le serveur diffuse room_status = live. "
            "Go live with camera ne touche pas la base: il active la partie media cote front, pose isBroadcasting = true "
            "et envoie broadcaster_ready. Cette separation explique pourquoi un utilisateur peut voir 'The room is live' "
            "tout en attendant encore le message 'Waiting for the editor camera stream'."
        )
    )

    story.append(PageBreak())
    story.append(p("3. Pourquoi le projet utilise WebSocket et WebRTC en meme temps", "SectionTitle"))
    story.append(
        p(
            "Dans NewsHub, WebSocket est la couche de pilotage et WebRTC est la couche de transport audio/video. "
            "Cette architecture est saine: le serveur garde le controle de la room, du droit d'acces et de l'historique "
            "de messages, tandis que le navigateur optimise le transport media entre l'editeur et chaque lecteur."
        )
    )
    story.append(
        p(
            "WebSocket est bien adapte aux petits messages JSON de faible taille: chat_message, live_update, room_status, "
            "viewer_count, viewer_joined, offer, answer et ice_candidate. WebRTC, lui, est concu pour des pistes media "
            "temps reel, avec negotiation SDP, ICE et STUN. Le code montre bien cette repartition: aucune frame video "
            "n'est envoyee dans la WebSocket; seules les informations de controle et de signalisation y passent."
        )
    )
    comparison_rows = [
        ["Technologie", "Role dans NewsHub", "Pourquoi elle est utile ici"],
        ["REST HTTP", "Creer, lister, demarrer, terminer et supprimer les rooms; charger l'etat initial", "Adaptation naturelle aux actions metier et a la persistence en base."],
        ["WebSocket", "Chat, updates, viewer_count, room_status et signalisation WebRTC", "Canal bidirectionnel continu, leger, centralise par le serveur."],
        ["WebRTC", "Transport du flux camera/micro de l'editeur", "Faible latence, adaptation aux flux media, API native des navigateurs."],
    ]
    story.append(make_table(comparison_rows, [3.2 * cm, 5.8 * cm, 8.0 * cm]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(p("Ce que fait exactement WebSocket dans votre code", "SubsectionTitle"))
    for item in [
        "Il authentifie l'entree dans la room grace au token passe dans l'URL ?token=....",
        "Il attribue un clientId unique par connexion.",
        "Il calcule le viewer_count et le diffuse a tous.",
        "Il persiste le chat et les updates via LiveMessage cote serveur.",
        "Il transporte les messages de signalisation WebRTC sans porter la video elle-meme.",
    ]:
        story.append(bullet(item))

    story.append(p("Ce que fait exactement WebRTC dans votre code", "SubsectionTitle"))
    for item in [
        "Il cree une RTCPeerConnection cote editeur pour chaque lecteur actif dans broadcasterPeerConnections.",
        "Il cree une seule viewerPeerConnection cote lecteur pour recevoir le flux de l'editeur.",
        "Il utilise le serveur STUN public stun.l.google.com:19302 pour la decouverte reseau.",
        "Il ajoute les pistes de localStream avec addTrack cote editeur.",
        "Il declenche ontrack cote lecteur quand le flux distant devient disponible.",
    ]:
        story.append(bullet(item))

    story.append(p("Observations techniques sur l'implementation actuelle", "SubsectionTitle"))
    for item in [
        "Le champ stream_url existe dans LiveEvent, mais le flux actuel ne l'utilise pas: la diffusion reelle passe par la camera WebRTC du navigateur.",
        "Le serveur STUN est configure, mais aucun TURN n'est defini. Dans des reseaux tres contraints, certains lecteurs peuvent donc rencontrer des limites de connexion.",
        "Le compteur viewer_count compte les sockets actives, pas seulement les lecteurs ayant deja recu un flux video.",
        "Le service WebSocket Angular n'implemente pas de logique explicite onclose, onerror ou de reconnexion automatique.",
        "Le choix d'une connexion editeur -> une RTCPeerConnection par lecteur est simple et lisible, mais charge davantage la machine de l'editeur si l'audience augmente beaucoup.",
    ]:
        story.append(bullet(item))

    story.append(PageBreak())
    story.append(p("4. Captures de code principales", "SectionTitle"))
    story.append(
        p(
            "Les captures ci-dessous servent d'ancrage visuel. Elles reprennent les blocs les plus importants du projet "
            "live et seront detaillees ensuite ligne par ligne."
        )
    )
    add_screenshot(story, "routes_live", "Routes Angular qui ouvrent le hub live et la room live.")
    add_screenshot(story, "live_model_socket_contract", "Union TypeScript qui decrit tous les evenements WebSocket du module.")
    add_screenshot(story, "socket_service", "Service Angular qui convertit l'URL HTTP en URL WebSocket et ouvre la connexion.")
    add_screenshot(story, "live_hub_create", "Bloc de creation d'une room depuis le hub live.")
    add_screenshot(story, "room_init_and_access", "Initialisation de la room et calcul des droits d'acces.")
    add_screenshot(story, "editor_actions", "Actions front de l'editeur: preview camera, start, go live, end, updates et chat.")
    add_screenshot(story, "socket_orchestration", "Traitement des evenements socket dans le composant de room.")
    add_screenshot(story, "webrtc_signaling_frontend", "Blocs Angular qui realisent la negotiation WebRTC.")
    add_screenshot(story, "backend_models", "Modeles SQLAlchemy qui representent room et messages live.")
    add_screenshot(story, "backend_manager", "Gestionnaire serveur des connexions temps reel.")
    add_screenshot(story, "backend_rest_live", "Endpoints REST de creation, start, end et delete.")
    add_screenshot(story, "backend_websocket_guard", "Validation serveur avant acceptation de la socket.")
    add_screenshot(story, "backend_websocket_messages", "Traitement serveur des messages chat, update et broadcaster_ready.")
    add_screenshot(story, "backend_websocket_signaling", "Relai serveur des messages WebRTC et nettoyage final.")

    story.append(PageBreak())
    story.append(p("5. Lecture detaillee du frontend", "SectionTitle"))

    add_function_block(
        story,
        title="5.1 Routage live Angular",
        relative_path="frontend/src/app/app.routes.ts",
        line_span="23-30",
        summary="Ce bloc branche le module live dans le routeur Angular. C'est le premier point d'entree du parcours utilisateur.",
        notes=[
            ("23-26", "La route /live charge LiveHubPageComponent. C'est la page catalogue des rooms, avec eventuellement le formulaire de creation si l'utilisateur est editor."),
            ("27-30", "La route /live/:id charge LiveRoomPageComponent. La room se base ensuite sur cet id pour charger les details et ouvrir la socket ciblee."),
        ],
        screenshot_slug="routes_live",
    )

    add_function_block(
        story,
        title="5.2 Structures LiveEvent et payload de creation",
        relative_path="frontend/src/app/core/models/live-event.model.ts",
        line_span="1-40",
        summary="Le debut du fichier decrit les structures metier principales de la partie live cote frontend.",
        notes=[
            ("1", "LiveEventStatus limite les etats possibles a upcoming, live et ended. Cette union simplifie les controles d'interface et reduit les fautes de frappe."),
            ("3-10", "LiveMessage decrit un message persiste par le backend. Le front ne distingue que deux types: chat et update."),
            ("12-27", "LiveEvent porte la metadonnee de room. viewer_count est fourni par le serveur, tandis que stream_url est present mais n'alimente pas la diffusion WebRTC actuelle."),
            ("29-32", "LiveEventDetail enrichit la room avec deux listes: updates et chat_messages. C'est la forme renvoyee par GET /live-events/{id}."),
            ("34-40", "CreateLiveEventPayload est le contrat d'entree pour la creation d'une room depuis le hub."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="5.3 Contrat exact des messages socket",
        relative_path="frontend/src/app/core/models/live-event.model.ts",
        line_span="43-92",
        summary="Cette capture montre uniquement l'union TypeScript LiveSocketEvent. Le tableau ci-dessous explique exactement les lignes visibles dans l'image.",
        notes=[
            ("43-50", "Premiere variante: socket_ready. Le serveur renvoie clientId, viewerCount, status et isEditor juste apres l'ouverture de la WebSocket."),
            ("51-58", "viewer_count et room_status servent a synchroniser l'etat global de la room sans recharger la page."),
            ("59-66", "chat_message et live_update encapsulent un LiveMessage complet pour pouvoir mettre a jour l'interface immediatement."),
            ("67-74", "broadcaster_ready et viewer_joined pilotent l'amorcage du flux video. Le premier annonce que l'editeur diffuse; le second demande un flux."),
            ("75-84", "offer et answer transportent les descriptions SDP necessaires a la negotiation WebRTC."),
            ("85-92", "ice_candidate et stream_ended terminent respectivement la decouverte reseau et l'arret propre du flux."),
        ],
        screenshot_slug="live_model_socket_contract",
    )

    add_function_block(
        story,
        title="5.4 Service REST live Angular",
        relative_path="frontend/src/app/core/services/live-events.ts",
        line_span="14-40",
        summary="Ce service isole toutes les requetes HTTP du module live. Il garde le composant propre et concentre les URLs dans un seul endroit.",
        notes=[
            ("15-16", "Le service injecte HttpClient et construit apiBaseUrl a partir de environment.backendApiBaseUrl + /live-events."),
            ("18-20", "getLiveEvents() appelle GET /live-events pour afficher la liste du hub."),
            ("22-24", "getLiveEventById(eventId) charge le detail d'une room ouverte par le routeur."),
            ("26-28", "createLiveEvent(payload) poste la room au backend. Le JWT sera ajoute automatiquement par l'interceptor HTTP."),
            ("30-32", "startLiveEvent(eventId) bascule la room a live. Cette action ne diffuse pas encore de video."),
            ("34-36", "endLiveEvent(eventId) ferme metierement la room et declenche ensuite des notifications socket cote serveur."),
            ("38-40", "deleteLiveEvent(eventId) supprime une room existante."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="5.5 Service WebSocket Angular",
        relative_path="frontend/src/app/core/services/live-room-socket.ts",
        line_span="9-39",
        summary="Ce service maintient le canal bidirectionnel temps reel et transforme les messages JSON en observable RxJS.",
        notes=[
            ("10-13", "socket conserve l'instance WebSocket active, tandis que eventsSubject sert de pont vers le composant via events$."),
            ("15-16", "connect(roomId, token) commence par fermer proprement une ancienne socket pour eviter les doubles connexions."),
            ("18-20", "Le code convertit l'URL backend HTTP en WS, ajoute l'id de room et le token encode dans la query string, puis ouvre la WebSocket."),
            ("22-25", "Chaque message recu est parse en JSON puis publie dans eventsSubject pour que LiveRoomPageComponent le traite."),
            ("28-34", "send(payload) refuse d'envoyer si la socket n'est pas OPEN; cela evite des erreurs quand l'etat reseau n'est pas encore pret."),
            ("36-39", "disconnect() ferme la socket puis remet la reference a null."),
        ],
        screenshot_slug="socket_service",
    )

    add_function_block(
        story,
        title="5.6 Service d'authentification utile au live",
        relative_path="frontend/src/app/core/services/auth/auth.ts",
        line_span="16-31, 38-49, 80-99",
        summary="Le module live depend de deux comportements d'AuthService: la diffusion de currentUser$ et la recuperation d'un JWT encore valide pour la WebSocket.",
        notes=[
            ("16-31", "Le constructeur recharge l'utilisateur et le token depuis localStorage. Si l'etat est incoherent ou si le token est expire, il nettoie le stockage et republie un utilisateur null."),
            ("38-49", "getToken() est critique pour le live: sans JWT valide, attemptSocketConnection ne peut pas ouvrir /ws/live-events/{id}."),
            ("44-46", "Si le token est expire, le service deconnecte l'utilisateur avant de renvoyer null."),
            ("80-99", "isTokenExpired() decode le JWT cote navigateur, lit exp et compare a Date.now(). Cette verification se fait avant l'ouverture WebSocket."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="5.7 Vue d'ensemble de LiveHubPageComponent",
        relative_path="frontend/src/app/features/live/live-hub-page/live-hub-page.ts",
        line_span="28-75 et 120-162",
        summary="Le hub live est la porte d'entree du module. Cette partie couvre les etats, les permissions et le chargement de la liste, hors bloc exact de creation.",
        notes=[
            ("29-32", "Le composant injecte AuthService, LiveEventsService, FormBuilder et Router."),
            ("34-40", "Ces etats pilotent la page: utilisateur courant, rooms chargees, loading, erreurs, creation en cours et suppression en cours."),
            ("42-58", "categories et createForm definissent les options de creation. premiumOnly vaut true par defaut, ce qui montre que la fonctionnalite vise surtout le public premium."),
            ("60-65", "ngOnInit() s'abonne a currentUser$ puis lance loadLiveEvents(). Le hub ne depend pas du live en cours pour exister."),
            ("68-70", "isEditor est un getter simple mais essentiel pour masquer ou afficher les outils de creation."),
            ("72-74", "isOwnedByCurrentEditor(event) verifie qu'une room appartient a l'editeur courant, utile pour afficher le bouton Delete."),
            ("120-145", "deleteLiveRoom(event) demande une confirmation, appelle le backend puis retire la room de liveEvents si la suppression reussit."),
            ("147-162", "loadLiveEvents() charge le catalogue des rooms et gere les etats loading/error du hub."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="5.8 Creation d'une room depuis le hub",
        relative_path="frontend/src/app/features/live/live-hub-page/live-hub-page.ts",
        line_span="76-117",
        summary="Cette capture correspond uniquement a la fonction createLiveRoom(), donc le tableau ci-dessous explique exactement les lignes visibles dans l'image.",
        notes=[
            ("76-79", "La creation est refusee si l'utilisateur courant n'est pas editor."),
            ("81-86", "Le code vide createError puis valide le formulaire. En cas d'erreur, markAllAsTouched() force l'affichage des validations."),
            ("88-99", "Le formulaire est lu, normalise avec trim() puis envoye a createLiveEvent()."),
            ("100-117", "En succes, le formulaire est reinitialise puis l'utilisateur est redirige vers /live/{event.id}. En erreur, createError est alimente avec le message du backend."),
        ],
        screenshot_slug="live_hub_create",
    )

    add_function_block(
        story,
        title="5.9 LiveRoomPageComponent: cycle de vie et controle d'acces",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        line_span="80-156",
        summary="Ce bloc decide si l'utilisateur peut entrer, quand la socket doit s'ouvrir et quels panneaux d'interface doivent s'afficher.",
        notes=[
            ("80-84", "ngOnInit() memorise l'URL courante pour un retour apres login puis s'abonne au flux events$ du service WebSocket."),
            ("86-94", "Le composant s'abonne a currentUser$. Si l'utilisateur disparait, disconnectSocket() est appele. Sinon, on tente une connexion socket."),
            ("96-103", "L'id de route est lu depuis ActivatedRoute. Sans id valide, la room s'arrete immediatement avec une erreur."),
            ("106-109", "ngAfterViewInit() essaye de binder les flux video aux balises video des que la vue existe."),
            ("111-116", "ngOnDestroy() desabonne, coupe la diffusion locale si necessaire et ferme la socket."),
            ("118-128", "isPremiumUser, isEditor et isRoomEditor definissent les roles de base. isRoomEditor exige a la fois le role editor et la propriete editor_user_id de la room."),
            ("130-140", "canJoinLiveRoom() contient la vraie regle d'entree: il faut un currentUser et une room; l'editeur proprietaire entre toujours; sinon le premium est verifie si la room est premium_only."),
            ("142-148", "showLoginGate et showPremiumGate pilotent l'affichage des portes d'entree UI."),
            ("150-155", "canSendChat et hasRemoteStream sont des raccourcis de confort pour les boutons et overlays."),
        ],
        screenshot_slug="room_init_and_access",
    )

    add_function_block(
        story,
        title="5.10 Actions de l'editeur et du chat dans la room",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        line_span="158-305",
        summary="Ici se trouvent les actions que l'utilisateur voit directement: camera preview, start de la room, bascule camera live, end, delete, updates editoriales et chat.",
        notes=[
            ("158-180", "prepareCamera() n'est autorise que pour l'editeur proprietaire. Elle ouvre getUserMedia(video+audio), prepare localStream, active isCameraPrepared puis met a jour le message d'etat."),
            ("182-205", "startLiveRoom() appelle l'endpoint REST /start. Son but est uniquement de faire passer le statut de la room a live et de mettre a jour l'interface."),
            ("207-223", "goLiveWithCamera() exige une room, un editeur et un localStream. Elle met isBroadcasting a true puis envoie broadcaster_ready. C'est l'etape qui lance la partie media."),
            ("225-250", "endLiveRoom() coupe d'abord la diffusion locale avec stopCameraBroadcast(), puis appelle l'endpoint /end pour clore la session cote metier."),
            ("252-279", "deleteLiveRoom() confirme l'action, coupe le broadcast, ferme la socket, supprime la room via REST puis renvoie vers /live."),
            ("281-292", "publishEditorUpdate() envoie live_update sur la socket seulement si le texte n'est pas vide, si l'utilisateur est l'editeur et si la socket est prete."),
            ("294-305", "sendChatMessage() envoie chat_message a la room. Le front n'ecrit pas localement le message tant que le serveur ne l'a pas rebroadcast."),
        ],
        screenshot_slug="editor_actions",
    )

    add_function_block(
        story,
        title="5.11 Chargement de room et orchestration des evenements socket",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        line_span="307-463",
        summary="Ce bloc est le cerveau du composant. Il charge la room, ouvre la WebSocket au bon moment, puis route chaque message vers l'action a entreprendre.",
        notes=[
            ("307-331", "loadLiveRoom(eventId) recupere le detail depuis le backend, alimente event, updates, chatMessages et fixe le texte d'etat selon upcoming/live/ended."),
            ("325", "Une fois la room chargee, attemptSocketConnection() est appele. La connexion temps reel depend donc d'abord du chargement metier."),
            ("333-346", "attemptSocketConnection() coupe toute tentative si la room n'est pas chargee, si l'utilisateur n'est pas logge, si l'acces n'est pas autorise, ou si une connexion existe deja."),
            ("338-340", "Le JWT est recupere via AuthService.getToken(). La WebSocket privee est donc strictement liee a une session valide."),
            ("343-345", "Le label UI passe a Connecting..., puis le service ouvre /ws/live-events/{id}?token=..."),
            ("348-354", "disconnectSocket() reinitialise l'etat local avant de fermer la socket reelle."),
            ("361-375", "Branche socket_ready: la room recupere clientId, passe a l'etat Connected, met a jour viewer_count et status, puis un viewer demande immediatement une connexion si la room est deja live."),
            ("378-384", "Branche viewer_count: met simplement a jour le compteur affiche."),
            ("386-401", "Branche room_status: si live, le message visuel change et le viewer essaie requestViewerConnection(); si ended, le flux distant est nettoye."),
            ("404-412", "chat_message et live_update alimentent respectivement chatMessages et updates."),
            ("414-420", "broadcaster_ready signifie que l'editeur diffuse sa camera. Le viewer remet hasRequestedViewerConnection a false puis relance requestViewerConnection() pour declencher la negotiation."),
            ("422-429", "viewer_joined et offer etablissent le basculement vers WebRTC: l'editeur cree une offre pour le viewer; le viewer la traite."),
            ("432-456", "answer et ice_candidate terminent la negotiation progressive des pairs."),
            ("459-462", "stream_ended remet l'interface viewer en mode attente et supprime remoteStream."),
        ],
        screenshot_slug="socket_orchestration",
    )

    add_function_block(
        story,
        title="5.12 Signalisation WebRTC cote Angular",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        line_span="465-563",
        summary="Ces fonctions transforment les messages WebSocket en vraie session WebRTC et branchent la video entre navigateur editeur et navigateur viewer.",
        notes=[
            ("465-474", "requestViewerConnection() ne s'execute que pour un viewer, avec socket prete, et une seule fois a la fois. Elle envoie viewer_joined au serveur."),
            ("476-490", "createOfferForViewer(targetClientId) cree une offre SDP a partir de la RTCPeerConnection de l'editeur et l'envoie au viewer cible."),
            ("492-500", "createBroadcasterPeerConnection() reutilise une connexion existante si elle existe deja; sinon il cree une nouvelle RTCPeerConnection avec un serveur STUN public."),
            ("502-504", "Toutes les pistes du localStream sont ajoutees a la connexion. C'est ici que la camera et le micro de l'editeur deviennent partageables."),
            ("506-516", "onicecandidate capture chaque candidat ICE et le renvoie via WebSocket au viewer cible."),
            ("518-519", "La connexion editeur est conservee dans broadcasterPeerConnections, une map par viewer."),
            ("522-534", "handleViewerOffer(senderClientId, sdp) cree ou recupere la connexion viewer, applique l'offre distante, cree une answer puis la renvoie."),
            ("536-543", "createViewerPeerConnection() garantit une unique connexion cote viewer."),
            ("545-549", "ontrack est le point exact d'arrivee du flux. remoteStream recoit event.streams[0], bindRemoteStream() affecte la balise video et le texte d'etat passe a Connected to the editor video stream."),
            ("551-560", "Le viewer renvoie aussi ses candidats ICE via WebSocket."),
        ],
        screenshot_slug="webrtc_signaling_frontend",
    )

    add_function_block(
        story,
        title="5.13 Nettoyage des flux et liaison aux balises video",
        relative_path="frontend/src/app/features/live/live-room-page/live-room-page.ts",
        line_span="566-619",
        summary="Ce dernier bloc ferme proprement les flux et raccorde les MediaStream aux elements HTMLVideoElement.",
        notes=[
            ("566-585", "stopCameraBroadcast() annonce stream_ended s'il existait une diffusion, remet les drapeaux de camera a false, ferme les peer connections de l'editeur, stoppe les tracks locales et nettoie la video locale."),
            ("587-590", "closeBroadcasterPeerConnections() ferme toutes les connexions editeur -> viewer puis vide la map."),
            ("592-600", "clearRemoteViewerState() remet le viewer dans un etat sans flux: la connexion est closee, remoteStream est null et la balise video est videe."),
            ("603-610", "bindLocalStream() attache localStream a la video locale puis essaye de lancer play()."),
            ("612-619", "bindRemoteStream() fait la meme chose pour remoteStream cote viewer."),
        ],
        screenshot_slug=None,
    )

    story.append(PageBreak())
    story.append(p("6. Lecture detaillee du backend", "SectionTitle"))

    add_function_block(
        story,
        title="6.1 Modeles SQLAlchemy du live",
        relative_path="backend/models.py",
        line_span="96-127",
        summary="Le backend stocke la room et les messages dans deux tables simples. Toute la negotiation WebRTC reste hors base et vit uniquement en memoire navigateur/serveur.",
        notes=[
            ("96-110", "LiveEvent contient les metadonnees de la room: titre, description, categorie, image, stream_url, status, premium_only, l'editeur proprietaire et les timestamps de vie."),
            ("112-113", "Les relations editor et messages relient la room au User proprietaire et a l'historique des messages."),
            ("116-124", "LiveMessage stocke chaque message avec son live_event_id, son user_id, son type et son contenu."),
            ("126-127", "Les relations renvoient vers la room et vers l'utilisateur auteur."),
        ],
        screenshot_slug="backend_models",
    )

    add_function_block(
        story,
        title="6.2 Schemas Pydantic utiles au live",
        relative_path="backend/schemas.py",
        line_span="114-124",
        summary="Les schemas de creation sont volontairement legers: la vraie complexite du temps reel ne passe pas par Pydantic mais par la WebSocket.",
        notes=[
            ("114-120", "CreateLiveEventRequest exige titre, description, categorie, accepte optionnellement cover_image et stream_url, puis premium_only."),
            ("123-124", "CreateLiveMessageRequest ne contient qu'un content. Dans la pratique, le projet utilise surtout des payloads JSON recus dans la WebSocket."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="6.3 Authentification et garde d'acces cote serveur",
        relative_path="backend/main.py",
        line_span="141-179",
        summary="Avant de laisser entrer un client dans la room, le serveur valide le JWT, verifie le role editor si necessaire, puis controle l'acces premium.",
        notes=[
            ("141-152", "get_current_user_from_token(token, db) decode le JWT, retrouve ou cree l'utilisateur et renvoie un objet User exploitable par la WebSocket."),
            ("160-162", "ensure_editor(current_user) garantit que certaines actions sensibles restent reservees au role editor."),
            ("165-168", "ensure_live_room_editor(live_event, current_user) ajoute une verification de propriete: la room doit appartenir a cet editeur."),
            ("171-179", "can_access_live_event(live_event, current_user) autorise toujours l'editeur proprietaire, puis applique la regle premium_only pour les autres."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="6.4 Serialization des messages live",
        relative_path="backend/main.py",
        line_span="232-240",
        summary="Cette petite fonction convertit un LiveMessage SQLAlchemy en dictionnaire JSON exploitable par le frontend.",
        notes=[
            ("232-240", "serialize_live_message() expose id, message_type, contenu, date ISO, user_id et user_name. Ce format est ensuite reemploye dans chat_message et live_update."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="6.5 LiveRoomManager: connexions WebSocket en memoire",
        relative_path="backend/main.py",
        line_span="243-302",
        summary="Cette capture correspond exactement au gestionnaire en memoire des connexions WebSocket par room.",
        notes=[
            ("243-245", "Le constructeur initialise connections comme un dictionnaire de rooms, chacune contenant un sous-dictionnaire clientId -> meta connexion."),
            ("247-254", "connect(room_id, websocket, user) cree un clientId UUID et l'enregistre avec le socket, l'user_id et le role."),
            ("256-263", "disconnect(room_id, client_id) retire une connexion. Si la room n'a plus aucun client, elle est supprimee du manager."),
            ("265-266", "get_viewer_count(room_id) compte les connexions actives pour cette room."),
            ("268-282", "broadcast(room_id, payload, exclude_client_id) envoie un JSON a tous les clients de la room, avec possibilite d'exclure l'emetteur. Les sockets cassees sont nettoyees ensuite."),
            ("284-293", "send_to_client(room_id, client_id, payload) permet le routage cible vers un pair precis, indispensable pour offer, answer et ice_candidate."),
            ("295-302", "broadcast_viewer_count(room_id) diffuse le compteur a tous les clients de la room."),
        ],
        screenshot_slug="backend_manager",
    )

    add_function_block(
        story,
        title="6.6 Serialization des rooms et de leur detail",
        relative_path="backend/main.py",
        line_span="308-343",
        summary="Ces fonctions transforment une room en JSON simple ou detaille, avec injection du compteur de connexions actives.",
        notes=[
            ("308-324", "serialize_live_event() expose la room avec viewer_count injecte depuis la memoire et les timestamps ISO."),
            ("327-343", "serialize_live_event_detail() separe l'historique update de l'historique chat et ne renvoie que les 30 updates et 40 messages les plus recents."),
        ],
        screenshot_slug=None,
    )

    add_function_block(
        story,
        title="6.7 Endpoints REST du module live",
        relative_path="backend/main.py",
        line_span="410-579",
        summary="La couche REST pilote le cycle de vie metier de la room. Elle ne transporte pas le flux camera, mais fixe le contexte a partir duquel le temps reel fonctionne.",
        notes=[
            ("410-424", "list_live_events() recupere les rooms triees en mettant les rooms live en premier et injecte viewer_count a la volee."),
            ("427-433", "get_live_event(event_id) charge le detail d'une room unique ou renvoie 404 si elle n'existe pas."),
            ("436-476", "create_live_event() verifie que l'utilisateur est editor, nettoie les champs, cree la room avec status='upcoming' puis la persiste."),
            ("479-512", "start_live_event() verifie la room et l'editeur proprietaire, passe status='live', renseigne started_at, commit puis broadcast room_status=live a la room."),
            ("515-553", "end_live_event() passe status='ended', renseigne ended_at, broadcast room_status=ended puis broadcast stream_ended."),
            ("556-579", "delete_live_event() supprime la room en base et nettoie les connexions en memoire pour cette room."),
        ],
        screenshot_slug="backend_rest_live",
    )

    add_function_block(
        story,
        title="6.8 Ouverture et validation du endpoint WebSocket",
        relative_path="backend/main.py",
        line_span="970-1008",
        summary="Cette premiere capture du endpoint WebSocket couvre uniquement l'entree dans la room, les verifications et l'envoi de socket_ready.",
        notes=[
            ("970-979", "La fonction recoit websocket, event_id et token. Elle ouvre une session DB dediee a la duree de vie de la socket."),
            ("980-994", "Le serveur refuse toute connexion sans token, sans room existante ou sans droit d'acces. Les codes 4401, 4404 et 4403 explicitent la raison."),
            ("996-1008", "Apres accept(), le serveur enregistre la connexion dans live_room_manager, envoie socket_ready avec clientId, viewerCount, status et isEditor, puis broadcast le nouveau viewer_count."),
        ],
        screenshot_slug="backend_websocket_guard",
    )

    add_function_block(
        story,
        title="6.9 WebSocket: chat, updates et annonces d'etat",
        relative_path="backend/main.py",
        line_span="1010-1085",
        summary="Cette capture couvre les branches qui persistent ou diffusent les messages de room avant la partie purement WebRTC.",
        notes=[
            ("1010-1013", "La boucle attend un payload JSON et lit message_type pour savoir quelle branche executer."),
            ("1014-1037", "Branche chat_message: le message est nettoye, persiste en base comme type='chat', puis rebroadcast a toute la room."),
            ("1039-1063", "Branche live_update: reservee a l'editeur proprietaire, persiste le message comme type='update', puis diffuse l'update officielle."),
            ("1065-1075", "Branche broadcaster_ready: reservee a l'editeur. Le serveur diffuse l'information a tous les autres clients de la room, sans se la renvoyer."),
            ("1077-1085", "Branche stream_ended: reservee a l'editeur. Le serveur diffuse la fin du flux camera."),
        ],
        screenshot_slug="backend_websocket_messages",
    )

    add_function_block(
        story,
        title="6.10 WebSocket: signalisation WebRTC et nettoyage final",
        relative_path="backend/main.py",
        line_span="1087-1114",
        summary="Cette derniere capture montre le relai des messages WebRTC et le nettoyage de la connexion quand un client se deconnecte.",
        notes=[
            ("1087-1098", "Le serveur prepare un payload sortant commun pour viewer_joined, offer, answer et ice_candidate, puis ajoute sdp ou candidate selon le cas."),
            ("1099-1107", "Si targetClientId est present, le message est route vers un pair precis. Sinon, il est diffuse aux autres clients de la room."),
            ("1108-1114", "Au disconnect, la socket est retiree du manager, le viewer_count est rediffuse, puis la session DB est fermee."),
        ],
        screenshot_slug="backend_websocket_signaling",
    )

    story.append(PageBreak())
    story.append(p("7. Resume final du fonctionnement du live", "SectionTitle"))
    story.append(
        p(
            "Le module live de NewsHub suit une logique tres nette. Le hub /live sert a creer ou choisir une room. "
            "Quand la room /live/:id s'ouvre, Angular charge son etat initial via REST. Si l'utilisateur a le droit "
            "d'entrer, une WebSocket privee est ensuite ouverte avec un JWT. La WebSocket apporte l'etat courant de la "
            "room, le chat, les updates, le compteur de lecteurs connectes et la signalisation."
        )
    )
    story.append(
        p(
            "Le media n'est pas transporte par la WebSocket. Quand l'editeur clique sur Go live with camera, le front "
            "marque la diffusion comme active et envoie broadcaster_ready. Les lecteurs envoient alors viewer_joined, "
            "puis l'offre, la reponse et les candidats ICE circulent via la socket. Enfin, l'evenement ontrack du lecteur "
            "raccorde le vrai flux distant a la balise video. C'est exactement la que le lecteur rejoint le direct video."
        )
    )
    story.append(
        p(
            "En bref: REST installe la scene, WebSocket dirige la session, WebRTC transporte l'image et le son. "
            "L'implementation est lisible, pedagogique et bien separee entre controle metier et flux media."
        )
    )

    return story


def draw_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 8)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(doc.leftMargin, 0.65 * cm, "NewsHub - Documentation technique du module live")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.65 * cm, f"Page {doc.page}")
    canvas.restoreState()


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    for spec in SCREENSHOTS:
        render_code_screenshot(spec)

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=1.45 * cm,
        rightMargin=1.45 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.2 * cm,
        title="Documentation technique du module live NewsHub",
        author="OpenAI Codex",
    )
    story = build_story()
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"PDF generated: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
