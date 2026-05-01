from __future__ import annotations

import shutil
from pathlib import Path
from textwrap import dedent

import pypdf
from reportlab.graphics.shapes import Drawing, Line, Rect, String
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
ORIGINAL_PDF = Path(r"C:\Users\hp\Downloads\news_v1__Copy___Copy___Copy_.pdf")
OUT_DIR = ROOT / "reports" / "overleaf_newshub_final"
ORIGINAL_COPY = OUT_DIR / "news_v1_original.pdf"
TEX_PATH = OUT_DIR / "main.tex"
APPENDIX_PDF = OUT_DIR / "newshub_pages_finales.pdf"
FINAL_PDF = OUT_DIR / "newshub_rapport_resultat.pdf"

PAGE_WIDTH, _PAGE_HEIGHT = A4


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def copy_original() -> None:
    shutil.copy2(ORIGINAL_PDF, ORIGINAL_COPY)


def write_overleaf_source() -> None:
    source = r"""
\documentclass[12pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[french]{babel}
\usepackage{geometry}
\usepackage{pdfpages}
\usepackage{tikz}
\usepackage{array}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage{hyperref}

\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}
\setlist[itemize]{label=--}

\begin{document}

% Le rapport initial est garde comme base pour ne pas changer beaucoup le document.
\includepdf[pages=-]{news_v1_original.pdf}

\chapter*{Réalisation du Sprint 1}
\addcontentsline{toc}{chapter}{Réalisation du Sprint 1}
La réalisation du Sprint 1 complète les fonctionnalités principales de la plateforme NewsHub. Cette partie ajoute les interfaces et les traitements liés à l'espace utilisateur, aux favoris, aux commentaires, à l'abonnement premium et au chatbot IA.

\section*{Interfaces réalisées}
\begin{itemize}
\item Interface de gestion du profil : consultation et modification des informations personnelles.
\item Interface des favoris : affichage des actualités enregistrées par l'utilisateur.
\item Interface des commentaires : ajout et consultation des commentaires liés à une actualité.
\item Interface d'abonnement : simulation d'une offre premium.
\item Interface du chatbot : discussion avec l'assistant IA à partir d'une actualité.
\end{itemize}

\section*{Diagramme de déploiement}
\begin{center}
\begin{tikzpicture}[node distance=1.8cm, every node/.style={draw, rounded corners, align=center, minimum width=3cm, minimum height=1cm}]
\node (client) {Navigateur\\Angular};
\node[right of=client, xshift=3cm] (api) {Serveur API\\FastAPI};
\node[right of=api, xshift=3cm] (db) {Base de données\\MySQL};
\node[below of=api] (ollama) {Service IA\\Ollama};
\node[above of=api] (news) {API externe\\Newsdata.io};
\draw[->] (client) -- (api);
\draw[->] (api) -- (db);
\draw[->] (api) -- (news);
\draw[->] (api) -- (ollama);
\end{tikzpicture}
\end{center}

\chapter*{Conclusion générale}
\addcontentsline{toc}{chapter}{Conclusion générale}
Dans ce projet fédéré, nous avons conçu et réalisé NewsHub, une plateforme web d'actualités personnalisées avec chatbot IA. Le système permet à l'utilisateur de consulter des actualités, filtrer le contenu, créer un compte, se connecter, gérer son profil, enregistrer des articles, commenter, s'abonner et discuter avec un assistant intelligent.

La méthode SCRUM nous a permis d'organiser le travail en sprints. Le Sprint 0 a assuré les fonctionnalités de base, telles que l'inscription, la connexion, la consultation et le filtrage des actualités. Le Sprint 1 a enrichi la plateforme avec les fonctionnalités liées au profil, aux favoris, aux commentaires, à l'abonnement et au chatbot.

Sur le plan technique, le projet repose sur une architecture web moderne composée d'un frontend Angular, d'un backend FastAPI, d'une base de données MySQL, d'une API externe d'actualités et d'un service IA local basé sur Ollama.

\section*{Perspectives}
Comme perspectives, nous pouvons proposer l'intégration d'un paiement réel, l'amélioration du système de recommandation, l'ajout de notifications, la mise en place de tests automatisés et le renforcement de la modération des commentaires et des espaces live.

\end{document}
"""
    TEX_PATH.write_text(dedent(source).strip() + "\n", encoding="utf-8")


def styles():
    s = getSampleStyleSheet()
    s.add(
        ParagraphStyle(
            name="ChapterTitle",
            parent=s["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=23,
            textColor=colors.HexColor("#111827"),
            spaceAfter=12,
        )
    )
    s.add(
        ParagraphStyle(
            name="SubTitle",
            parent=s["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    s.add(
        ParagraphStyle(
            name="Body",
            parent=s["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15.5,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        )
    )
    s.add(
        ParagraphStyle(
            name="BulletLine",
            parent=s["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            leftIndent=12,
            firstLineIndent=-8,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )
    )
    s.add(
        ParagraphStyle(
            name="Caption",
            parent=s["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )
    return s


def p(text: str, style: str, s):
    return Paragraph(text, s[style])


def bullet(items: list[str], s):
    return [p(f"- {item}", "BulletLine", s) for item in items]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(doc.leftMargin, 0.72 * cm, "NewsHub - Pages finales")
    label = str(doc.page)
    canvas.drawString(PAGE_WIDTH - doc.rightMargin - stringWidth(label, "Helvetica", 8.5), 0.72 * cm, label)
    canvas.restoreState()


def deployment_drawing() -> Drawing:
    d = Drawing(520, 190)
    d.add(String(12, 170, "Diagramme de déploiement simplifié", fontName="Helvetica-Bold", fontSize=12, fillColor=colors.HexColor("#111827")))
    boxes = [
        (20, 95, 105, 50, "Navigateur", ["Angular", "Interface web"]),
        (155, 95, 105, 50, "Serveur API", ["FastAPI", "REST / JWT"]),
        (290, 95, 90, 50, "MySQL", ["Utilisateurs", "Favoris", "Commentaires"]),
        (415, 126, 82, 38, "NewsData", ["Actualités"]),
        (415, 60, 82, 38, "Ollama", ["Chatbot IA"]),
        (155, 22, 225, 38, "Temps réel", ["WebSocket et WebRTC pour les espaces live"]),
    ]
    for x, y, w, h, title, lines in boxes:
        d.add(Rect(x, y, w, h, rx=7, ry=7, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#475569"), strokeWidth=0.9))
        d.add(String(x + 8, y + h - 16, title, fontName="Helvetica-Bold", fontSize=9, fillColor=colors.HexColor("#111827")))
        for index, line in enumerate(lines):
            d.add(String(x + 8, y + h - 29 - index * 9, line, fontName="Helvetica", fontSize=7.2, fillColor=colors.HexColor("#475569")))
    for x1, y1, x2, y2 in [
        (125, 120, 155, 120),
        (260, 120, 290, 120),
        (260, 120, 415, 145),
        (260, 100, 415, 79),
        (210, 95, 230, 60),
    ]:
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#2563eb"), strokeWidth=1.1))
    return d


def make_appendix_pdf() -> None:
    s = styles()
    story = []
    story.append(p("Réalisation du Sprint 1", "ChapterTitle", s))
    story.append(
        p(
            "La réalisation du Sprint 1 complète les fonctionnalités principales de la plateforme NewsHub. Cette partie ajoute les interfaces et les traitements liés à l'espace utilisateur, aux favoris, aux commentaires, à l'abonnement premium et au chatbot IA.",
            "Body",
            s,
        )
    )
    story.append(p("Interfaces réalisées", "SubTitle", s))
    story.extend(
        bullet(
            [
                "Interface de gestion du profil : consultation et modification des informations personnelles.",
                "Interface des favoris : affichage des actualités enregistrées par l'utilisateur.",
                "Interface des commentaires : ajout et consultation des commentaires liés à une actualité.",
                "Interface d'abonnement : simulation d'une offre premium.",
                "Interface du chatbot : discussion avec l'assistant IA à partir d'une actualité.",
            ],
            s,
        )
    )
    story.append(p("Description technique de la réalisation", "SubTitle", s))
    story.append(
        p(
            "Le frontend Angular communique avec le backend FastAPI à travers des services dédiés. Les données sont stockées dans MySQL. Les routes sensibles utilisent un jeton JWT afin de protéger l'accès aux informations personnelles, aux favoris et à l'abonnement premium.",
            "Body",
            s,
        )
    )
    story.append(
        Table(
            [
                ["Fonctionnalité", "Résultat obtenu"],
                ["Profil", "Modification du nom, de l'email, du mot de passe et de la photo de profil."],
                ["Favoris", "Sauvegarde, suppression et affichage des articles enregistrés."],
                ["Commentaires", "Ajout et consultation des commentaires sur une actualité."],
                ["Premium", "Activation simulée d'un abonnement pour accéder au chatbot."],
                ["Chatbot", "Assistant IA local basé sur Ollama et le modèle qwen3:14b."],
            ],
            colWidths=[4.2 * cm, 11.7 * cm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        )
    )
    story.append(PageBreak())
    story.append(p("Diagramme de déploiement", "ChapterTitle", s))
    story.append(
        p(
            "Conformément à l'architecture de travail proposée dans l'exemple, le diagramme de déploiement est modélisé une seule fois. Il montre les principaux blocs techniques utilisés par NewsHub.",
            "Body",
            s,
        )
    )
    story.append(deployment_drawing())
    story.append(p("Figure : Diagramme de déploiement du système NewsHub.", "Caption", s))
    story.append(
        p(
            "Le navigateur exécute l'application Angular. Le serveur FastAPI centralise les traitements métier, l'authentification, les favoris, les commentaires, l'abonnement et les appels vers les services externes. MySQL assure la persistance des données, tandis que NewsData fournit les actualités et Ollama fournit l'assistance IA.",
            "Body",
            s,
        )
    )
    story.append(PageBreak())
    story.append(p("Conclusion générale", "ChapterTitle", s))
    story.append(
        p(
            "Dans ce projet fédéré, nous avons conçu et réalisé NewsHub, une plateforme web d'actualités personnalisées avec chatbot IA. Le système permet à l'utilisateur de consulter des actualités, filtrer le contenu, créer un compte, se connecter, gérer son profil, enregistrer des articles, commenter, s'abonner et discuter avec un assistant intelligent.",
            "Body",
            s,
        )
    )
    story.append(
        p(
            "La méthode SCRUM nous a permis d'organiser le travail en sprints. Le Sprint 0 a assuré les fonctionnalités de base, telles que l'inscription, la connexion, la consultation et le filtrage des actualités. Le Sprint 1 a enrichi la plateforme avec les fonctionnalités liées au profil, aux favoris, aux commentaires, à l'abonnement et au chatbot.",
            "Body",
            s,
        )
    )
    story.append(
        p(
            "Sur le plan technique, le projet repose sur une architecture web moderne composée d'un frontend Angular, d'un backend FastAPI, d'une base de données MySQL, d'une API externe d'actualités et d'un service IA local basé sur Ollama.",
            "Body",
            s,
        )
    )
    story.append(p("Perspectives", "SubTitle", s))
    story.extend(
        bullet(
            [
                "Intégrer une passerelle de paiement réelle pour l'abonnement premium.",
                "Améliorer la recommandation des actualités selon le comportement utilisateur.",
                "Ajouter des notifications pour les nouvelles actualités et les commentaires.",
                "Mettre en place des tests automatisés frontend et backend.",
                "Renforcer la modération des commentaires et des espaces live.",
            ],
            s,
        )
    )
    doc = SimpleDocTemplate(
        str(APPENDIX_PDF),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.4 * cm,
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def merge_pdfs() -> None:
    writer = pypdf.PdfWriter()
    for pdf in [ORIGINAL_COPY, APPENDIX_PDF]:
        reader = pypdf.PdfReader(str(pdf))
        for page in reader.pages:
            writer.add_page(page)
    with FINAL_PDF.open("wb") as output:
        writer.write(output)


def main() -> None:
    ensure_dirs()
    copy_original()
    write_overleaf_source()
    make_appendix_pdf()
    merge_pdfs()
    print(TEX_PATH)
    print(FINAL_PDF)


if __name__ == "__main__":
    main()
