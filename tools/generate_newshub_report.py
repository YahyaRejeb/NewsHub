from __future__ import annotations

from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Circle, Drawing, Line, Polygon, Rect, String


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "reports"
PDF_PATH = OUTPUT_DIR / "newshub_rapport_global.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=6,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.2,
            leading=15,
            textColor=colors.HexColor("#111827"),
            alignment=TA_JUSTIFY,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletLine",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#111827"),
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#475569"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            leftIndent=8,
            rightIndent=8,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.4,
            leading=10,
            textColor=colors.white,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.1,
            leading=9.8,
            textColor=colors.HexColor("#111827"),
            alignment=TA_LEFT,
        )
    )
    return styles


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(doc.leftMargin, 0.75 * cm, "NewsHub - Rapport global du projet")
    page_number = f"Page {doc.page}"
    width = stringWidth(page_number, "Helvetica", 8.5)
    canvas.drawString(PAGE_WIDTH - doc.rightMargin - width, 0.75 * cm, page_number)
    canvas.restoreState()


def paragraph(text: str, style_name: str, styles):
    return Paragraph(text, styles[style_name])


def bullets(items: list[str], styles):
    return [paragraph(f"• {item}", "BulletLine", styles) for item in items]


def info_box(title: str, lines: list[str], styles, background="#eff6ff"):
    rows = [[paragraph(f"<b>{title}</b>", "Body", styles)]]
    rows.extend([[paragraph(line, "Callout", styles)] for line in lines])
    table = Table(rows, colWidths=[16.2 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#bfdbfe")),
                ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def summary_table(styles):
    data = [
        [table_header("Indicateur", styles), table_header("Valeur observee dans le projet", styles)],
        [table_cell("Frontend", styles), table_cell("Angular standalone components + Router + RxJS + Bootstrap d'appui", styles)],
        [table_cell("Backend", styles), table_cell("FastAPI + SQLAlchemy + JWT + WebSocket", styles)],
        [table_cell("Base de donnees", styles), table_cell("MySQL avec creation automatique et seed des centres d'interet", styles)],
        [table_cell("Fonctions metier", styles), table_cell("authentification, fil d'actualites, favoris, commentaires, premium, IA, live", styles)],
        [table_cell("Temps reel", styles), table_cell("WebSocket + WebRTC pour les rooms live", styles)],
        [table_cell("IA locale", styles), table_cell("Ollama + modele prefere qwen3:14b (implementation actuelle)", styles)],
    ]
    table = Table(data, colWidths=[5.1 * cm, 11.1 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def structure_table(styles):
    data = [
        [table_header("Dossier", styles), table_header("Role principal", styles)],
        [table_cell("frontend/src/app/features", styles), table_cell("Pages metier: home, details, profile, premium, live hub, live room", styles)],
        [table_cell("frontend/src/app/shared/components", styles), table_cell("Composants reutilisables: header, footer, auth-card, cards, filtres", styles)],
        [table_cell("frontend/src/app/core/services", styles), table_cell("Services Angular pour news, auth, profil, favoris, commentaires, chatbot, live", styles)],
        [table_cell("backend/main.py", styles), table_cell("API principale FastAPI, endpoints HTTP et WebSocket", styles)],
        [table_cell("backend/models.py", styles), table_cell("Modele relationnel SQLAlchemy", styles)],
        [table_cell("backend/database.py", styles), table_cell("Connexion MySQL, creation automatique, extensions de schema, seed des interets", styles)],
        [table_cell("backend/security.py", styles), table_cell("Hash des mots de passe et creation/verification des JWT", styles)],
        [table_cell("backend/simple_chatbot.py", styles), table_cell("Assistant IA local base sur Ollama", styles)],
    ]
    table = Table(data, colWidths=[5.1 * cm, 11.1 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#eff6ff"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#bfdbfe")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.2),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def api_table(styles):
    data = [
        [table_header("Groupe", styles), table_header("Endpoints cles", styles), table_header("Utilite", styles)],
        [table_cell("Auth", styles), table_cell("GET /check-email, POST /complete-signup, POST /login, GET /users/me", styles), table_cell("Creation de session, verification email, identification de l'utilisateur", styles)],
        [table_cell("Profil", styles), table_cell("GET /users/{id}, PUT /users/{id}/profile, PUT/DELETE /users/{id}/profile/photo", styles), table_cell("Consultation et mise a jour du profil", styles)],
        [table_cell("News", styles), table_cell("GET /news-feed", styles), table_cell("Intermediation vers NewsData avec filtres et normalisation", styles)],
        [table_cell("Interets", styles), table_cell("GET /interests", styles), table_cell("Chargement des centres d'interet pour l'inscription", styles)],
        [table_cell("Favoris", styles), table_cell("POST /favorites, DELETE /favorites, GET /favorites-status, GET /favorites/{id}", styles), table_cell("Sauvegarde et recuperation des articles favoris", styles)],
        [table_cell("Commentaires", styles), table_cell("GET /comments, POST /comments", styles), table_cell("Discussion autour d'un article", styles)],
        [table_cell("Premium", styles), table_cell("POST /premium/activate", styles), table_cell("Activation premium simulee cote backend", styles)],
        [table_cell("IA", styles), table_cell("GET /chatbot/status, POST /chatbot/article-brief, POST /chatbot/ask", styles), table_cell("Etat Ollama, resume article, conversation IA", styles)],
        [table_cell("Live", styles), table_cell("GET/POST /live-events, POST /live-events/{id}/start, POST /end, DELETE /live-events/{id}, WS /ws/live-events/{id}", styles), table_cell("Evenements live, chat temps reel, video et updates editeur", styles)],
    ]
    table = Table(data, colWidths=[2.4 * cm, 6.9 * cm, 6.9 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.6),
                ("LEADING", (0, 0), (-1, -1), 10.5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def db_table(styles):
    data = [
        [table_header("Table", styles), table_header("Role dans l'application", styles)],
        [table_cell("users", styles), table_cell("Compte utilisateur, role, photo, premium, historique minimal de session", styles)],
        [table_cell("interests", styles), table_cell("Liste des centres d'interet disponibles", styles)],
        [table_cell("user_interests", styles), table_cell("Association n-n entre utilisateurs et interets", styles)],
        [table_cell("source", styles), table_cell("Source de publication d'un article", styles)],
        [table_cell("news", styles), table_cell("Copie locale des articles qui deviennent favoris ou support de commentaire", styles)],
        [table_cell("favorite", styles), table_cell("Articles sauvegardes par utilisateur", styles)],
        [table_cell("comments", styles), table_cell("Commentaires postes sur un article", styles)],
        [table_cell("live_events", styles), table_cell("Salles live creees par un editeur", styles)],
        [table_cell("live_messages", styles), table_cell("Messages de chat et updates editeur pendant le live", styles)],
    ]
    table = Table(data, colWidths=[4.2 * cm, 12 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#eef2ff"), colors.white]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 9.2),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def make_breakable(text: str) -> str:
    safe = escape(text)
    for token in ["/", ".", "_", "(", ")", ",", "{", "}", ":", "-"]:
        safe = safe.replace(token, f"{token}<wbr/>")
    return safe


def table_header(text: str, styles):
    return Paragraph(escape(text), styles["TableHeader"])


def table_cell(text: str, styles):
    return Paragraph(make_breakable(text), styles["TableCell"])


def functionality_table(rows, styles):
    data = [[table_header("Fonction / methode", styles), table_header("Localisation", styles), table_header("Role dans le projet", styles)]]
    data.extend([[table_cell(a, styles), table_cell(b, styles), table_cell(c, styles)] for a, b, c in rows])
    table = Table(data, colWidths=[5.3 * cm, 5.1 * cm, 5.8 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eff6ff")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bfdbfe")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def technology_table(rows, styles):
    data = [[table_header("Technologie", styles), table_header("Principe", styles), table_header("Usage dans NewsHub", styles), table_header("Exemple concret", styles)]]
    data.extend([[table_cell(a, styles), table_cell(b, styles), table_cell(c, styles), table_cell(d, styles)] for a, b, c, d in rows])
    table = Table(data, colWidths=[2.8 * cm, 4.2 * cm, 5.2 * cm, 4.0 * cm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def add_box(d, x, y, w, h, title, subtitle="", fill="#ffffff", stroke="#334155", title_fill="#0f172a"):
    d.add(
        Rect(
            x,
            y,
            w,
            h,
            rx=8,
            ry=8,
            fillColor=colors.HexColor(fill),
            strokeColor=colors.HexColor(stroke),
            strokeWidth=1.1,
        )
    )
    d.add(
        String(
            x + 8,
            y + h - 18,
            title,
            fontName="Helvetica-Bold",
            fontSize=10,
            fillColor=colors.HexColor(title_fill),
        )
    )
    if subtitle:
        d.add(
            String(
                x + 8,
                y + h - 33,
                subtitle,
                fontName="Helvetica",
                fontSize=7.8,
                fillColor=colors.HexColor("#475569"),
            )
        )


def add_arrow(d, x1, y1, x2, y2, label="", color="#2563eb"):
    d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor(color), strokeWidth=1.3))
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx ** 2 + dy ** 2) ** 0.5, 1)
    ux = dx / length
    uy = dy / length
    size = 6
    px = -uy
    py = ux
    arrow = Polygon(
        [
            x2,
            y2,
            x2 - size * ux + (size / 2) * px,
            y2 - size * uy + (size / 2) * py,
            x2 - size * ux - (size / 2) * px,
            y2 - size * uy - (size / 2) * py,
        ],
        fillColor=colors.HexColor(color),
        strokeColor=colors.HexColor(color),
    )
    d.add(arrow)
    if label:
        d.add(
            String(
                (x1 + x2) / 2,
                (y1 + y2) / 2 + 6,
                label,
                fontName="Helvetica",
                fontSize=7.4,
                fillColor=colors.HexColor("#1e293b"),
            )
        )


def simple_flow_diagram(title, steps, caption):
    width = 520
    height = 155
    d = Drawing(width, height)
    d.add(String(12, height - 18, title, fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    start_x = 18
    y = 56
    box_w = 92
    box_h = 54
    gap = 11
    palette = ["#f8fafc", "#e0f2fe", "#dbeafe", "#dcfce7", "#fef3c7", "#fee2e2"]
    current_x = start_x
    previous_mid_x = None
    mid_y = y + box_h / 2
    for index, step in enumerate(steps):
        lines = step.split("\n", 1)
        title_line = lines[0]
        subtitle = lines[1] if len(lines) > 1 else ""
        add_box(d, current_x, y, box_w, box_h, title_line, subtitle, fill=palette[index % len(palette)], stroke="#94a3b8")
        if previous_mid_x is not None:
            add_arrow(d, previous_mid_x, mid_y, current_x, mid_y, color="#2563eb")
        previous_mid_x = current_x + box_w
        current_x += box_w + gap
    d.add(String(18, 20, caption, fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#475569")))
    return d


def architecture_diagram():
    d = Drawing(520, 260)
    add_box(d, 15, 140, 120, 72, "Visiteur / utilisateur", "navigue, filtre, se connecte", fill="#f8fafc")
    add_box(d, 165, 138, 145, 78, "Frontend Angular", "routes, composants, services, etat local", fill="#e0f2fe")
    add_box(d, 347, 138, 145, 78, "Backend FastAPI", "REST, JWT, WebSocket, logique metier", fill="#dbeafe")
    add_box(d, 347, 40, 145, 66, "MySQL", "utilisateurs, favoris, commentaires, live", fill="#ecfccb")
    add_box(d, 15, 38, 120, 66, "Ollama local", "resume article + chat via qwen3:14b", fill="#fde68a")
    add_box(d, 165, 38, 145, 66, "NewsData API", "source externe d'actualites", fill="#fee2e2")

    add_arrow(d, 135, 175, 165, 175, "UI / navigation")
    add_arrow(d, 310, 175, 347, 175, "HTTP / JSON")
    add_arrow(d, 420, 138, 420, 106, "SQLAlchemy")
    add_arrow(d, 238, 138, 238, 104, "GET /news-feed")
    add_arrow(d, 347, 72, 135, 72, "status + ask")
    add_arrow(d, 238, 104, 347, 104, "proxy / filtrage")

    d.add(String(165, 228, "Vue d'ensemble de l'architecture", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    d.add(String(167, 122, "Le front gere l'experience utilisateur et appelle le backend.", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#475569")))
    d.add(String(349, 24, "Le backend stocke les donnees locales et orchestre les services externes.", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#475569")))
    return d


def signup_diagram():
    d = Drawing(520, 250)
    d.add(String(12, 228, "Flux d'inscription reele du projet", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    add_box(d, 20, 150, 110, 54, "1. Saisie identite", "nom, email, mot de passe", fill="#f8fafc")
    add_box(d, 150, 150, 110, 54, "2. Etape interets", "selection max 3 centres", fill="#e0f2fe")
    add_box(d, 280, 150, 110, 54, "3. Verification email", "GET /check-email", fill="#dbeafe")
    add_box(d, 410, 150, 90, 54, "4. Creation compte", "POST /complete-signup", fill="#dcfce7")
    add_box(d, 410, 60, 90, 54, "5. Auto-login", "JWT + currentUser", fill="#fef3c7")
    add_box(d, 280, 60, 110, 54, "Si compte existe", "message d'erreur + retour etape 1", fill="#fee2e2")

    add_arrow(d, 130, 176, 150, 176, "Continue")
    add_arrow(d, 260, 176, 280, 176, "Complete")
    add_arrow(d, 390, 176, 410, 176, "email libre")
    add_arrow(d, 455, 150, 455, 114, "succes")
    add_arrow(d, 410, 87, 390, 87, "sinon")
    add_arrow(d, 280, 87, 130, 150, "afficher erreur", color="#dc2626")
    return d


def article_flow_diagram():
    d = Drawing(520, 260)
    d.add(String(12, 236, "Cycle d'interaction autour d'un article", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    add_box(d, 18, 150, 120, 64, "Home / News card", "clic sur une actualite", fill="#f8fafc")
    add_box(d, 165, 150, 120, 64, "Page details", "image, meta, source, actions", fill="#e0f2fe")
    add_box(d, 315, 170, 165, 44, "Favoris", "save / unsave avec verification login", fill="#dcfce7")
    add_box(d, 315, 112, 165, 44, "Commentaires", "lecture + ajout via API", fill="#dbeafe")
    add_box(d, 315, 54, 165, 44, "Premium AI", "gate guest / free / premium", fill="#fde68a")
    add_box(d, 165, 48, 120, 50, "Backend services", "comments, favorites, chatbot", fill="#eff6ff")

    add_arrow(d, 138, 182, 165, 182, "route /details/:id")
    add_arrow(d, 285, 195, 315, 195, "save")
    add_arrow(d, 285, 135, 315, 135, "comment")
    add_arrow(d, 285, 79, 315, 79, "assistant")
    add_arrow(d, 255, 98, 315, 98, "API")
    d.add(String(24, 28, "Un meme article devient le point d'entree vers la consultation, la sauvegarde, la discussion et l'assistance IA.", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#475569")))
    return d


def live_diagram():
    d = Drawing(520, 270)
    d.add(String(12, 244, "Architecture du module live temps reel", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    add_box(d, 25, 162, 120, 60, "Editeur", "cree la room, demarre le live, publie updates", fill="#fee2e2")
    add_box(d, 200, 162, 120, 60, "Backend WebSocket", "presence, viewerCount, messages", fill="#dbeafe")
    add_box(d, 375, 162, 120, 60, "Viewer premium", "regarde le live et discute", fill="#dcfce7")
    add_box(d, 25, 62, 120, 58, "Camera locale", "MediaStream navigateur", fill="#fef3c7")
    add_box(d, 375, 62, 120, 58, "Remote video", "MediaStream recu", fill="#fefce8")
    add_box(d, 200, 62, 120, 58, "Signaling WebRTC", "offer, answer, ice_candidate", fill="#e0f2fe")

    add_arrow(d, 145, 190, 200, 190, "auth + WS")
    add_arrow(d, 320, 190, 375, 190, "events")
    add_arrow(d, 85, 120, 85, 162, "prepareCamera")
    add_arrow(d, 435, 162, 435, 120, "stream")
    add_arrow(d, 145, 92, 200, 92, "offer / answer")
    add_arrow(d, 320, 92, 375, 92, "ICE + SDP")
    add_arrow(d, 260, 120, 260, 162, "messages live")
    d.add(String(18, 26, "Le backend ne transporte pas la video elle-meme: il orchestre le signaling et l'etat de la room.", fontName="Helvetica", fontSize=8, fillColor=colors.HexColor("#475569")))
    return d


def build_story(styles):
    story = []
    story.append(Spacer(1, 1.2 * cm))
    story.append(paragraph("Rapport global d'analyse fonctionnelle et technique", "CoverTitle", styles))
    story.append(paragraph("Projet NewsHub", "CoverTitle", styles))
    story.append(
        paragraph(
            "Document de comprehension complet du projet, de son architecture et de ses scenarios d'usage. "
            "L'objectif est qu'une personne qui lit ce rapport comprenne comment l'application fonctionne, "
            "comment les composants interagissent et comment chaque fonctionnalite principale est executee.",
            "CoverSubtitle",
            styles,
        )
    )
    story.append(
        info_box(
            "Fiche d'identite du projet",
            [
                f"Date du rapport : {date.today().isoformat()}",
                "Nom du produit : NewsHub",
                "Nature : plateforme web d'actualites avec experience personnalisee, premium et live",
                "Public cible : visiteurs, utilisateurs connectes, membres premium, editeurs live",
            ],
            styles,
            background="#f8fafc",
        )
    )
    story.append(Spacer(1, 0.35 * cm))
    story.append(summary_table(styles))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        paragraph(
            "Resume executif : NewsHub est une application SPA Angular connectee a un backend FastAPI. "
            "Elle agrege des actualites externes, personnalise le fil selon les interets choisis lors de l'inscription, "
            "permet de sauvegarder des articles, publier des commentaires, activer un statut premium et acceder a un "
            "assistant IA local. Le projet contient aussi un module live en temps reel avec WebSocket et WebRTC.",
            "Body",
            styles,
        )
    )
    story.append(PageBreak())

    story.append(paragraph("Sommaire", "SectionTitle", styles))
    for item in [
        "1. Vision generale et objectifs du projet",
        "2. Architecture globale et structure du code",
        "3. Fonctionnalites principales et interactions utilisateur",
        "4. Scenarios metier et diagrammes de fonctionnement",
        "5. Donnees, API, securite et stockage",
        "6. Technologies utilisees et bilan du projet",
    ]:
        story.append(paragraph(item, "Body", styles))
    story.append(Spacer(1, 0.25 * cm))
    story.append(info_box("Lecture conseillee", [
        "Commencer par l'architecture pour comprendre les blocs.",
        "Ensuite lire les scenarios utilisateurs pour voir la logique metier.",
        "Enfin consulter les sections API/base de donnees pour la comprehension technique detaillee.",
    ], styles))
    story.append(PageBreak())

    story.append(paragraph("1. Vision generale et objectifs du projet", "SectionTitle", styles))
    story.append(
        paragraph(
            "NewsHub cherche a offrir une experience moderne de consultation d'actualites. "
            "Le systeme ne se limite pas a afficher des news : il personnalise l'accueil, gere les comptes, "
            "memorise des actions utilisateur et ajoute des fonctions avancees comme le premium, le chatbot local et les salles live.",
            "Body",
            styles,
        )
    )
    story.extend(
        bullets(
            [
                "Afficher des actualites par categorie a partir d'une source externe.",
                "Filtrer rapidement les articles grace a un cache local cote frontend.",
                "Permettre une inscription en deux etapes avec choix d'interets.",
                "Faire evoluer l'experience selon l'etat utilisateur : visiteur, connecte, premium, editeur.",
                "Centraliser l'activite de l'utilisateur : profil, favoris, commentaires, premium.",
                "Ajouter un module live avec communication temps reel et streaming navigateur a navigateur.",
            ],
            styles,
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(info_box("Conclusion de la vision", [
        "Le projet combine une logique de media, de compte utilisateur, de personnalisation, de paiement simule, d'IA locale et de live streaming.",
        "Cela en fait un projet riche, utile pour montrer une maitrise full-stack au-dela d'un simple site vitrine.",
    ], styles, background="#ecfeff"))

    story.append(Spacer(1, 0.35 * cm))
    story.append(paragraph("2. Architecture globale et structure du code", "SectionTitle", styles))
    story.append(paragraph("L'architecture est decoupee en deux grands sous-systemes : le frontend Angular et le backend FastAPI.", "Body", styles))
    story.append(architecture_diagram())
    story.append(paragraph("Figure 1 - Architecture globale de NewsHub.", "Caption", styles))
    story.append(paragraph("Le frontend pilote l'interface, les routes et les services HTTP. Le backend centralise la logique metier, la securite JWT, l'acces MySQL, les routes live et l'assistant Ollama.", "Body", styles))
    story.append(structure_table(styles))
    story.append(PageBreak())

    story.append(paragraph("3. Fonctionnalites principales et interactions utilisateur", "SectionTitle", styles))
    story.append(paragraph("Les principales fonctionnalites peuvent etre regroupees en huit modules.", "Body", styles))
    modules = [
        ("A. Fil d'actualites et filtres", "Le service news precharge plusieurs categories, dedoublonne les articles, trie par date et persiste le cache dans localStorage. Le Home recompose ensuite l'affichage selon les filtres et les interets preferes."),
        ("B. Authentification et inscription", "L'utilisateur peut s'inscrire en deux etapes : informations d'identite puis choix des interets. La verification d'email est declenchee juste avant la creation finale du compte, puis le backend cree l'utilisateur, lie ses interets et renvoie un token JWT."),
        ("C. Profil utilisateur", "La page profil recharge l'utilisateur depuis l'API, permet la mise a jour du nom, de l'email, du mot de passe et de la photo de profil. Les validations sont faites cote frontend puis confirmees cote backend."),
        ("D. Favoris", "Depuis la page detail, un utilisateur connecte peut sauvegarder un article. Si l'article n'a pas d'URL source valide, l'action est refusee. Les favoris sont ensuite visibles dans le dashboard profil."),
        ("E. Commentaires", "Chaque article peut porter une discussion. Les visiteurs sont rediriges vers le login, tandis que les membres connectes postent via /comments."),
        ("F. Premium", "La page premium simule un paiement. Une fois valide, le backend active is_premium et stocke le plan choisi. Le front rafraichit ensuite la session utilisateur."),
        ("G. Assistant IA", "Le panneau IA d'article interroge le backend pour obtenir l'etat Ollama, un brief article et des reponses conversationnelles. L'implementation actuelle utilise qwen3:14b et non gemma3:12b."),
        ("H. Live Hub", "Un editeur cree une room live, la demarre, diffuse sa camera et publie des updates. Les viewers premium rejoignent via WebSocket et WebRTC, peuvent chatter et recoivent les changements d'etat en temps reel."),
    ]
    for title, content in modules:
        story.append(paragraph(title, "SubTitle", styles))
        story.append(paragraph(content, "Body", styles))

    story.append(Spacer(1, 0.2 * cm))
    story.append(paragraph("Parcours utilisateur principaux", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "Visiteur : consulte l'accueil, filtre des actualites, ouvre les details, puis est redirige vers le login s'il veut sauvegarder, commenter ou utiliser le premium.",
                "Utilisateur standard : se connecte, retrouve ses interets, sauvegarde des articles, commente et peut activer le premium.",
                "Utilisateur premium : accede en plus a l'assistant IA sur les articles et aux salles live premium.",
                "Editeur : cree et administre des rooms live, controle le demarrage, l'arret et la diffusion camera.",
            ],
            styles,
        )
    )
    story.append(PageBreak())

    story.append(paragraph("4. Fiches fonctionnelles detaillees", "SectionTitle", styles))
    story.append(paragraph("Cette section descend au niveau des fonctions exactes du projet. Pour chaque fonctionnalite, le rapport indique les methodes mobilisees, leur localisation, la logique metier et l'efficacite de la solution dans NewsHub.", "Body", styles))

    story.append(paragraph("4.1 Connexion utilisateur", "SubTitle", styles))
    story.append(functionality_table([
        ["LoginForm.onSubmit()", "frontend/src/app/shared/components/login-form/login-form.ts", "Envoie les identifiants au backend et remonte le succes ou l'erreur au composant parent."],
        ["AuthCard.onLoginSuccess()", "frontend/src/app/shared/components/auth-card/auth-card.ts", "Stocke la session via AuthService puis redirige vers returnUrl."],
        ["AuthService.setAuthData()", "frontend/src/app/core/services/auth/auth.ts", "Met a jour localStorage et l'observable currentUser$."],
        ["login()", "backend/main.py", "Verifie l'email, le mot de passe hash et renvoie un JWT + l'utilisateur serialize."],
        ["create_access_token()", "backend/security.py", "Fabrique le token JWT utilise par le frontend."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(simple_flow_diagram(
        "Diagramme de la fonctionnalite Login",
        ["Utilisateur\nsaisit email + mot de passe", "LoginForm.onSubmit\nPOST /login", "backend.login\nverifie credentials", "AuthCard.onLoginSuccess\nsetAuthData", "Retour utilisateur\nredirection"],
        "Cette chaine rend la connexion rapide et centralise l'etat de session dans AuthService."
    ))
    story.append(paragraph("Explication : la connexion est volontairement courte. Le composant LoginForm ne garde pas la logique metier ; il delegue au backend la verification reelle des credentials. L'efficacite de cette conception vient du fait que la validation sensible ne quitte jamais le serveur, tandis que le frontend ne gere que l'affichage et la redirection.", "Body", styles))

    story.append(paragraph("4.2 Inscription et choix des interets", "SubTitle", styles))
    story.append(functionality_table([
        ["RegisterForm.onSubmit()", "frontend/src/app/shared/components/register-form/register-form.ts", "Valide les champs locaux et emet les donnees de base vers AuthCard."],
        ["AuthCard.goToNextStep()", "frontend/src/app/shared/components/auth-card/auth-card.ts", "Conserve les informations d'identite et passe a l'etape interets."],
        ["InterestsForm.submit()", "frontend/src/app/shared/components/interests-form/interests-form.ts", "Envoie la liste finale des interets selectionnes."],
        ["AuthCard.finishSignup()", "frontend/src/app/shared/components/auth-card/auth-card.ts", "Verifie d'abord l'email puis poste l'inscription finale."],
        ["check_email()", "backend/main.py", "Teste l'existence d'un compte sur l'email fourni."],
        ["complete_signup()", "backend/main.py", "Cree l'utilisateur, lie les interets et retourne la session authentifiee."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(signup_diagram())
    story.append(paragraph("Explication : ce flux en deux etapes ameliore l'onboarding, car il separe la creation d'identite de la personnalisation. Son efficacite tient au fait que le frontend collecte progressivement les informations, tandis que le backend conserve le dernier mot sur l'unicite de l'email et la creation effective du compte.", "Body", styles))

    story.append(paragraph("4.3 Sauvegarde des favoris", "SubTitle", styles))
    story.append(functionality_table([
        ["NewsDetailsPageComponent.toggleSaveArticle()", "frontend/src/app/features/news/news-details-page/news-details-page.ts", "Point d'entree UI pour sauvegarder ou retirer un favori."],
        ["FavoritesService.saveArticle()", "frontend/src/app/core/services/favorites.ts", "Mappe l'article frontend vers le payload backend puis appelle POST /favorites."],
        ["FavoritesService.removeArticle()", "frontend/src/app/core/services/favorites.ts", "Supprime un favori via DELETE /favorites."],
        ["FavoritesService.isArticleSaved()", "frontend/src/app/core/services/favorites.ts", "Charge l'etat saved/non saved pour l'article courant."],
        ["save_favorite()", "backend/main.py", "Cree ou remet a jour l'association favorite entre l'utilisateur et la news."],
        ["remove_favorite()", "backend/main.py", "Supprime la liaison entre l'utilisateur et la news."],
        ["crud.upsert_news_record()", "backend/crud.py", "Assure qu'un article existe en base avant d'etre reference comme favori."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(simple_flow_diagram(
        "Diagramme de la fonctionnalite Save Favorite",
        ["Details article\nclic Save", "toggleSaveArticle\nverifie login + URL", "FavoritesService\nPOST / DELETE", "backend.save_favorite\nupsert news", "Profil\narticle visible en favoris"],
        "Le design evite les doublons et garantit qu'un favori pointe toujours vers un article persiste."
    ))
    story.append(paragraph("Explication : l'efficacite vient d'une conception robuste. Avant de stocker un favori, le backend normalise l'article et le persiste si necessaire. Ainsi, le projet evite de multiplier des copies incoherentes et peut reutiliser la meme news pour les commentaires et l'historique utilisateur.", "Body", styles))

    story.append(paragraph("4.4 Commentaires sur les articles", "SubTitle", styles))
    story.append(functionality_table([
        ["NewsDetailsPageComponent.submitComment()", "frontend/src/app/features/news/news-details-page/news-details-page.ts", "Valide le texte, verifie la session puis envoie le commentaire."],
        ["CommentsService.addComment()", "frontend/src/app/core/services/comments.ts", "Poste le commentaire et l'article associe."],
        ["CommentsService.getComments()", "frontend/src/app/core/services/comments.ts", "Recharge tous les commentaires d'une URL d'article."],
        ["add_comment()", "backend/main.py", "Nettoie le texte, rattache la news et insere le commentaire."],
        ["get_comments()", "backend/main.py", "Retourne la liste ordonnee des commentaires d'un article."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(simple_flow_diagram(
        "Diagramme de la fonctionnalite Commentaire",
        ["Utilisateur connecte\necrit un texte", "submitComment\nvalidation locale", "CommentsService\nPOST /comments", "backend.add_comment\ninsert DB", "refresh comments\nGET /comments"],
        "Le refresh immediat donne un retour utilisateur clair et maintient la page coherente."
    ))
    story.append(paragraph("Explication : le commentaire reutilise la meme structure d'article que les favoris. Cela augmente l'efficacite du projet, car un article deja persiste peut etre partage entre plusieurs tables metier sans duplication conceptuelle du schema.", "Body", styles))

    story.append(paragraph("4.5 Gestion du profil", "SubTitle", styles))
    story.append(functionality_table([
        ["ProfilePageComponent.loadProfile()", "frontend/src/app/features/profile/profile-page/profile-page.ts", "Recharge le profil depuis l'API pour ne pas dependre uniquement de localStorage."],
        ["ProfilePageComponent.saveProfile()", "frontend/src/app/features/profile/profile-page/profile-page.ts", "Construit full_name, email et eventuellement le changement de mot de passe."],
        ["ProfilePageComponent.saveProfilePhoto()", "frontend/src/app/features/profile/profile-page/profile-page.ts", "Envoie la photo encodee et optimisee."],
        ["ProfileService.updateProfileDetails()", "frontend/src/app/core/services/profile.ts", "PUT du profil texte."],
        ["ProfileService.updateProfilePhoto()", "frontend/src/app/core/services/profile.ts", "PUT de la photo."],
        ["update_user_profile()", "backend/main.py", "Verifie l'unicite de l'email et les regles de changement de mot de passe."],
        ["update_user_profile_photo()", "backend/main.py", "Normalise et stocke la photo."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(simple_flow_diagram(
        "Diagramme de la fonctionnalite Profil",
        ["Ouverture /profile\ncharge session", "loadProfile\nGET /users/{id}", "Edition form\nsaveProfile", "backend.update_user_profile\ncommit", "AuthService\nsession rafraichie"],
        "Le profil reste synchronise entre le backend et la session frontend."
    ))
    story.append(paragraph("Explication : la page profil n'est pas seulement un formulaire. Elle recalcule la completion, recharge la session et separe clairement la photo des details textuels. Cette separation ameliore l'efficacite des interactions et simplifie les validations.", "Body", styles))

    story.append(PageBreak())
    story.append(paragraph("4.6 Premium et paiement simule", "SubTitle", styles))
    story.append(functionality_table([
        ["PremiumPageComponent.simulateCheckout()", "frontend/src/app/features/premium/premium-page/premium-page.ts", "Valide les champs puis appelle le service premium."],
        ["PremiumService.activatePremium()", "frontend/src/app/core/services/premium.ts", "POST /premium/activate."],
        ["PremiumService.decorateUser()", "frontend/src/app/core/services/premium.ts", "Normalise les champs premium dans la session frontend."],
        ["activate_premium_membership()", "backend/main.py", "Active is_premium, premium_plan et premium_since."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(simple_flow_diagram(
        "Diagramme de la fonctionnalite Premium",
        ["Choix du plan\nmonthly / annual", "simulateCheckout\nvalidation form", "PremiumService\nPOST /premium/activate", "backend.activate_premium\nmaj user", "AuthService\nsession premium"],
        "Le projet simule un paiement sans passer par une vraie passerelle, ce qui est ideal pour la demonstration."
    ))
    story.append(paragraph("Explication : cette fonctionnalite est efficace pedagogiquement. Elle montre un vrai flux d'abonnement sans dependance a Stripe ou a une banque, ce qui permet de concentrer l'analyse sur la logique metier et les changements d'etat utilisateur.", "Body", styles))

    story.append(paragraph("4.7 Assistant IA premium", "SubTitle", styles))
    story.append(functionality_table([
        ["ArticleAssistantPanelComponent.loadStatus()", "frontend/src/app/features/news/article-assistant-panel/article-assistant-panel.ts", "Charge l'etat d'Ollama et du modele."],
        ["ArticleAssistantPanelComponent.loadBrief()", "frontend/src/app/features/news/article-assistant-panel/article-assistant-panel.ts", "Demande un resume structurant de l'article."],
        ["ArticleAssistantPanelComponent.send()", "frontend/src/app/features/news/article-assistant-panel/article-assistant-panel.ts", "Construit l'historique recent et envoie le prompt."],
        ["ChatbotService.getStatus()", "frontend/src/app/core/services/chatbot.ts", "GET /chatbot/status."],
        ["ChatbotService.getArticleBrief()", "frontend/src/app/core/services/chatbot.ts", "POST /chatbot/article-brief."],
        ["ChatbotService.askChatbot()", "frontend/src/app/core/services/chatbot.ts", "POST /chatbot/ask."],
        ["get_chatbot_status()", "backend/simple_chatbot.py", "Teste Ollama et la disponibilite de qwen3:14b."],
        ["get_article_brief()", "backend/simple_chatbot.py", "Produit un resume simple a partir du texte de l'article."],
        ["ask_chatbot()", "backend/simple_chatbot.py", "Construit le prompt article-aware et appelle /api/chat d'Ollama."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(simple_flow_diagram(
        "Diagramme de la fonctionnalite Assistant IA",
        ["Article ouvert\nuser premium", "loadStatus + loadBrief\npreparation UI", "send()\nquestion utilisateur", "backend.ask_chatbot\nappel Ollama", "Reponse\naffichee dans la conversation"],
        "La limite d'historique garde le chat reactif et reduit la charge d'appel du modele."
    ))
    story.append(paragraph("Explication : l'assistant est efficace parce qu'il reste simple. Il n'utilise pas une stack RAG lourde ; il injecte plutot le texte de l'article dans un prompt systeme puis ajoute les derniers tours de conversation. Cela convient bien a une application locale ou a un projet de demonstration.", "Body", styles))

    story.append(paragraph("4.8 Module live temps reel", "SubTitle", styles))
    story.append(functionality_table([
        ["LiveHubPageComponent.createLiveRoom()", "frontend/src/app/features/live/live-hub-page/live-hub-page.ts", "Cree une salle live reservee a l'editeur."],
        ["LiveRoomPageComponent.startLiveRoom()", "frontend/src/app/features/live/live-room-page/live-room-page.ts", "Passe l'evenement au statut live."],
        ["LiveRoomPageComponent.goLiveWithCamera()", "frontend/src/app/features/live/live-room-page/live-room-page.ts", "Prepare la camera et annonce broadcaster_ready."],
        ["LiveRoomPageComponent.publishEditorUpdate()", "frontend/src/app/features/live/live-room-page/live-room-page.ts", "Diffuse un update texte a tous les viewers."],
        ["LiveRoomPageComponent.sendChatMessage()", "frontend/src/app/features/live/live-room-page/live-room-page.ts", "Diffuse un message de chat."],
        ["LiveRoomSocketService.connect()", "frontend/src/app/core/services/live-room-socket.ts", "Ouvre la connexion WebSocket de signaling."],
        ["create_live_event(), start_live_event(), end_live_event()", "backend/main.py", "Pilotent le cycle de vie metier d'une room."],
        ["live_event_socket()", "backend/main.py", "Traite les evenements chat, signaling WebRTC, viewer_count et updates live."],
        ["LiveRoomManager.connect()/broadcast()", "backend/main.py", "Maintient les connexions WebSocket par room."],
    ], styles))
    story.append(Spacer(1, 0.15 * cm))
    story.append(live_diagram())
    story.append(paragraph("Explication : c'est l'une des parties les plus ambitieuses du projet. L'efficacite repose sur un bon partage des roles : REST pour l'etat metier, WebSocket pour les evenements temps reel, WebRTC pour la video. Ce decoupage est exactement ce qu'on attend d'une architecture live moderne.", "Body", styles))
    story.append(PageBreak())

    story.append(paragraph("5. Scenarios metier et diagrammes de fonctionnement", "SectionTitle", styles))
    story.append(paragraph("Cette section traduit le comportement du projet en scenarios lisibles.", "Body", styles))
    story.append(paragraph("Scenario 1 - Inscription complete", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "L'utilisateur ouvre /register et remplit nom, email, mot de passe et confirmation.",
                "Le composant RegisterForm valide la coherence locale des champs.",
                "Le composant AuthCard passe ensuite a l'ecran de selection des interets.",
                "Apres selection, AuthCard appelle GET /check-email puis POST /complete-signup si l'adresse est libre.",
                "Le backend cree le compte, rattache les interets et renvoie un JWT ; le frontend connecte automatiquement l'utilisateur.",
            ],
            styles,
        )
    )
    story.append(signup_diagram())
    story.append(paragraph("Figure 2 - Scenario d'inscription conforme a l'implementation actuelle.", "Caption", styles))

    story.append(paragraph("Scenario 2 - Consultation et exploitation d'un article", "SubTitle", styles))
    story.append(article_flow_diagram())
    story.append(paragraph("Figure 3 - Cycle d'interaction autour d'un article.", "Caption", styles))
    story.extend(
        bullets(
            [
                "Depuis le Home, l'utilisateur clique sur une carte d'actualite.",
                "La page details recharge l'article via l'etat de navigation ou via le store de news.",
                "A partir de cette page, il peut enregistrer l'article, commenter, consulter la source ou ouvrir l'IA premium.",
                "Le niveau d'acces depend de la session : visiteur, standard ou premium.",
            ],
            styles,
        )
    )

    story.append(paragraph("Scenario 3 - Experience premium et IA", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "L'utilisateur active le premium depuis la page /premium avec un paiement simule.",
                "Le backend met a jour les champs premium de l'utilisateur.",
                "Sur la page d'un article, le panneau assistant appelle /chatbot/status, /chatbot/article-brief puis /chatbot/ask.",
                "Le backend interroge Ollama et construit une reponse en injectant le texte de l'article dans le prompt systeme.",
            ],
            styles,
        )
    )
    story.append(info_box("Point d'analyse important", [
        "Le brief fonctionnel mentionne gemma3:12b, mais le code reel du backend utilise qwen3:14b dans simple_chatbot.py.",
        "Le rapport doit donc retenir qwen3:14b comme implementation effective actuelle.",
    ], styles, background="#fff7ed"))

    story.append(paragraph("Scenario 4 - Module live temps reel", "SubTitle", styles))
    story.append(live_diagram())
    story.append(paragraph("Figure 4 - Flux temps reel du module live.", "Caption", styles))
    story.extend(
        bullets(
            [
                "L'editeur cree un event live depuis /live, puis ouvre la room /live/:id.",
                "La room utilise des endpoints REST pour l'etat metier et un WebSocket pour la presence, le chat et le signaling.",
                "La video n'est pas transmise par le backend : elle passe directement entre navigateurs via WebRTC.",
                "Le backend conserve toutefois les messages live et les updates editeur en base.",
            ],
            styles,
        )
    )
    story.append(PageBreak())

    story.append(paragraph("6. Donnees, API, securite et stockage", "SectionTitle", styles))
    story.append(paragraph("Le systeme s'appuie sur une base MySQL, une securite JWT, du stockage local navigateur et des routes REST/WebSocket.", "Body", styles))
    story.append(paragraph("6.1 Modele de donnees", "SubTitle", styles))
    story.append(db_table(styles))
    story.append(Spacer(1, 0.2 * cm))
    story.append(paragraph("Le backend cree automatiquement la base si elle n'existe pas et ajoute aussi les colonnes profile_photo, role, premium et premium_since lorsqu'elles manquent. Il seed egalement les interets par defaut.", "Body", styles))

    story.append(paragraph("6.2 API et contrats d'echange", "SubTitle", styles))
    story.append(api_table(styles))
    story.append(Spacer(1, 0.2 * cm))
    story.append(paragraph("6.3 Securite et session", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "Le mot de passe est hashe avec bcrypt si disponible, sinon PBKDF2 SHA-256.",
                "Le backend cree un JWT avec une date d'expiration et le frontend le relit depuis localStorage.",
                "AuthService supprime automatiquement une session invalide ou expiree.",
                "Les endpoints sensibles verifient l'utilisateur courant et interdisent l'acces a un autre compte.",
                "Le role editor est exige pour creer, lancer, terminer ou supprimer une room live.",
            ],
            styles,
        )
    )

    story.append(paragraph("6.4 Stockage local navigateur", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "currentUser : session utilisateur courante decoree par PremiumService.",
                "access_token : JWT utilise par les appels proteges.",
                "newshub-news-store-v1 : cache des categories d'actualites prechargees.",
                "Le front reutilise ce stockage pour rendre l'experience plus rapide et resiliente si l'API news echoue temporairement.",
            ],
            styles,
        )
    )

    story.append(PageBreak())
    story.append(paragraph("7. Technologies utilisees et bilan du projet", "SectionTitle", styles))
    story.append(paragraph("7.1 Technologies - lecture approfondie", "SubTitle", styles))
    story.append(technology_table([
        ["Angular", "Framework SPA structure en composants", "Toutes les pages et composants reutilisables du projet", "HomePageComponent, AuthCard, ProfilePageComponent"],
        ["RxJS", "Programmation reactive par observables", "Gestion des flux utilisateur, requetes HTTP, refresh de session, debounce filtres", "AuthService.currentUser$, NewsService.getHomeFeed()"],
        ["FastAPI", "Framework Python rapide pour APIs", "Expose les endpoints login, signup, favoris, premium, chatbot, live", "backend/main.py"],
        ["SQLAlchemy", "ORM reliant objets Python et tables SQL", "Modelise users, news, favorite, comments, live_events", "backend/models.py + SessionLocal"],
        ["JWT", "Token signe qui transporte l'identite de session", "Token de connexion stocke en local et verifie sur endpoints proteges", "create_access_token(), verify_token()"],
        ["MySQL", "Base relationnelle durable", "Persistance des utilisateurs, interactions et rooms live", "database.py + init_db.sql"],
        ["WebSocket", "Canal bidirectionnel temps reel", "Chat live, viewer count, signaling WebRTC", "live_event_socket(), LiveRoomSocketService.connect()"],
        ["WebRTC", "Transport peer-to-peer audio/video", "Diffusion camera editeur vers viewers", "createOfferForViewer(), handleViewerOffer()"],
        ["Ollama", "Runtime local pour LLM", "Assistant premium article-aware en local", "simple_chatbot.py -> _ollama('/api/chat')"],
        ["localStorage", "Stockage navigateur persistant", "Session utilisateur et cache de news", "AuthService + NewsService.persistStore()"],
    ], styles))
    story.append(Spacer(1, 0.25 * cm))
    story.append(paragraph("7.2 Explications approfondies par technologie", "SubTitle", styles))
    tech_sections = [
        ("JWT", "JWT sert a transporter une preuve d'authentification sans stocker l'etat serveur dans une session classique. Dans NewsHub, create_access_token() fabrique un token signe avec SECRET_KEY et une date d'expiration. Ensuite AuthService.getToken() le relit, verifie son expiration et invalide la session locale si le token n'est plus valable. L'interet pratique est fort : le backend peut reconnaitre l'utilisateur sur plusieurs routes sans garder une session memoire liee au navigateur."),
        ("SQLAlchemy", "SQLAlchemy joue ici le role de pont entre les classes Python et MySQL. Par exemple models.User, models.News et models.Favorite representent directement les tables. Quand save_favorite() est execute, SQLAlchemy permet de rechercher une news, creer une relation favorite, puis commit() l'ensemble. Cette approche rend le code plus lisible qu'un grand nombre de requetes SQL ecrites a la main."),
        ("WebSocket", "WebSocket est utilise quand une requete reponse classique ne suffit plus. Dans NewsHub, la room live a besoin de pousser des messages sans recharger la page : nombre de viewers, messages chat, updates editeur, signaling WebRTC. C'est exactement le travail de live_event_socket() cote backend et de LiveRoomSocketService.connect() cote frontend."),
        ("WebRTC", "WebRTC ne remplace pas WebSocket, il le complete. WebSocket sert a dire qui parle a qui, tandis que WebRTC transporte la video et l'audio entre pairs. NewsHub l'utilise dans LiveRoomPageComponent avec createBroadcasterPeerConnection(), handleViewerOffer() et les messages offer/answer/ice_candidate. C'est un choix efficace car la video ne surcharge pas le backend."),
        ("FastAPI", "FastAPI structure proprement les routes backend et les dependances. L'application definit des endpoints courts, nommes et coherents comme /login, /favorites, /chatbot/status ou /live-events. Sa force ici est la lisibilite et la rapidite de mise en place d'une API moderne avec typage via Pydantic."),
        ("RxJS", "RxJS apporte un style reactif dans Angular. AuthService expose currentUser$ pour que plusieurs pages se mettent a jour automatiquement quand la session change. NewsService emploie shareReplay() pour mettre en cache les news et eviter des appels repetitifs. Ce n'est pas seulement technique ; c'est une vraie optimisation de l'experience utilisateur."),
        ("Ollama", "Ollama fournit une execution locale du modele. Dans simple_chatbot.py, _ollama() appelle /api/tags pour verifier les modeles installes puis /api/chat pour les reponses. Cela rend le projet autonome, sans dependance a une API cloud payante. C'est tres pertinent pour une application de demo locale."),
        ("MySQL", "MySQL est la memoire structurante du projet. Les comptes, favoris, commentaires et events live doivent survivre aux rechargements de page, ce que localStorage seul ne peut pas faire. database.py configure la connexion, cree la base si necessaire et ajoute meme certaines colonnes manquantes pour faciliter l'evolution du schema."),
    ]
    for title, text in tech_sections:
        story.append(paragraph(title, "SubTitle", styles))
        story.append(paragraph(text, "Body", styles))

    story.append(paragraph("7.3 Technologies", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "Angular : SPA, composants standalone, router, forms, reactive forms.",
                "RxJS : observables, subscriptions, debounce, finalize, shareReplay.",
                "FastAPI : exposition des routes REST et WebSocket.",
                "SQLAlchemy : mapping objet-relationnel et persistance MySQL.",
                "MySQL : stockage durable des comptes, interactions et rooms live.",
                "JWT : gestion des sessions et de l'authentification stateless.",
                "Ollama : execution locale du modele d'assistance IA.",
                "WebSocket + WebRTC : temps reel et video peer-to-peer pour les lives.",
            ],
            styles,
        )
    )

    story.append(paragraph("7.4 Forces du projet", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "Projet riche, couvrant beaucoup de besoins full-stack dans une seule application.",
                "Bonne separation des responsabilites entre composants, services frontend et routes backend.",
                "Personnalisation utile grace aux interets, au cache de news et aux parcours premium.",
                "Module live ambitieux avec vraie logique de signaling et streaming navigateur.",
                "Presence d'une securite minimum serieuse pour un projet academique ou portfolio.",
            ],
            styles,
        )
    )

    story.append(paragraph("7.5 Points d'attention et ameliorations possibles", "SubTitle", styles))
    story.extend(
        bullets(
            [
                "Uniformiser la configuration d'environnement pour eviter les URLs hardcodees comme http://127.0.0.1:8000 dans certains services.",
                "Rapprocher le brief documentaire du code reel pour lever l'ecart gemma3:12b / qwen3:14b.",
                "Renforcer les tests automatises frontend/backend, aujourd'hui peu visibles dans la structure.",
                "Ajouter une couche de gestion d'erreurs plus homogène sur tout le front.",
                "Prevoir une vraie pagination ou du lazy loading si le volume d'articles augmente.",
            ],
            styles,
        )
    )

    story.append(info_box("Bilan final", [
        "NewsHub est un projet complet et pedagogiquement fort.",
        "Il montre une vision produit claire, une architecture moderne et plusieurs niveaux d'interaction utilisateur.",
        "Une personne qui lit ce rapport doit comprendre que le projet ne se limite pas a afficher des news: il orchestre de la personnalisation, de la securite, du premium, de l'IA et du live temps reel.",
    ], styles, background="#ecfdf5"))
    story.append(Spacer(1, 0.25 * cm))
    story.append(paragraph("Fin du rapport.", "Small", styles))
    return story


def generate_pdf() -> Path:
    ensure_output_dir()
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.4 * cm,
        title="Rapport global du projet NewsHub",
        author="OpenAI Codex",
    )
    story = build_story(styles)
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return PDF_PATH


if __name__ == "__main__":
    output = generate_pdf()
    print(output)
