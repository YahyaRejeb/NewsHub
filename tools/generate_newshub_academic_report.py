from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "reports"
PDF_PATH = OUTPUT_DIR / "newshub_rapport_final.pdf"

PAGE_WIDTH, PAGE_HEIGHT = A4


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTop",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#334155"),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1d4ed8"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=4,
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
            spaceBefore=7,
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
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#0f172a"),
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
            alignment=TA_LEFT,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.7,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.7,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#475569"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            alignment=TA_LEFT,
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=10,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#0f172a"),
        )
    )
    return styles


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(doc.leftMargin, 0.7 * cm, "NewsHub - Rapport de projet")
    page_number = f"Page {doc.page}"
    width = stringWidth(page_number, "Helvetica", 8.5)
    canvas.drawString(PAGE_WIDTH - doc.rightMargin - width, 0.7 * cm, page_number)
    canvas.restoreState()


def p(text: str, style: str, styles):
    return Paragraph(text, styles[style])


def make_breakable(text: str) -> str:
    safe = escape(text)
    for token in ["/", ".", "_", "-", ":", "(", ")", ","]:
        safe = safe.replace(token, f"{token}<wbr/>")
    return safe


def table_header(text: str, styles):
    return Paragraph(escape(text), styles["TableHeader"])


def table_cell(text: str, styles):
    return Paragraph(make_breakable(text), styles["TableCell"])


def bullet_lines(items: list[str], styles):
    return [p(f"- {escape(item)}", "BulletLine", styles) for item in items]


def info_box(title: str, lines: list[str], styles, background="#eff6ff", border="#bfdbfe"):
    rows = [[p(f"<b>{escape(title)}</b>", "Body", styles)]]
    rows.extend([[p(escape(line), "Body", styles)] for line in lines])
    table = Table(rows, colWidths=[16.1 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(background)),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(border)),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def standard_table(headers: list[str], rows: list[list[str]], widths, styles, header_color="#0f172a", stripe="#f8fafc"):
    data = [[table_header(item, styles) for item in headers]]
    data.extend([[table_cell(item, styles) for item in row] for row in rows])
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor(stripe)]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def use_case_table(
    name: str,
    actors: str,
    description: str,
    preconditions: list[str],
    postconditions: list[str],
    main_scenario: list[str],
    exceptions: list[str],
    styles,
):
    rows = [
        ["Nom", name],
        ["Acteurs", actors],
        ["Description", description],
        ["Preconditions", "<br/>".join(f"- {escape(item)}" for item in preconditions)],
        ["Postconditions", "<br/>".join(f"- {escape(item)}" for item in postconditions)],
        ["Scenario nominal", "<br/>".join(f"{index + 1}. {escape(item)}" for index, item in enumerate(main_scenario))],
        ["Exceptions", "<br/>".join(f"- {escape(item)}" for item in exceptions)],
    ]
    data = [
        [
            Paragraph(f"<b>{escape(key)}</b>", styles["TableCell"]),
            Paragraph(value, styles["TableCell"]),
        ]
        for key, value in rows
    ]
    table = Table(data, colWidths=[4.2 * cm, 11.9 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2fe")),
                ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def add_multiline_text(d: Drawing, x: float, y: float, lines: list[str], font_name="Helvetica", font_size=8, color="#0f172a", leading=10):
    for index, line in enumerate(lines):
        d.add(
            String(
                x,
                y - index * leading,
                line,
                fontName=font_name,
                fontSize=font_size,
                fillColor=colors.HexColor(color),
            )
        )


def add_box(d: Drawing, x: float, y: float, w: float, h: float, title: str, lines: list[str], fill="#ffffff", stroke="#334155", title_color="#0f172a"):
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
            strokeWidth=1,
        )
    )
    d.add(
        String(
            x + 8,
            y + h - 17,
            title,
            fontName="Helvetica-Bold",
            fontSize=10,
            fillColor=colors.HexColor(title_color),
        )
    )
    add_multiline_text(d, x + 8, y + h - 31, lines, font_size=7.8, color="#475569")


def add_arrow(d: Drawing, x1: float, y1: float, x2: float, y2: float, label: str = "", color="#2563eb"):
    d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor(color), strokeWidth=1.2))
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
                (x1 + x2) / 2 - 6,
                (y1 + y2) / 2 + 8,
                label,
                fontName="Helvetica",
                fontSize=7,
                fillColor=colors.HexColor("#1e293b"),
            )
        )


def architecture_diagram():
    d = Drawing(520, 240)
    d.add(String(12, 220, "Architecture globale du systeme", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    add_box(d, 20, 128, 92, 52, "Acteurs", ["Visiteur", "Utilisateur", "Premium", "Editeur"], fill="#f8fafc")
    add_box(d, 145, 128, 108, 58, "Frontend Angular", ["Home, Profile,", "Premium, Details,", "Live Hub, Live Room"], fill="#eff6ff", stroke="#60a5fa")
    add_box(d, 285, 120, 112, 74, "Backend FastAPI", ["Authentification JWT", "News feed", "Favoris / Commentaires", "Premium / Chatbot / Live"], fill="#eef2ff", stroke="#818cf8")
    add_box(d, 430, 166, 72, 38, "MySQL", ["users, news,", "comments, live"], fill="#ecfeff", stroke="#22c55e")
    add_box(d, 430, 112, 72, 38, "NewsData", ["API news", "externes"], fill="#fff7ed", stroke="#f59e0b")
    add_box(d, 430, 58, 72, 38, "Ollama", ["qwen3:14b"], fill="#fef2f2", stroke="#ef4444")
    add_box(d, 145, 48, 252, 42, "Temps reel", ["WebSocket pour le chat et le signalement, WebRTC pour le flux video"], fill="#f8fafc", stroke="#64748b")
    add_arrow(d, 112, 154, 145, 154, "HTTP")
    add_arrow(d, 253, 154, 285, 154, "REST")
    add_arrow(d, 397, 185, 430, 185)
    add_arrow(d, 397, 131, 430, 131)
    add_arrow(d, 397, 77, 430, 77)
    add_arrow(d, 341, 120, 341, 90, "WS")
    return d


def use_case_diagram():
    d = Drawing(520, 255)
    d.add(String(12, 233, "Vue globale des cas d'utilisation", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    add_box(d, 20, 150, 86, 58, "Visiteur", ["Creer compte", "Se connecter", "Consulter le fil"], fill="#f8fafc")
    add_box(d, 20, 76, 86, 58, "Utilisateur", ["Gerer profil", "Enregistrer", "Commenter"], fill="#f8fafc")
    add_box(d, 20, 12, 86, 48, "Premium", ["Discuter avec", "l'assistant IA"], fill="#f8fafc")
    add_box(d, 408, 80, 88, 58, "Editeur", ["Creer une room", "Lancer / terminer", "Publier des updates"], fill="#f8fafc")
    add_box(d, 155, 42, 205, 174, "NewsHub", ["Fil d'actualites personnalise", "Authentification et profil", "Favoris et commentaires", "Abonnement premium", "Assistant IA premium", "Module live collaboratif"], fill="#eff6ff", stroke="#60a5fa")
    add_arrow(d, 106, 179, 155, 179)
    add_arrow(d, 106, 105, 155, 105)
    add_arrow(d, 106, 35, 155, 72)
    add_arrow(d, 408, 109, 360, 109)
    return d


def simple_flow_diagram(title: str, steps: list[str], caption: str):
    width = 520
    height = 150
    d = Drawing(width, height)
    d.add(String(12, height - 16, title, fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#0f172a")))
    colors_list = ["#eff6ff", "#e0f2fe", "#dbeafe", "#ede9fe", "#fef3c7", "#ecfccb"]
    box_w = 88
    box_h = 52
    y = 54
    start_x = 18
    gap = 12
    for index, step in enumerate(steps):
        x = start_x + index * (box_w + gap)
        add_box(
            d,
            x,
            y,
            box_w,
            box_h,
            f"Etape {index + 1}",
            step.split("\n"),
            fill=colors_list[index % len(colors_list)],
            stroke="#94a3b8",
        )
        if index < len(steps) - 1:
            add_arrow(d, x + box_w, y + box_h / 2, x + box_w + gap, y + box_h / 2)
    add_multiline_text(d, 18, 32, [caption], font_size=7.8, color="#475569")
    return d


def cover_story(styles):
    story = []
    story.append(Spacer(1, 1.2 * cm))
    story.append(p("Republique Tunisienne", "CoverTop", styles))
    story.append(p("Ministere de l'Enseignement Superieur et de la Recherche Scientifique", "CoverTop", styles))
    story.append(p("Universite de Carthage", "CoverTop", styles))
    story.append(p("Institut Superieur des Technologies de l'Information et de la Communication", "CoverTop", styles))
    story.append(Spacer(1, 1.4 * cm))
    story.append(p("RAPPORT DE PROJET FEDERE", "CoverTitle", styles))
    story.append(p("Plateforme Web de News Personnalisees avec Assistant IA : NewsHub", "CoverSubtitle", styles))
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        info_box(
            "Cadre du projet",
            [
                "Rapport realise selon une methodologie SCRUM simple et incrementale.",
                "Le document presente les besoins, l'architecture, les sprints de conception et les fonctionnalites finales du projet.",
            ],
            styles,
        )
    )
    story.append(Spacer(1, 0.9 * cm))
    story.append(p("Presente en vue de l'obtention de la Licence en Sciences de l'Informatique", "Body", styles))
    story.append(p("Parcours : Genie Logiciel et Systemes d'Information", "Body", styles))
    story.append(Spacer(1, 0.5 * cm))
    story.append(p("<b>Realise par :</b> Yahya Rejeb, Aziz Ben Slimen, Rayen Ben Yahmed", "Body", styles))
    story.append(p("<b>Annee universitaire :</b> 2025-2026", "Body", styles))
    story.append(Spacer(1, 1.2 * cm))
    story.append(
        p(
            "Version finale simplifiee, coherente et completee a partir du projet reel realise avec Angular, FastAPI, MySQL, JWT, Ollama et WebSocket/WebRTC.",
            "Small",
            styles,
        )
    )
    story.append(PageBreak())
    return story


def intro_and_summary(styles):
    story = []
    story.append(p("Sommaire", "SectionTitle", styles))
    story.extend(
        bullet_lines(
            [
                "Introduction generale",
                "Chapitre 1 : Specification des besoins",
                "Chapitre 2 : Sprint 0 - socle fonctionnel",
                "Chapitre 3 : Sprint 1 - espace utilisateur et abonnement",
                "Chapitre 4 : Sprint 2 - assistant IA et module live",
                "Conclusion generale et perspectives",
            ],
            styles,
        )
    )
    story.append(Spacer(1, 0.25 * cm))
    story.append(p("Introduction generale", "SectionTitle", styles))
    story.append(
        p(
            "La multiplication rapide des sources d'information numeriques rend l'acces a une actualite pertinente de plus en plus difficile. L'utilisateur moderne recherche non seulement des articles fiables, mais aussi une experience plus rapide, plus personnalisee et plus interactive.",
            "Body",
            styles,
        )
    )
    story.append(
        p(
            "Dans ce contexte, notre projet <b>NewsHub</b> propose une plateforme web de consultation d'actualites personnalisees. L'application permet de consulter des articles provenant d'une API externe, de filtrer le fil d'actualites, de creer un compte, de gerer son profil, d'enregistrer des favoris, de commenter les articles, de simuler un abonnement premium et d'utiliser un assistant IA local pour analyser une actualite.",
            "Body",
            styles,
        )
    )
    story.append(
        p(
            "Le projet a ete conduit selon une demarche <b>SCRUM</b> organisee en trois sprints progressifs. Le premier sprint met en place le socle de consultation et d'authentification. Le second enrichit l'espace utilisateur avec les interactions metier. Le troisieme ajoute les services avances : assistant IA premium et module live en temps reel.",
            "Body",
            styles,
        )
    )
    story.append(
        p(
            "Le present rapport adopte volontairement une forme simple et claire. Il conserve la meme logique de travail que le rapport initial, mais corrige les incoherences, complete les parties manquantes et s'aligne sur l'etat reel du projet implemente.",
            "Body",
            styles,
        )
    )
    story.append(PageBreak())
    return story


def chapter_1(styles):
    story = []
    story.append(p("Chapitre 1 - Specification des besoins", "SectionTitle", styles))
    story.append(p("1.1 Introduction", "SubTitle", styles))
    story.append(
        p(
            "L'etape de specification permet de definir clairement le perimetre du systeme, les acteurs qui interagissent avec lui, les besoins attendus ainsi que les contraintes de qualite qui doivent etre respectees. Elle constitue la base de toute la conception du projet.",
            "Body",
            styles,
        )
    )
    story.append(p("1.2 Contexte du systeme", "SubTitle", styles))
    story.append(
        p(
            "NewsHub s'inscrit dans un contexte ou l'utilisateur consulte l'actualite sur plusieurs plateformes distinctes sans toujours beneficier d'une personnalisation pertinente. Le systeme propose un point d'acces unifie aux actualites, complete par une couche de personnalisation, une experience premium et des services collaboratifs en temps reel.",
            "Body",
            styles,
        )
    )
    story.append(architecture_diagram())
    story.append(p("Figure 1 - Architecture globale de NewsHub.", "Caption", styles))
    story.append(p("1.3 Objectifs du projet", "SubTitle", styles))
    story.extend(
        bullet_lines(
            [
                "Centraliser des actualites provenant d'une source externe fiable.",
                "Adapter le fil d'actualites aux centres d'interet de l'utilisateur.",
                "Offrir une experience de consultation simple, rapide et responsive.",
                "Ajouter des fonctions d'interaction : favoris, commentaires, profil et premium.",
                "Proposer une assistance IA locale reservee aux utilisateurs premium.",
                "Etendre la plateforme avec un module live pour les editeurs et les lecteurs.",
            ],
            styles,
        )
    )
    story.append(p("1.4 Identification des acteurs", "SubTitle", styles))
    story.append(
        standard_table(
            ["Acteur", "Description", "Responsabilites principales"],
            [
                ["Visiteur", "Utilisateur non authentifie", "Creer un compte, se connecter, consulter le fil, filtrer les actualites"],
                ["Utilisateur", "Utilisateur authentifie standard", "Gerer son profil, enregistrer des articles, commenter, acceder a son espace personnel"],
                ["Utilisateur premium", "Utilisateur authentifie avec abonnement actif", "Utiliser l'assistant IA, acceder aux services reserves au premium"],
                ["Editeur", "Utilisateur avec role editor", "Creer une room live, lancer un direct, publier des updates et moderer son espace live"],
            ],
            [2.9 * cm, 4.2 * cm, 9.0 * cm],
            styles,
            header_color="#1d4ed8",
            stripe="#eff6ff",
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(p("1.5 Besoins fonctionnels", "SubTitle", styles))
    story.extend(
        bullet_lines(
            [
                "Creer un compte avec selection des centres d'interet.",
                "Se connecter et recuperer une session securisee.",
                "Consulter un fil d'actualites personnalise.",
                "Filtrer les actualites par categorie, source, pays, date et type de donnees.",
                "Gerer les informations du profil utilisateur.",
                "Enregistrer ou retirer une actualite des favoris.",
                "Commenter une actualite.",
                "Simuler un abonnement premium.",
                "Discuter avec un assistant IA premium a propos d'un article.",
                "Creer, demarrer et terminer un evenement live.",
                "Participer a un chat live et consulter les updates de l'editeur.",
            ],
            styles,
        )
    )
    story.append(p("1.6 Besoins non fonctionnels", "SubTitle", styles))
    story.extend(
        bullet_lines(
            [
                "Ergonomie : interface claire, moderne et responsive sur mobile, tablette et ordinateur.",
                "Performance : affichage rapide grace au cache local du fil d'actualites et a la reutilisation des donnees prechargees.",
                "Securite : mots de passe haches, gestion des roles, JWT pour la session et protection des routes sensibles.",
                "Maintenabilite : separation nette entre frontend Angular, backend FastAPI et base de donnees MySQL.",
                "Extensibilite : architecture permettant l'ajout de modules premium, IA ou live sans refonte majeure.",
                "Disponibilite : API et services concus pour fonctionner de maniere continue, avec gestion d'erreurs en cas d'indisponibilite externe.",
            ],
            styles,
        )
    )
    story.append(p("1.7 Diagramme global des cas d'utilisation", "SubTitle", styles))
    story.append(use_case_diagram())
    story.append(p("Figure 2 - Vue globale des principaux cas d'utilisation.", "Caption", styles))
    story.append(p("1.8 Backlog du produit", "SubTitle", styles))
    story.append(
        standard_table(
            ["ID", "User story", "Priorite", "Sprint"],
            [
                ["US1", "En tant que visiteur, je veux creer un compte afin d'acceder a la plateforme.", "1", "Sprint 0"],
                ["US2", "En tant que visiteur, je veux me connecter afin d'acceder a mon espace personnel.", "1", "Sprint 0"],
                ["US3", "En tant que visiteur, je veux consulter les actualites afin de rester informe.", "1", "Sprint 0"],
                ["US4", "En tant que visiteur, je veux filtrer les actualites afin de personnaliser mon fil.", "1", "Sprint 0"],
                ["US5", "En tant qu'utilisateur, je veux gerer mon profil afin de mettre a jour mes informations.", "2", "Sprint 1"],
                ["US6", "En tant qu'utilisateur, je veux enregistrer une actualite afin d'y revenir plus tard.", "2", "Sprint 1"],
                ["US7", "En tant qu'utilisateur, je veux commenter une actualite afin d'exprimer mon opinion.", "2", "Sprint 1"],
                ["US8", "En tant qu'utilisateur, je veux activer le premium afin de debloquer les services avances.", "2", "Sprint 1"],
                ["US9", "En tant qu'utilisateur premium, je veux discuter avec un assistant IA a propos d'un article.", "3", "Sprint 2"],
                ["US10", "En tant qu'editeur, je veux creer un live afin de diffuser une actualite en direct.", "3", "Sprint 2"],
                ["US11", "En tant qu'editeur, je veux lancer et terminer un live afin de piloter la diffusion.", "3", "Sprint 2"],
                ["US12", "En tant qu'utilisateur, je veux participer a un live afin d'echanger en temps reel.", "3", "Sprint 2"],
            ],
            [1.3 * cm, 10.0 * cm, 1.8 * cm, 3.0 * cm],
            styles,
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(p("1.9 Environnement de travail", "SubTitle", styles))
    story.append(
        standard_table(
            ["Technologie", "Role dans le projet"],
            [
                ["Angular", "Developpement du frontend, navigation entre les pages, composants reutilisables et experience utilisateur."],
                ["FastAPI", "Developpement de l'API backend et exposition des routes REST et WebSocket."],
                ["MySQL", "Stockage durable des utilisateurs, articles, favoris, commentaires et rooms live."],
                ["SQLAlchemy", "Mapping objet relationnel entre Python et MySQL."],
                ["JWT", "Gestion des sessions et de l'authentification securisee."],
                ["NewsData", "API externe utilisee pour recuperer les actualites."],
                ["Ollama + qwen3:14b", "Assistant IA local pour l'analyse des articles premium."],
                ["WebSocket / WebRTC", "Communication temps reel et diffusion live."],
                ["GitHub", "Suivi de version et collaboration entre membres de l'equipe."],
            ],
            [4.2 * cm, 11.9 * cm],
            styles,
            header_color="#0f172a",
            stripe="#f8fafc",
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(p("1.10 Conclusion", "SubTitle", styles))
    story.append(
        p(
            "Ce premier chapitre a permis de definir les objectifs du projet, de deliminer les acteurs et de structurer le backlog du produit. Les chapitres suivants detailent l'avancement du travail selon les sprints SCRUM retenus.",
            "Body",
            styles,
        )
    )
    story.append(PageBreak())
    return story


def chapter_2(styles):
    story = []
    story.append(p("Chapitre 2 - Sprint 0 : socle fonctionnel", "SectionTitle", styles))
    story.append(p("2.1 Introduction", "SubTitle", styles))
    story.append(
        p(
            "Le Sprint 0 pose les fondations du projet. Il couvre les besoins de priorite 1 : creation de compte, authentification, consultation du fil d'actualites et filtrage des news. L'objectif de ce sprint est d'obtenir un produit navigable et demonstrable tres tot.",
            "Body",
            styles,
        )
    )
    story.append(p("2.2 Backlog du Sprint 0", "SubTitle", styles))
    story.append(
        standard_table(
            ["ID", "User story", "Livrable attendu"],
            [
                ["US1", "Creer un compte", "Ecran d'inscription en deux etapes avec choix de centres d'interet"],
                ["US2", "Se connecter", "Authentification par email et mot de passe avec jeton JWT"],
                ["US3", "Consulter le fil d'actualites", "Page d'accueil affichant des cartes d'articles"],
                ["US4", "Filtrer les actualites", "Filtrage par categorie, source, pays, date et type"],
            ],
            [1.4 * cm, 6.1 * cm, 8.6 * cm],
            styles,
            header_color="#1d4ed8",
            stripe="#eff6ff",
        )
    )
    story.append(p("2.3 Raffinement des cas d'utilisation", "SubTitle", styles))
    story.append(p("2.3.1 Creer un compte", "Small", styles))
    story.append(
        use_case_table(
            "Creer un compte",
            "Visiteur",
            "Permet au visiteur de creer un compte et de choisir jusqu'a trois centres d'interet.",
            ["Le systeme est accessible.", "L'adresse email n'est pas deja utilisee."],
            ["Le compte est cree.", "L'utilisateur est connecte automatiquement."],
            [
                "Le visiteur ouvre l'ecran d'inscription.",
                "Il saisit ses informations personnelles.",
                "Le systeme verifie la validite de l'email et du mot de passe.",
                "Le visiteur choisit ses centres d'interet.",
                "Le backend cree le compte et retourne un jeton de session.",
            ],
            ["Email deja utilise.", "Depassement de la limite de centres d'interet.", "Erreur reseau ou base de donnees indisponible."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("2.3.2 Se connecter", "Small", styles))
    story.append(
        use_case_table(
            "Se connecter",
            "Visiteur",
            "Permet a un utilisateur existant d'acceder a son espace personnel.",
            ["Le compte existe.", "Le visiteur possede des identifiants valides."],
            ["La session est ouverte.", "Le jeton d'authentification est stocke dans le navigateur."],
            [
                "L'utilisateur ouvre la page de connexion.",
                "Il saisit son email et son mot de passe.",
                "Le backend verifie les identifiants.",
                "Le systeme cree un JWT puis redirige l'utilisateur.",
            ],
            ["Email ou mot de passe invalide.", "Session expiree ou token incorrect."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("2.3.3 Consulter le fil d'actualites", "Small", styles))
    story.append(
        use_case_table(
            "Consulter le fil d'actualites",
            "Visiteur, Utilisateur",
            "Affiche les actualites prechargees et dedoublonnees dans une interface claire.",
            ["Le service de news est disponible ou le cache local existe."],
            ["Le fil d'actualites est affiche."],
            [
                "L'utilisateur ouvre la page d'accueil.",
                "Le frontend charge les categories predefinies.",
                "Le backend recupere les donnees depuis l'API externe.",
                "Les articles sont tries, dedoublonnes puis affiches sous forme de cartes.",
            ],
            ["API externe indisponible.", "Aucun article disponible pour un filtre donne."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("2.3.4 Filtrer les actualites", "Small", styles))
    story.append(
        use_case_table(
            "Filtrer les actualites",
            "Visiteur, Utilisateur",
            "Permet de restreindre l'affichage selon les preferences de navigation.",
            ["Le fil d'actualites est deja charge."],
            ["Les articles affiches correspondent aux filtres choisis."],
            [
                "L'utilisateur choisit une categorie ou un filtre supplementaire.",
                "Le frontend applique les filtres avec un leger debounce.",
                "Le fil est recompose sans rechargement lourd.",
            ],
            ["Aucun resultat trouve pour les filtres selectionnes."],
            styles,
        )
    )
    story.append(p("2.4 Conception du Sprint 0", "SubTitle", styles))
    story.append(
        simple_flow_diagram(
            "Conception logique du Sprint 0",
            [
                "Inscription\net validation",
                "Connexion\nJWT",
                "Chargement\ndes news",
                "Cache local\net filtres",
                "Affichage\nsur Home",
            ],
            "Le Sprint 0 relie l'authentification, la recuperation des articles et la composition de l'interface d'accueil.",
        )
    )
    story.append(p("Figure 3 - Flux principal du Sprint 0.", "Caption", styles))
    story.append(p("2.5 Realisation du Sprint 0", "SubTitle", styles))
    story.append(
        standard_table(
            ["Bloc realise", "Resultat obtenu"],
            [
                ["Inscription", "Formulaire en deux etapes avec verification d'email et selection d'interets."],
                ["Connexion", "Authentification avec retour d'un token et decor de session utilisateur."],
                ["Accueil", "Cartes d'articles, page hero, experience responsive et categories prechargees."],
                ["Filtres", "Recherche rapide par categorie, source, pays, date et type de donnees."],
                ["Navigation", "Routes principales : home, login, register et details d'un article."],
            ],
            [4.5 * cm, 11.6 * cm],
            styles,
            header_color="#0f172a",
            stripe="#f8fafc",
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        info_box(
            "Bilan du Sprint 0",
            [
                "Le systeme devient exploitable des le premier sprint.",
                "Le visiteur peut deja naviguer, consulter des actualites et entrer dans un parcours d'authentification complet.",
            ],
            styles,
            background="#ecfdf5",
            border="#86efac",
        )
    )
    story.append(PageBreak())
    return story


def chapter_3(styles):
    story = []
    story.append(p("Chapitre 3 - Sprint 1 : espace utilisateur et abonnement", "SectionTitle", styles))
    story.append(p("3.1 Introduction", "SubTitle", styles))
    story.append(
        p(
            "Le Sprint 1 enrichit le produit avec les fonctions d'interaction attendues dans une plateforme moderne. L'utilisateur ne se contente plus de lire les actualites ; il personnalise son compte, sauvegarde des articles, commente et active l'offre premium.",
            "Body",
            styles,
        )
    )
    story.append(p("3.2 Backlog du Sprint 1", "SubTitle", styles))
    story.append(
        standard_table(
            ["ID", "User story", "Livrable attendu"],
            [
                ["US5", "Gerer son profil", "Tableau de bord profil avec mise a jour des informations et du mot de passe"],
                ["US6", "Enregistrer une actualite", "Favoris persistants et recuperables depuis le profil"],
                ["US7", "Commenter une actualite", "Publication et lecture de commentaires associes a un article"],
                ["US8", "Activer le premium", "Simulation de paiement et mise a jour de l'etat premium"],
            ],
            [1.4 * cm, 6.2 * cm, 8.5 * cm],
            styles,
            header_color="#1d4ed8",
            stripe="#eff6ff",
        )
    )
    story.append(p("3.3 Raffinement des cas d'utilisation", "SubTitle", styles))
    story.append(p("3.3.1 Gerer le profil", "Small", styles))
    story.append(
        use_case_table(
            "Gerer le profil",
            "Utilisateur, Utilisateur premium",
            "Mettre a jour le nom complet, l'email, le mot de passe et les donnees de session.",
            ["L'utilisateur est authentifie."],
            ["Les informations du compte sont mises a jour.", "Un nouveau token peut etre renvoye si necessaire."],
            [
                "L'utilisateur ouvre son tableau de bord.",
                "Le systeme charge les informations actuelles du profil.",
                "L'utilisateur modifie les champs souhaites.",
                "Le backend valide les donnees puis enregistre les changements.",
                "Le systeme affiche un message de confirmation.",
            ],
            ["Email deja utilise.", "Mot de passe actuel incorrect.", "Nouveau mot de passe trop court."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("3.3.2 Enregistrer une actualite", "Small", styles))
    story.append(
        use_case_table(
            "Enregistrer une actualite",
            "Utilisateur, Utilisateur premium",
            "Sauvegarder une actualite dans les favoris pour la retrouver plus tard.",
            ["L'utilisateur est authentifie.", "L'article possede une URL valide."],
            ["L'article est enregistre dans la base de donnees et visible dans le profil."],
            [
                "L'utilisateur ouvre le detail d'un article.",
                "Il clique sur le bouton de sauvegarde.",
                "Le backend cree ou met a jour l'enregistrement local de l'article.",
                "L'article apparait dans la liste des favoris.",
            ],
            ["Utilisateur non connecte.", "Article sans source ou URL exploitable."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("3.3.3 Commenter une actualite", "Small", styles))
    story.append(
        use_case_table(
            "Commenter une actualite",
            "Utilisateur, Utilisateur premium",
            "Ajouter un commentaire sur une actualite affichee dans la page de details.",
            ["L'utilisateur est authentifie.", "L'article est charge dans la page de details."],
            ["Le commentaire est enregistre et visible dans la liste."],
            [
                "L'utilisateur saisit un message dans la zone de commentaire.",
                "Le systeme verifie que le texte n'est pas vide.",
                "Le backend enregistre le commentaire dans la base.",
                "La liste des commentaires est rechargee.",
            ],
            ["Commentaire vide.", "Erreur de persistance."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("3.3.4 Activer le premium", "Small", styles))
    story.append(
        use_case_table(
            "Activer le premium",
            "Utilisateur",
            "Simuler un paiement pour debloquer les fonctions premium.",
            ["L'utilisateur est authentifie.", "Un plan d'abonnement est selectionne."],
            ["Le compte passe a l'etat premium.", "Le plan et la date d'activation sont memorises."],
            [
                "L'utilisateur ouvre la page premium.",
                "Il choisit un plan mensuel ou annuel.",
                "Il remplit un formulaire de paiement simule.",
                "Le backend active l'etat premium du compte.",
            ],
            ["Formulaire incomplet.", "Plan invalide.", "Utilisateur non connecte."],
            styles,
        )
    )
    story.append(p("3.4 Conception du Sprint 1", "SubTitle", styles))
    story.append(
        simple_flow_diagram(
            "Conception logique du Sprint 1",
            [
                "Profil\nmise a jour",
                "Favoris\npersistants",
                "Commentaires\nsur article",
                "Premium\nsimulation",
                "Session\nactualisee",
            ],
            "Le Sprint 1 consolide la relation entre l'utilisateur et la plateforme.",
        )
    )
    story.append(p("Figure 4 - Flux principal du Sprint 1.", "Caption", styles))
    story.append(p("3.5 Realisation du Sprint 1", "SubTitle", styles))
    story.append(
        standard_table(
            ["Bloc realise", "Resultat obtenu"],
            [
                ["Profil utilisateur", "Page de profil avec formulaire, validations, retours d'erreur et zone des articles sauvegardes."],
                ["Favoris", "Ajout, suppression et verification d'etat d'un article pour l'utilisateur courant."],
                ["Commentaires", "Lecture et publication des commentaires dans la page de details."],
                ["Premium", "Simulation d'abonnement avec choix de plan et mise a jour de la session."],
                ["Securite", "Protection des appels via JWT et verification du compte courant sur les routes sensibles."],
            ],
            [4.5 * cm, 11.6 * cm],
            styles,
            header_color="#0f172a",
            stripe="#f8fafc",
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        info_box(
            "Bilan du Sprint 1",
            [
                "L'application passe d'un simple lecteur d'actualites a une vraie plateforme utilisateur.",
                "Le profil, les favoris, les commentaires et le premium introduisent une logique metier complete et realiste.",
            ],
            styles,
            background="#ecfdf5",
            border="#86efac",
        )
    )
    story.append(PageBreak())
    return story


def chapter_4(styles):
    story = []
    story.append(p("Chapitre 4 - Sprint 2 : assistant IA et module live", "SectionTitle", styles))
    story.append(p("4.1 Introduction", "SubTitle", styles))
    story.append(
        p(
            "Le Sprint 2 correspond a la partie la plus innovante du projet. Il ajoute a la plateforme deux dimensions avancees : un assistant IA premium capable d'expliquer une actualite, et un module live permettant a un editeur de diffuser et d'animer un evenement en temps reel.",
            "Body",
            styles,
        )
    )
    story.append(p("4.2 Backlog du Sprint 2", "SubTitle", styles))
    story.append(
        standard_table(
            ["ID", "User story", "Livrable attendu"],
            [
                ["US9", "Discuter avec l'assistant IA", "Panneau de chat premium lie a l'article consulte"],
                ["US10", "Creer un live", "Creation d'un evenement live reservee au role editor"],
                ["US11", "Lancer ou terminer un live", "Pilotage du statut du direct en temps reel"],
                ["US12", "Participer a un live", "Chat temps reel, updates editeur et diffusion video"],
            ],
            [1.4 * cm, 6.0 * cm, 8.7 * cm],
            styles,
            header_color="#1d4ed8",
            stripe="#eff6ff",
        )
    )
    story.append(p("4.3 Raffinement des cas d'utilisation", "SubTitle", styles))
    story.append(p("4.3.1 Discuter avec l'assistant IA", "Small", styles))
    story.append(
        use_case_table(
            "Discuter avec l'assistant IA",
            "Utilisateur premium",
            "Interroger un assistant local pour resumer ou expliquer un article en cours de lecture.",
            ["L'utilisateur est premium.", "L'article est ouvert.", "Ollama est disponible localement."],
            ["Une reponse est generee et affichee dans l'interface de discussion."],
            [
                "L'utilisateur premium ouvre le panneau assistant.",
                "Le systeme verifie l'etat du runtime Ollama.",
                "Un bref resume de l'article est prepare.",
                "L'utilisateur envoie une question.",
                "Le backend transmet le contexte de l'article au modele qwen3:14b.",
                "La reponse est retournee au frontend et affichee.",
            ],
            ["Ollama n'est pas demarre.", "Le modele n'est pas installe.", "L'article contient trop peu de texte."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("4.3.2 Gerer un evenement live", "Small", styles))
    story.append(
        use_case_table(
            "Creer, lancer et terminer un live",
            "Editeur",
            "Permet a un utilisateur de role editor de planifier puis d'animer un direct.",
            ["L'utilisateur est authentifie avec le role editor."],
            ["La room live est creee, passe a l'etat live puis peut etre cloturee proprement."],
            [
                "L'editeur cree un evenement live avec titre, description et categorie.",
                "Le backend enregistre la room avec le statut upcoming.",
                "L'editeur lance le live lorsque la diffusion commence.",
                "Les participants recoivent les changements d'etat en temps reel.",
                "L'editeur peut terminer la room a la fin de l'evenement.",
            ],
            ["Compte non autorise.", "Room inexistante.", "Erreur de diffusion ou de synchronisation."],
            styles,
        )
    )
    story.append(Spacer(1, 0.15 * cm))
    story.append(p("4.3.3 Participer a un live", "Small", styles))
    story.append(
        use_case_table(
            "Participer a un live",
            "Utilisateur, Utilisateur premium",
            "Consulter un direct, echanger par chat et recevoir les updates de l'editeur.",
            ["L'utilisateur est authentifie.", "La room est accessible selon son niveau d'acces."],
            ["Le participant est connecte a la room et recoit les messages temps reel."],
            [
                "L'utilisateur ouvre une room live.",
                "Le frontend ouvre un WebSocket securise avec le token utilisateur.",
                "Le systeme transmet le nombre de viewers et l'etat de la room.",
                "Les messages de chat et updates sont diffuses en temps reel.",
                "Le flux video transite entre navigateurs via WebRTC.",
            ],
            ["Acces refuse pour une room premium.", "Deconnexion WebSocket.", "Fin du direct."],
            styles,
        )
    )
    story.append(p("4.4 Conception du Sprint 2", "SubTitle", styles))
    story.append(
        simple_flow_diagram(
            "Conception logique de l'assistant IA",
            [
                "Article\ncharge",
                "Verification\nOllama",
                "Resume\nprealable",
                "Question\nutilisateur",
                "Reponse\nqwen3:14b",
            ],
            "Le chat premium reutilise le contexte de l'article pour produire une reponse plus pertinente.",
        )
    )
    story.append(p("Figure 5 - Flux fonctionnel de l'assistant IA.", "Caption", styles))
    story.append(
        simple_flow_diagram(
            "Conception logique du module live",
            [
                "Creation\nde la room",
                "Passage\nau statut live",
                "WebSocket\nchat / updates",
                "WebRTC\nvideo",
                "Cloture\nde la room",
            ],
            "Le backend pilote l'etat metier tandis que la video est echangée directement entre navigateurs.",
        )
    )
    story.append(p("Figure 6 - Flux fonctionnel du module live.", "Caption", styles))
    story.append(p("4.5 Realisation du Sprint 2", "SubTitle", styles))
    story.append(
        standard_table(
            ["Bloc realise", "Resultat obtenu"],
            [
                ["Assistant IA", "Verification de l'etat Ollama, resume d'article et questions/reponses basees sur le contexte courant."],
                ["Modele local", "Utilisation de qwen3:14b comme modele prefere pour l'assistance premium."],
                ["Rooms live", "Creation, consultation, lancement, cloture et suppression d'evenements live."],
                ["Temps reel", "WebSocket pour le chat, les updates editeur et le nombre de viewers."],
                ["Diffusion video", "Signalement WebRTC pour limiter la charge du backend sur le transport media."],
                ["Controle d'acces", "Role editor pour la gestion des rooms et acces premium pour certaines salles reservees."],
            ],
            [4.5 * cm, 11.6 * cm],
            styles,
            header_color="#0f172a",
            stripe="#f8fafc",
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        info_box(
            "Bilan du Sprint 2",
            [
                "Ce sprint donne au projet une valeur ajoutee forte : intelligence locale, premium et collaboration temps reel.",
                "Il montre que NewsHub depasse une simple application de lecture pour devenir une plateforme riche et evolutive.",
            ],
            styles,
            background="#ecfdf5",
            border="#86efac",
        )
    )
    story.append(PageBreak())
    return story


def conclusion(styles):
    story = []
    story.append(p("Conclusion generale", "SectionTitle", styles))
    story.append(
        p(
            "A l'issue de ce projet, nous avons concu et realise une plateforme web complete de news personnalisees nommee <b>NewsHub</b>. Le systeme repond aux besoins de base d'une application d'actualites moderne : consultation, filtrage, personnalisation, gestion de compte, sauvegarde d'articles et interactions communautaires.",
            "Body",
            styles,
        )
    )
    story.append(
        p(
            "La demarche SCRUM adoptee a permis une progression logique. Le Sprint 0 a mis en place le socle fonctionnel. Le Sprint 1 a structure l'espace utilisateur et l'offre premium. Le Sprint 2 a apporte des services differenciants avec l'assistant IA local et le module live temps reel.",
            "Body",
            styles,
        )
    )
    story.append(
        p(
            "Sur le plan technique, le projet s'appuie sur une architecture moderne et modulaire : Angular pour l'interface, FastAPI pour l'API, MySQL pour la persistance, JWT pour la securite, Ollama pour l'assistance IA locale et WebSocket/WebRTC pour le temps reel. Cette organisation rend la solution lisible, maintenable et extensible.",
            "Body",
            styles,
        )
    )
    story.append(p("Perspectives", "SubTitle", styles))
    story.extend(
        bullet_lines(
            [
                "Ajouter une passerelle de paiement reelle pour l'abonnement premium.",
                "Introduire des tests automatises frontend et backend plus complets.",
                "Renforcer la moderation et les notifications des rooms live.",
                "Mettre en place un moteur de recommandation plus avance base sur le comportement utilisateur.",
                "Ajouter une pagination intelligente et des statistiques d'usage pour les editeurs.",
            ],
            styles,
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        info_box(
            "Bilan final",
            [
                "NewsHub constitue un projet pedagogique solide, moderne et valorisant.",
                "Le rapport final est maintenant coherent avec la realisation technique du projet et complet sur le plan methodologique.",
            ],
            styles,
            background="#eff6ff",
            border="#93c5fd",
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(p("Fin du rapport.", "Small", styles))
    return story


def build_story(styles):
    story = []
    story.extend(cover_story(styles))
    story.extend(intro_and_summary(styles))
    story.extend(chapter_1(styles))
    story.extend(chapter_2(styles))
    story.extend(chapter_3(styles))
    story.extend(chapter_4(styles))
    story.extend(conclusion(styles))
    return story


def generate_pdf() -> Path:
    ensure_output_dir()
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.4 * cm,
        title="Rapport final du projet NewsHub",
        author="OpenAI Codex",
    )
    doc.build(build_story(styles), onFirstPage=add_page_number, onLaterPages=add_page_number)
    return PDF_PATH


if __name__ == "__main__":
    print(generate_pdf())
