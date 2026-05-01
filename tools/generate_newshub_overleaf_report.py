from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from xml.sax.saxutils import escape

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
REPORT_DIR = ROOT / "reports" / "overleaf_newshub"
TEX_PATH = REPORT_DIR / "main.tex"
PDF_PATH = REPORT_DIR / "newshub_rapport_overleaf.pdf"

PAGE_WIDTH, _PAGE_HEIGHT = A4


def ensure_dirs() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Cover",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Chapter",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=6,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
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
            textColor=colors.HexColor("#111827"),
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
            textColor=colors.HexColor("#111827"),
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8.8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#475569"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.2,
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
            fontSize=8.2,
            leading=9.8,
            textColor=colors.HexColor("#111827"),
            alignment=TA_LEFT,
        )
    )
    return styles


def paragraph(text: str, style: str, styles):
    return Paragraph(text, styles[style])


def bullet(items: list[str], styles):
    return [paragraph(f"- {escape(item)}", "BulletLine", styles) for item in items]


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.setFont("Helvetica", 8.5)
    canvas.drawString(doc.leftMargin, 0.72 * cm, "NewsHub - Rapport Overleaf")
    num = str(doc.page)
    canvas.drawString(PAGE_WIDTH - doc.rightMargin - stringWidth(num, "Helvetica", 8.5), 0.72 * cm, num)
    canvas.restoreState()


def make_breakable(text: str) -> str:
    safe = escape(text)
    for token in ["/", ".", "_", "-", ":", "(", ")", ","]:
        safe = safe.replace(token, f"{token}<wbr/>")
    return safe


def hcell(text: str, styles):
    return Paragraph(escape(text), styles["TableHeader"])


def ccell(text: str, styles):
    return Paragraph(make_breakable(text), styles["TableCell"])


def table(headers: list[str], rows: list[list[str]], widths: list[float], styles, color="#1f2937"):
    data = [[hcell(item, styles) for item in headers]]
    data.extend([[ccell(item, styles) for item in row] for row in rows])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(color)),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def use_case_table(title: str, actor: str, pre: str, post: str, scenario: list[str], exception: str, styles):
    rows = [
        ["Cas d'utilisation", title],
        ["Acteur", actor],
        ["Pré-condition", pre],
        ["Post-condition", post],
        ["Description du scénario principal", "<br/>".join(f"{i + 1}. {escape(s)}" for i, s in enumerate(scenario))],
        ["Exception", exception],
    ]
    data = [
        [Paragraph(f"<b>{escape(left)}</b>", styles["TableCell"]), Paragraph(right, styles["TableCell"])]
        for left, right in rows
    ]
    t = Table(data, colWidths=[4.2 * cm, 11.9 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e0f2fe")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def flow_diagram(title: str, steps: list[str]) -> Drawing:
    d = Drawing(520, 130)
    d.add(String(12, 112, title, fontName="Helvetica-Bold", fontSize=11, fillColor=colors.HexColor("#111827")))
    x = 18
    y = 43
    w = 88
    h = 46
    gap = 12
    for i, step in enumerate(steps):
        d.add(Rect(x, y, w, h, rx=6, ry=6, fillColor=colors.HexColor("#eff6ff"), strokeColor=colors.HexColor("#2563eb"), strokeWidth=0.9))
        d.add(String(x + 8, y + 28, f"Etape {i + 1}", fontName="Helvetica-Bold", fontSize=8.5, fillColor=colors.HexColor("#1e3a8a")))
        for j, line in enumerate(step.split("\n")):
            d.add(String(x + 8, y + 16 - j * 9, line, fontName="Helvetica", fontSize=7.2, fillColor=colors.HexColor("#334155")))
        if i < len(steps) - 1:
            d.add(Line(x + w, y + h / 2, x + w + gap, y + h / 2, strokeColor=colors.HexColor("#2563eb"), strokeWidth=1.1))
        x += w + gap
    return d


def deployment_diagram() -> Drawing:
    d = Drawing(520, 180)
    d.add(String(12, 160, "Diagramme de déploiement simplifié", fontName="Helvetica-Bold", fontSize=11, fillColor=colors.HexColor("#111827")))
    boxes = [
        (20, 92, 105, 48, "Navigateur", ["Angular", "Interface web"]),
        (157, 92, 105, 48, "Serveur API", ["FastAPI", "JWT / REST"]),
        (294, 92, 82, 48, "MySQL", ["Données", "persistantes"]),
        (414, 118, 82, 38, "NewsData", ["API externe"]),
        (414, 58, 82, 38, "Ollama", ["Assistant IA"]),
        (157, 20, 219, 38, "Temps réel", ["WebSocket pour chat et WebRTC pour vidéo live"]),
    ]
    for x, y, w, h, title, lines in boxes:
        d.add(Rect(x, y, w, h, rx=7, ry=7, fillColor=colors.HexColor("#f8fafc"), strokeColor=colors.HexColor("#475569"), strokeWidth=0.9))
        d.add(String(x + 8, y + h - 16, title, fontName="Helvetica-Bold", fontSize=9, fillColor=colors.HexColor("#111827")))
        for j, line in enumerate(lines):
            d.add(String(x + 8, y + h - 29 - j * 9, line, fontName="Helvetica", fontSize=7.2, fillColor=colors.HexColor("#475569")))
    for x1, y1, x2, y2 in [(125, 116, 157, 116), (262, 116, 294, 116), (262, 116, 414, 137), (262, 101, 414, 77), (210, 92, 240, 58)]:
        d.add(Line(x1, y1, x2, y2, strokeColor=colors.HexColor("#2563eb"), strokeWidth=1.1))
    return d


def build_story(styles):
    story = []

    story.append(Spacer(1, 1.1 * cm))
    for line in [
        "République Tunisienne",
        "Ministère de l'Enseignement Supérieur et de la Recherche Scientifique",
        "Université de Carthage",
        "Institut Supérieur des Technologies de l'Information et de la Communication",
    ]:
        story.append(paragraph(line, "Cover", styles))
    story.append(Spacer(1, 1.1 * cm))
    story.append(paragraph("RAPPORT DE PROJET FÉDÉRÉ", "CoverTitle", styles))
    story.append(paragraph("Présenté en vue de l'obtention de la", "Cover", styles))
    story.append(paragraph("LICENCE EN SCIENCES DE L'INFORMATIQUE", "Cover", styles))
    story.append(paragraph("Parcours : Génie Logiciel et Systèmes d'Information", "Cover", styles))
    story.append(Spacer(1, 0.7 * cm))
    story.append(paragraph("Plateforme Web de News Personnalisées avec Chatbot IA : NewsHub", "CoverTitle", styles))
    story.append(Spacer(1, 0.5 * cm))
    story.append(paragraph("Yahya Rejeb, Aziz Ben Slimen, Rayen Ben Yahmed", "Cover", styles))
    story.append(Spacer(1, 1.0 * cm))
    story.append(paragraph("Année Universitaire 2025-2026", "Cover", styles))
    story.append(PageBreak())

    story.append(paragraph("Table des matières", "Chapter", styles))
    story.extend(
        bullet(
            [
                "Introduction Générale",
                "Chapitre 1 : Spécification des besoins",
                "Chapitre 2 : Sprint 0",
                "Chapitre 3 : Sprint 1",
                "Conclusion générale",
            ],
            styles,
        )
    )
    story.append(PageBreak())

    story.append(paragraph("Introduction Générale", "Chapter", styles))
    for text in [
        "Avec la croissance rapide des sources d'information numériques, les utilisateurs sont confrontés à une quantité massive d'actualités publiées chaque jour. Cette abondance d'informations rend difficile l'accès rapide à un contenu pertinent, fiable et adapté aux préférences individuelles.",
        "Les plateformes traditionnelles d'actualités proposent généralement un contenu générique, identique pour tous les utilisateurs, sans prise en compte précise de leurs intérêts spécifiques. De leur côté, les réseaux sociaux offrent une certaine personnalisation, mais leur objectif principal n'est pas toujours la diffusion structurée d'informations fiables issues de sources vérifiées.",
        "Dans ce contexte s'inscrit notre projet fédéré, dont l'objectif est le développement de NewsHub, une plateforme web d'actualités intelligente et personnalisée, combinant la structure des plateformes de news avec des mécanismes dynamiques et interactifs.",
        "Pour modéliser ce projet, nous avons suivi une méthodologie de conception orientée objet, itérative et incrémentale basée sur SCRUM. Le rapport suit l'architecture proposée dans le document exemple : spécification des besoins, étude des sprints, raffinement, conception, réalisation et conclusion.",
    ]:
        story.append(paragraph(text, "Body", styles))
    story.append(PageBreak())

    story.append(paragraph("Chapitre 1 : Spécification des besoins", "Chapter", styles))
    story.append(paragraph("1. Introduction", "Section", styles))
    story.append(paragraph("L'analyse des besoins est essentielle pour le succès d'un système. Elle consiste à identifier les attentes de l'utilisateur pour une nouvelle application en cours de création. Ces attentes doivent être définies de manière approfondie afin de bien comprendre les besoins du client.", "Body", styles))
    story.append(paragraph("Ce chapitre contient l'identification des exigences fonctionnelles et non fonctionnelles, ainsi que la spécification des acteurs. Il présente également le diagramme global de cas d'utilisation et le backlog du produit afin de mieux comprendre les différentes parties du projet.", "Body", styles))
    story.append(paragraph("2. Contexte du système", "Section", styles))
    story.append(paragraph("Le système proposé est une plateforme web dédiée à la consultation d'actualités personnalisées. Il exploite une API externe d'actualités afin de récupérer des articles provenant de différentes sources d'information. L'objectif principal est de permettre aux utilisateurs d'accéder à un fil d'actualité adapté à leurs centres d'intérêt, tout en offrant des fonctionnalités interactives telles que la notation, l'enregistrement d'articles, les commentaires, la gestion du profil, l'abonnement premium et le chatbot.", "Body", styles))
    story.append(paragraph("3. Identification des besoins fonctionnels", "Section", styles))
    story.extend(
        bullet(
            [
                "Créer un compte.",
                "Se connecter.",
                "Consulter le fil d'actualité.",
                "Filtrer les actualités.",
                "Enregistrer une actualité.",
                "Commenter une actualité.",
                "Gérer le profil.",
                "S'abonner.",
                "Discuter avec le chatbot.",
            ],
            styles,
        )
    )
    story.append(paragraph("4. Identification des besoins non fonctionnels", "Section", styles))
    story.extend(
        bullet(
            [
                "Ergonomie : interface intuitive et responsive.",
                "Performance : chargement rapide et réutilisation du cache local.",
                "Sécurité : authentification sécurisée avec hachage des mots de passe et gestion des rôles.",
                "Disponibilité : système accessible de manière continue.",
                "Extensibilité : ajout futur de nouvelles fonctionnalités sans modification majeure.",
                "Fiabilité : traitement correct des données issues de l'API externe.",
            ],
            styles,
        )
    )
    story.append(paragraph("5. Identification des acteurs", "Section", styles))
    story.append(
        table(
            ["Acteur", "Rôle"],
            [
                ["Visiteur", "Créer un compte, se connecter, consulter et filtrer les actualités."],
                ["Utilisateur", "Gérer son profil, commenter une actualité, enregistrer une actualité et s'abonner."],
                ["Utilisateur Premium", "Discuter avec le chatbot IA et accéder aux services premium."],
                ["Éditeur", "Créer et gérer des événements live lorsque le rôle est activé."],
            ],
            [4.3 * cm, 11.8 * cm],
            styles,
        )
    )
    story.append(paragraph("6. Diagramme de cas d'utilisation globale", "Section", styles))
    story.append(flow_diagram("Diagramme de cas d'utilisation global", ["Visiteur\ncompte / login", "Utilisateur\nprofil / favoris", "Premium\nchatbot IA", "Éditeur\nlive", "NewsHub\nservices web"]))
    story.append(paragraph("Figure 1 : Diagramme de cas d'utilisation global simplifié.", "Caption", styles))
    story.append(paragraph("7. Backlog de produit", "Section", styles))
    story.append(
        table(
            ["ID", "User Story", "Priorité"],
            [
                ["US1", "En tant que visiteur, je veux créer un compte afin d'accéder à la plateforme.", "1"],
                ["US2", "En tant que visiteur, je veux me connecter afin d'accéder à mon espace personnel.", "1"],
                ["US3", "En tant que visiteur, je veux consulter les actualités afin de rester informé.", "1"],
                ["US4", "En tant que visiteur, je veux filtrer les actualités afin de personnaliser mon fil.", "1"],
                ["US5", "En tant qu'utilisateur, je veux commenter une actualité afin d'exprimer mon opinion.", "2"],
                ["US6", "En tant qu'utilisateur, je veux enregistrer une actualité à mes favoris.", "2"],
                ["US7", "En tant qu'utilisateur, je veux gérer mon profil.", "2"],
                ["US8", "En tant qu'utilisateur, je veux souscrire à un abonnement afin de devenir premium.", "2"],
                ["US9", "En tant qu'utilisateur premium, je veux discuter avec le chatbot.", "2"],
            ],
            [1.3 * cm, 12.7 * cm, 2.1 * cm],
            styles,
        )
    )
    story.append(paragraph("8. Environnement de travail", "Section", styles))
    story.append(paragraph("8.1 Méthodologie de conception", "Section", styles))
    story.append(paragraph("La méthodologie adoptée est SCRUM, organisée en sprints. Chaque sprint contient une phase d'identification du backlog, une phase de raffinement, une phase de conception et une phase de réalisation.", "Body", styles))
    story.append(paragraph("8.2 Environnement logiciel", "Section", styles))
    story.append(
        table(
            ["Outil", "Utilisation"],
            [
                ["Angular", "Développement du frontend et des interfaces web."],
                ["FastAPI", "Développement du backend et des API."],
                ["MySQL", "Stockage des utilisateurs, favoris, commentaires et événements."],
                ["Newsdata.io", "Récupération dynamique des actualités."],
                ["Ollama / qwen3:14b", "Assistant IA local utilisé par le chatbot."],
                ["GitHub", "Gestion de version et collaboration."],
            ],
            [4.2 * cm, 11.9 * cm],
            styles,
        )
    )
    story.append(paragraph("9. Conclusion", "Section", styles))
    story.append(paragraph("Dans ce chapitre, nous avons identifié les besoins fonctionnels et non fonctionnels, les acteurs principaux, le diagramme global de cas d'utilisation et le backlog du produit. Dans le chapitre suivant, nous élaborerons le premier sprint.", "Body", styles))
    story.append(PageBreak())

    story.append(paragraph("Chapitre 2 : Sprint 0", "Chapter", styles))
    story.append(paragraph("1. Introduction", "Section", styles))
    story.append(paragraph("Dans ce chapitre, nous présentons le premier sprint du projet qui permet de détailler les cas d'utilisation de priorité 1. L'étude de ce sprint comprend le raffinement, la conception et la réalisation.", "Body", styles))
    story.append(paragraph("2. Identification de Backlog de Sprint 0", "Section", styles))
    story.append(
        table(
            ["ID", "User Story", "Priorité"],
            [
                ["US1", "Créer un compte.", "1"],
                ["US2", "Se connecter.", "1"],
                ["US3", "Consulter le fil d'actualité.", "1"],
                ["US4", "Filtrer les actualités.", "1"],
            ],
            [1.3 * cm, 12.7 * cm, 2.1 * cm],
            styles,
        )
    )
    story.append(paragraph("3. Raffinement de Sprint 0", "Section", styles))
    story.append(paragraph("3.1 Raffinement du cas d'utilisation « créer compte »", "Section", styles))
    story.append(use_case_table("Créer compte", "Visiteur", "Système en marche.", "Compte créé avec succès et redirection vers la connexion.", ["Accès à la page d'inscription.", "Saisie des informations.", "Choix des centres d'intérêt.", "Validation du formulaire.", "Création du compte."], "Email déjà utilisé ou données invalides.", styles))
    story.append(paragraph("3.2 Raffinement du cas d'utilisation « se connecter »", "Section", styles))
    story.append(use_case_table("Se connecter", "Visiteur", "Compte existant.", "Utilisateur authentifié et session ouverte.", ["Accès à la page de connexion.", "Saisie de l'email et du mot de passe.", "Vérification des identifiants.", "Création d'un jeton JWT.", "Redirection vers l'accueil."], "Identifiants invalides.", styles))
    story.append(paragraph("3.3 Raffinement du cas d'utilisation « consulter fil d'actualité »", "Section", styles))
    story.append(use_case_table("Consulter fil d'actualité", "Visiteur, Utilisateur", "Système actif.", "Affichage des actualités personnalisées.", ["Accès à l'accueil.", "Récupération des actualités.", "Classement et déduplication.", "Affichage du fil."], "API externe indisponible ou aucun résultat.", styles))
    story.append(paragraph("3.4 Raffinement du cas d'utilisation « filtrer actualité »", "Section", styles))
    story.append(use_case_table("Filtrer actualité", "Visiteur, Utilisateur", "Fil d'actualité chargé.", "Affichage des actualités filtrées.", ["Choix d'une catégorie ou d'un filtre.", "Application du filtre.", "Mise à jour de l'affichage."], "Aucun article correspondant aux filtres.", styles))
    story.append(paragraph("4. Conception de Sprint 0", "Section", styles))
    story.append(flow_diagram("Conception du Sprint 0", ["Créer\ncompte", "Se\nconnecter", "Consulter\nactualités", "Filtrer\nactualité", "Afficher\nrésultat"]))
    story.append(paragraph("Figure 2 : Diagramme de fonctionnement du Sprint 0.", "Caption", styles))
    story.append(paragraph("5. Diagramme de déploiement", "Section", styles))
    story.append(deployment_diagram())
    story.append(paragraph("Figure 3 : Diagramme de déploiement du système NewsHub.", "Caption", styles))
    story.append(paragraph("6. Réalisation de Sprint 0", "Section", styles))
    story.append(paragraph("La réalisation du Sprint 0 a permis de mettre en place les premières interfaces : page d'accueil, formulaire d'inscription, formulaire de connexion, affichage du fil d'actualité et composant de filtrage. Ces interfaces constituent la base fonctionnelle de la plateforme.", "Body", styles))
    story.append(paragraph("7. Conclusion", "Section", styles))
    story.append(paragraph("Ce sprint a permis de livrer le socle de NewsHub. Le chapitre suivant présente les fonctionnalités liées à l'espace utilisateur, aux favoris, aux commentaires, à l'abonnement et au chatbot.", "Body", styles))
    story.append(PageBreak())

    story.append(paragraph("Chapitre 3 : Sprint 1", "Chapter", styles))
    story.append(paragraph("1. Introduction", "Section", styles))
    story.append(paragraph("Dans ce chapitre, nous présentons le deuxième sprint du projet. Il permet de détailler les cas d'utilisation de priorité 2 : gérer profil, commenter actualité, enregistrer actualité, s'abonner et discuter avec le chatbot.", "Body", styles))
    story.append(paragraph("2. Identification de Backlog de Sprint 1", "Section", styles))
    story.append(
        table(
            ["ID", "User Story", "Priorité"],
            [
                ["US5", "Commenter une actualité.", "2"],
                ["US6", "Enregistrer une actualité.", "2"],
                ["US7", "Gérer profil.", "2"],
                ["US8", "S'abonner.", "2"],
                ["US9", "Discuter avec le chatbot.", "2"],
            ],
            [1.3 * cm, 12.7 * cm, 2.1 * cm],
            styles,
        )
    )
    story.append(paragraph("3. Raffinement de Sprint 1", "Section", styles))
    story.append(paragraph("3.1 Raffinement du cas d'utilisation « gérer profil »", "Section", styles))
    story.append(use_case_table("Gérer profil", "Utilisateur, Utilisateur Premium", "L'utilisateur est authentifié.", "Les informations du profil sont mises à jour.", ["Accès à la page profil.", "Affichage des informations actuelles.", "Modification des champs souhaités.", "Validation des données.", "Enregistrement dans la base."], "Champs invalides, email déjà utilisé ou mot de passe incorrect.", styles))
    story.append(paragraph("3.2 Raffinement du cas d'utilisation « enregistrer actualité »", "Section", styles))
    story.append(use_case_table("Enregistrer actualité", "Utilisateur", "L'utilisateur est authentifié.", "L'article est ajouté aux favoris.", ["Ouverture du détail de l'article.", "Clic sur enregistrer.", "Création ou mise à jour de l'article en base.", "Ajout aux favoris de l'utilisateur."], "Article sans URL ou utilisateur non connecté.", styles))
    story.append(paragraph("3.3 Raffinement du cas d'utilisation « commenter actualité »", "Section", styles))
    story.append(use_case_table("Commenter actualité", "Utilisateur", "L'utilisateur est authentifié.", "Le commentaire est enregistré et affiché.", ["Saisie du commentaire.", "Validation du texte.", "Enregistrement du commentaire.", "Rafraîchissement de la liste."], "Commentaire vide ou erreur de base de données.", styles))
    story.append(paragraph("3.4 Raffinement du cas d'utilisation « s'abonner »", "Section", styles))
    story.append(use_case_table("S'abonner", "Utilisateur", "L'utilisateur est authentifié.", "Le compte devient premium.", ["Accès à la page des abonnements.", "Choix d'une offre.", "Saisie des informations de paiement simulé.", "Validation.", "Activation des privilèges premium."], "Informations invalides ou transaction simulée échouée.", styles))
    story.append(paragraph("3.5 Raffinement du cas d'utilisation « discuter avec le chatbot »", "Section", styles))
    story.append(use_case_table("Discuter avec le chatbot", "Utilisateur Premium", "L'utilisateur est premium et le chatbot est disponible.", "La discussion est affichée dans l'interface.", ["Ouverture d'un article.", "Affichage du panneau chatbot.", "Envoi d'une question.", "Analyse de l'article par le modèle IA.", "Affichage de la réponse."], "Utilisateur non premium, texte vide ou Ollama indisponible.", styles))
    story.append(paragraph("4. Conception de Sprint 1", "Section", styles))
    story.append(flow_diagram("Conception du Sprint 1", ["Profil\nutilisateur", "Favoris\narticles", "Commentaires\narticle", "Premium\nabonnement", "Chatbot\nIA"]))
    story.append(paragraph("Figure 4 : Diagramme de fonctionnement du Sprint 1.", "Caption", styles))
    story.append(paragraph("5. Réalisation de Sprint 1", "Section", styles))
    story.append(paragraph("La réalisation du Sprint 1 a permis d'ajouter une page profil complète, la gestion des favoris, le système de commentaires, la simulation d'abonnement premium et l'assistant IA accessible aux utilisateurs premium. Le backend assure la persistance dans MySQL et la sécurité des accès grâce au JWT.", "Body", styles))
    story.append(paragraph("6. Conclusion", "Section", styles))
    story.append(paragraph("Ce sprint complète les fonctionnalités principales de NewsHub. La plateforme devient interactive et personnalisée. Elle permet à l'utilisateur de construire son espace, d'interagir avec les articles et d'accéder à des services premium.", "Body", styles))
    story.append(PageBreak())

    story.append(paragraph("Conclusion générale", "Chapter", styles))
    story.append(paragraph("Dans ce projet, nous avons conçu et réalisé NewsHub, une plateforme web d'actualités personnalisées avec chatbot IA. Le système répond aux besoins principaux définis au début du projet : consulter des actualités, filtrer le contenu, gérer un compte utilisateur, enregistrer des articles, commenter, s'abonner et interagir avec un assistant intelligent.", "Body", styles))
    story.append(paragraph("La méthode SCRUM nous a permis d'organiser le travail en sprints clairs. Le Sprint 0 a permis de mettre en place le socle de l'application, tandis que le Sprint 1 a ajouté les fonctionnalités utilisateur et premium. L'architecture technique repose sur Angular, FastAPI, MySQL, Newsdata.io, JWT et Ollama.", "Body", styles))
    story.append(paragraph("Comme perspectives, nous pouvons proposer l'ajout d'un paiement réel, l'amélioration du système de recommandation, l'intégration de notifications, la mise en place de tests automatisés et l'amélioration de la modération des commentaires et des lives.", "Body", styles))
    story.append(Spacer(1, 0.3 * cm))
    story.append(paragraph("Fin du rapport.", "Small", styles))
    return story


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def write_latex_source() -> None:
    content = r"""
\documentclass[12pt,a4paper]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[french]{babel}
\usepackage{geometry}
\usepackage{array}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{float}
\usepackage{hyperref}
\usepackage{fancyhdr}
\usepackage{enumitem}

\geometry{left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.5cm}
\setlist[itemize]{label=--}
\pagestyle{fancy}
\fancyhf{}
\lhead{NewsHub}
\rhead{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

\newcommand{\simplebox}[2]{
\begin{center}
\begin{tikzpicture}
\node[draw, rounded corners, fill=blue!5, text width=0.85\textwidth, inner sep=8pt] {
\textbf{#1}\\[3pt] #2
};
\end{tikzpicture}
\end{center}
}

\begin{document}

\begin{titlepage}
\centering
République Tunisienne\\
Ministère de l'Enseignement Supérieur et de la Recherche Scientifique\\
Université de Carthage\\
Institut Supérieur des Technologies de l'Information et de la Communication\\[2cm]
{\Large \textbf{RAPPORT DE PROJET FÉDÉRÉ}}\\[1cm]
Présenté en vue de l'obtention de la\\
\textbf{LICENCE EN SCIENCES DE L'INFORMATIQUE}\\
Parcours : Génie Logiciel et Systèmes d'Information\\[1.5cm]
{\Large \textbf{Plateforme Web de News Personnalisées avec Chatbot IA : NewsHub}}\\[1.5cm]
Yahya Rejeb, Aziz Ben Slimen, Rayen Ben Yahmed\\[1.5cm]
Année Universitaire 2025--2026
\end{titlepage}

\tableofcontents
\clearpage

\chapter*{Introduction Générale}
\addcontentsline{toc}{chapter}{Introduction Générale}
Avec la croissance rapide des sources d'information numériques, les utilisateurs sont confrontés à une quantité massive d'actualités publiées chaque jour. Cette abondance d'informations rend difficile l'accès rapide à un contenu pertinent, fiable et adapté aux préférences individuelles.

Les plateformes traditionnelles d'actualités proposent généralement un contenu générique, identique pour tous les utilisateurs, sans prise en compte précise de leurs intérêts spécifiques. De leur côté, les réseaux sociaux offrent une certaine personnalisation, mais leur objectif principal n'est pas toujours la diffusion structurée d'informations fiables issues de sources vérifiées.

Dans ce contexte s'inscrit notre projet fédéré, dont l'objectif est le développement de NewsHub, une plateforme web d'actualités intelligente et personnalisée, combinant la structure des plateformes de news avec des mécanismes dynamiques et interactifs.

Pour modéliser ce projet, nous avons suivi une méthodologie de conception orientée objet, itérative et incrémentale basée sur SCRUM. Le rapport suit l'architecture proposée dans le document exemple : spécification des besoins, étude des sprints, raffinement, conception, réalisation et conclusion.

\chapter{Spécification des besoins}
\section{Introduction}
L'analyse des besoins est essentielle pour le succès d'un système. Elle consiste à identifier les attentes de l'utilisateur pour une nouvelle application en cours de création.

\section{Contexte du système}
Le système proposé est une plateforme web dédiée à la consultation d'actualités personnalisées. Il exploite une API externe d'actualités afin de récupérer des articles provenant de différentes sources d'information.

\section{Identification des besoins fonctionnels}
\begin{itemize}
\item créer un compte ;
\item se connecter ;
\item consulter le fil d'actualité ;
\item filtrer les actualités ;
\item enregistrer une actualité ;
\item commenter une actualité ;
\item gérer le profil ;
\item s'abonner ;
\item discuter avec le chatbot.
\end{itemize}

\section{Identification des besoins non fonctionnels}
\begin{itemize}
\item Ergonomie : interface intuitive et responsive.
\item Performance : chargement rapide et réutilisation du cache local.
\item Sécurité : authentification sécurisée et gestion des rôles.
\item Extensibilité : ajout futur de nouvelles fonctionnalités.
\item Fiabilité : traitement correct des données issues de l'API externe.
\end{itemize}

\section{Identification des acteurs}
\begin{longtable}{|p{4cm}|p{10cm}|}
\hline
\textbf{Acteur} & \textbf{Rôle}\\ \hline
Visiteur & Créer un compte, se connecter, consulter et filtrer les actualités.\\ \hline
Utilisateur & Gérer son profil, commenter une actualité, enregistrer une actualité et s'abonner.\\ \hline
Utilisateur Premium & Discuter avec le chatbot IA et accéder aux services premium.\\ \hline
\end{longtable}

\section{Diagramme de cas d'utilisation globale}
\simplebox{Diagramme de cas d'utilisation global}{Visiteur, Utilisateur et Utilisateur Premium interagissent avec NewsHub pour accéder aux fonctionnalités principales de la plateforme.}

\section{Backlog de produit}
\begin{longtable}{|p{1.5cm}|p{11cm}|p{2cm}|}
\hline
\textbf{ID} & \textbf{User Story} & \textbf{Priorité}\\ \hline
US1 & En tant que visiteur, je veux créer un compte afin d'accéder à la plateforme. & 1\\ \hline
US2 & En tant que visiteur, je veux me connecter afin d'accéder à mon espace personnel. & 1\\ \hline
US3 & En tant que visiteur, je veux consulter les actualités afin de rester informé. & 1\\ \hline
US4 & En tant que visiteur, je veux filtrer les actualités afin de personnaliser mon fil. & 1\\ \hline
US5 & En tant qu'utilisateur, je veux commenter une actualité. & 2\\ \hline
US6 & En tant qu'utilisateur, je veux enregistrer une actualité. & 2\\ \hline
US7 & En tant qu'utilisateur, je veux gérer mon profil. & 2\\ \hline
US8 & En tant qu'utilisateur, je veux souscrire à un abonnement. & 2\\ \hline
US9 & En tant qu'utilisateur premium, je veux discuter avec le chatbot. & 2\\ \hline
\end{longtable}

\section{Environnement de travail}
La méthodologie adoptée est SCRUM. L'environnement logiciel utilisé comprend Angular, FastAPI, MySQL, Newsdata.io, GitHub et Ollama avec le modèle qwen3:14b.

\section{Conclusion}
Dans ce chapitre, nous avons identifié les besoins fonctionnels et non fonctionnels, les acteurs principaux, le diagramme global de cas d'utilisation et le backlog du produit.

\chapter{Sprint 0}
\section{Introduction}
Dans ce chapitre, nous présentons le premier sprint du projet qui permet de détailler les cas d'utilisation de priorité 1.

\section{Identification de Backlog de Sprint 0}
\begin{longtable}{|p{1.5cm}|p{11cm}|p{2cm}|}
\hline
\textbf{ID} & \textbf{User Story} & \textbf{Priorité}\\ \hline
US1 & Créer un compte. & 1\\ \hline
US2 & Se connecter. & 1\\ \hline
US3 & Consulter le fil d'actualité. & 1\\ \hline
US4 & Filtrer les actualités. & 1\\ \hline
\end{longtable}

\section{Raffinement de Sprint 0}
\subsection{Raffinement du cas d'utilisation « créer compte »}
\simplebox{Créer compte}{Le visiteur saisit ses informations, choisit ses centres d'intérêt puis valide la création du compte.}

\subsection{Raffinement du cas d'utilisation « se connecter »}
\simplebox{Se connecter}{L'utilisateur saisit son email et son mot de passe. Le système vérifie les identifiants et ouvre la session.}

\subsection{Raffinement du cas d'utilisation « consulter fil d'actualité »}
\simplebox{Consulter fil d'actualité}{Le système récupère les articles depuis l'API externe et affiche le fil d'actualité.}

\subsection{Raffinement du cas d'utilisation « filtrer actualité »}
\simplebox{Filtrer actualité}{L'utilisateur choisit des filtres et le système affiche les actualités correspondantes.}

\section{Conception de Sprint 0}
\simplebox{Conception du Sprint 0}{Créer compte -- Se connecter -- Consulter actualités -- Filtrer actualité -- Afficher résultat.}

\section{Diagramme de déploiement}
\simplebox{Déploiement}{Navigateur Angular, serveur FastAPI, base MySQL, API NewsData et service Ollama.}

\section{Réalisation de Sprint 0}
La réalisation du Sprint 0 a permis de mettre en place les premières interfaces : page d'accueil, formulaire d'inscription, formulaire de connexion, affichage du fil d'actualité et composant de filtrage.

\section{Conclusion}
Ce sprint a permis de livrer le socle de NewsHub.

\chapter{Sprint 1}
\section{Introduction}
Dans ce chapitre, nous présentons le deuxième sprint du projet.

\section{Identification de Backlog de Sprint 1}
\begin{longtable}{|p{1.5cm}|p{11cm}|p{2cm}|}
\hline
\textbf{ID} & \textbf{User Story} & \textbf{Priorité}\\ \hline
US5 & Commenter une actualité. & 2\\ \hline
US6 & Enregistrer une actualité. & 2\\ \hline
US7 & Gérer profil. & 2\\ \hline
US8 & S'abonner. & 2\\ \hline
US9 & Discuter avec le chatbot. & 2\\ \hline
\end{longtable}

\section{Raffinement de Sprint 1}
\subsection{Gérer profil}
\simplebox{Gérer profil}{L'utilisateur consulte et modifie les informations de son profil.}
\subsection{Enregistrer actualité}
\simplebox{Enregistrer actualité}{L'utilisateur ajoute une actualité à ses favoris.}
\subsection{Commenter actualité}
\simplebox{Commenter actualité}{L'utilisateur ajoute un commentaire sur une actualité.}
\subsection{S'abonner}
\simplebox{S'abonner}{L'utilisateur choisit une offre et active son statut premium.}
\subsection{Discuter avec le chatbot}
\simplebox{Discuter avec le chatbot}{L'utilisateur premium pose une question au chatbot à propos d'un article.}

\section{Conception de Sprint 1}
\simplebox{Conception du Sprint 1}{Profil utilisateur -- Favoris -- Commentaires -- Abonnement -- Chatbot IA.}

\section{Réalisation de Sprint 1}
La réalisation du Sprint 1 a permis d'ajouter une page profil complète, la gestion des favoris, le système de commentaires, la simulation d'abonnement premium et l'assistant IA accessible aux utilisateurs premium.

\section{Conclusion}
Ce sprint complète les fonctionnalités principales de NewsHub.

\chapter*{Conclusion générale}
\addcontentsline{toc}{chapter}{Conclusion générale}
Dans ce projet, nous avons conçu et réalisé NewsHub, une plateforme web d'actualités personnalisées avec chatbot IA. Le système répond aux besoins principaux définis au début du projet : consulter des actualités, filtrer le contenu, gérer un compte utilisateur, enregistrer des articles, commenter, s'abonner et interagir avec un assistant intelligent.

Comme perspectives, nous pouvons proposer l'ajout d'un paiement réel, l'amélioration du système de recommandation, l'intégration de notifications, la mise en place de tests automatisés et l'amélioration de la modération.

\end{document}
"""
    TEX_PATH.write_text(dedent(content).strip() + "\n", encoding="utf-8")


def generate_pdf() -> Path:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.4 * cm,
        title="Rapport NewsHub Overleaf",
        author="NewsHub",
    )
    doc.build(build_story(styles), onFirstPage=page_number, onLaterPages=page_number)
    return PDF_PATH


def main() -> None:
    ensure_dirs()
    write_latex_source()
    output = generate_pdf()
    print(TEX_PATH)
    print(output)


if __name__ == "__main__":
    main()
