Pour réussir la compétition Google - Agent Harness on Physical-Engineering's Last Exam sur Kaggle, l'objectif n'est pas d'entraîner un modèle, mais de concevoir l'architecture logicielle (harness.py et serve.py) qui pilote un modèle imposé. Votre harnais doit transformer des dossiers bruts (plans PDF, fichiers CAD/IFC4, tableurs XLSX) en livrables techniques exacts à travers 85 tâches d'ingénierie.

1. Les contraintes techniques de l'évaluation Kaggle

Avant de coder votre harnais, vous devez respecter les règles strictes de l'environnement d'exécution :
• Modèle imposé via proxy. Vous devez configurer model_api dans submission.yaml sur l'un des 8 modèles officiels (google-cloud/<id>). Les clés API externes, serveurs privés et recherches web sont bloqués par le proxy d'évaluation.
• Structure du dépôt GitHub. La racine de votre dépôt doit impérativement contenir submission.yaml, serve.py / harness.py, une licence open source (MIT ou Apache-2.0) et le dossier décompressé artifacts/.
• Livrables de l'étape 1. Votre soumission nécessite un Kaggle Writeup de 2 000 mots maximum incluant 3 graphiques obligatoires : un diagramme d'architecture, une courbe score/coût en tokens et une analyse des échecs sur le jeu de développement.

2. Appliquer le Harness Engineering aux 4 briques clés

Les meilleures approches observées sur le jeu public (29 tâches de développement contenant chacune entre 50 et 207 fichiers) reposent sur quatre optimisations concrètes :
• Remplacer le calcul mental par des outils déterministes. Les LLM commettent des erreurs d'unités ou d'ordres de grandeur sur les calculs physiques. Équipez votre harnais de solveurs Python spécialisés (ex. vérification de poutres sous charges, dimensionnement électrique, perte de charge hydraulique ou calculs géométriques IFC4) que l'agent appelle comme outils.
• Filtrer le contexte avant l'injection. Chaque dossier pèse des dizaines de millions de tokens potentiels. Implémentez une étape d'indexation et de récupération ciblée (targeted retrieval) des plans, nomenclatures et feuilles de calcul pour réduire la facture de tokens tout en évitant la saturation de la mémoire.
• Imposer une boucle de vérification avant soumission. Ne laissez pas l'agent terminer sur une simple boucle ReAct libre. Ajoutez un mécanisme de contrôle déterministe (code-gated audit loop) qui vérifie automatiquement le format des fichiers générés (XLSX, DOCX, IFC4) et le respect des contraintes physiques avant de valider la réponse finale.
• Automatiser l'amélioration avec Harness². Vous pouvez utiliser le framework Google Harness² (cycle Propose → Probe → Compose) sur les 29 tâches publiques pour tester et affiner automatiquement vos prompts système et vos scripts d'outils sans réentraîner le modèle
