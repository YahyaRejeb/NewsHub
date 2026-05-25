import re

with open('extracted_pdf.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add to 4.2
addition_4_2 = """
**Gestion des transactions atomiques :**
L'efficacité de la fonction `complete_signup()` dans `backend/main.py` repose sur son utilisation des transactions atomiques. Lors de l'inscription en deux étapes, le backend crée d'abord l'utilisateur (`db.add(new_user)`), puis lie ses centres d'intérêt (`models.UserInterest`). Si une erreur survient à n'importe quel moment de ce processus (par exemple, un doublon détecté par `IntegrityError`), le backend exécute un `db.rollback()`. Cela garantit qu'aucun compte partiel ou corrompu ne sera enregistré en base de données, assurant une intégrité totale des données locales.
"""
content = content.replace("que le backend conserve le dernier mot sur l'unicite de l'email et la creation effective du compte.", 
"que le backend conserve le dernier mot sur l'unicite de l'email et la creation effective du compte.\n\n" + addition_4_2)

# 2. Add to 4.7
addition_4_7 = """
**Optimisation de la fenêtre de contexte et nettoyage des réponses :**
L'assistant IA a été conçu pour rester très rapide malgré son exécution locale. Dans le fichier `backend/simple_chatbot.py`, la fonction `ask_chatbot()` est optimisée pour ne conserver que les 4 derniers échanges de la conversation (`for turn in history[-4:]:`). Cela empêche le modèle de surcharger sa mémoire de contexte. De plus, pour garantir une interface utilisateur propre, la fonction interne `_clean_answer(text)` est exécutée avant de retourner la réponse au frontend. Elle se charge de nettoyer les balises de réflexion cachées (ex: `<think>...</think>`) qui peuvent être générées par certains modèles locaux complexes, assurant ainsi que l'utilisateur final ne voit que la réponse finale.
"""
content = content.replace("convient bien a une application locale ou a un projet de demonstration.", 
"convient bien a une application locale ou a un projet de demonstration.\n\n" + addition_4_7)

# 3. Add to Scenario 3
addition_scenario_3 = """
**Flexibilité du modèle IA via les variables d'environnement :**
Bien que le code utilise actuellement `qwen3:14b` par défaut, l'architecture du chatbot est conçue pour être modulaire. Dans `backend/simple_chatbot.py`, le modèle est instancié dynamiquement via `CHATBOT_MODEL = os.getenv("CHATBOT_MODEL", "qwen3:14b")`. Cela signifie que si l'équipe souhaite respecter à 100 % le brief initial et repasser sur `gemma3:12b`, il suffit de définir `CHATBOT_MODEL=gemma3:12b` dans un fichier `.env` local. Aucune modification du code source backend n'est requise pour effectuer cette transition.
"""
content = content.replace("Le rapport doit donc retenir qwen3:14b comme implementation effective actuelle.",
"Le rapport doit donc retenir qwen3:14b comme implementation effective actuelle.\n\n" + addition_scenario_3)

# 4. Add to 7.5
addition_7_5 = """  - **Sécurisation de la politique CORS pour la production :** Actuellement, dans `backend/main.py`, le middleware de sécurité `CORSMiddleware` est configuré avec `allow_origins=["*"]` (assorti du commentaire "Temporarily allow ALL for debugging"). Bien que parfait pour un environnement de développement local, il sera impératif de restreindre cette politique aux stricts domaines du frontend (ex: `http://localhost:4200` ou le futur domaine en production) pour éviter les failles de type Cross-Origin."""
content = content.replace("Prevoir une vraie pagination ou du lazy loading si le volume d'articles augmente.",
"Prevoir une vraie pagination ou du lazy loading si le volume d'articles augmente.\n" + addition_7_5)

# Clean up page numbers and headers
content = re.sub(r'NewsHub - Rapport global du projet\nPage \d+\n', '', content)

with open('newshub_rapport_global_mis_a_jour.md', 'w', encoding='utf-8') as f:
    f.write(content)
