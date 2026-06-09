import os
from dotenv import load_dotenv
from crewai import Task, Crew, Process, LLM
from agents import (
    chef_de_projet,
    responsable_marketing,
    redacteur,
    directeur_artistique,
    maquettiste
)

load_dotenv()

claude = LLM(
    model="anthropic/claude-sonnet-4-6",
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

chef_de_projet.llm = claude
responsable_marketing.llm = claude
redacteur.llm = claude
directeur_artistique.llm = claude
maquettiste.llm = claude

def lancer_projet(titre, genre, synopsis_brut, auteur):

    task_marketing = Task(
        description=f"""
        Pour le livre "{titre}" ({genre}) de {auteur}.
        Synopsis de départ : {synopsis_brut}

        Produis :
        1. Analyse de 3 livres comparables sur le marché actuel
        2. Persona du lectorat cible (âge, profil, habitudes de lecture)
        3. Positionnement éditorial en une phrase
        4. 4e de couverture (200 mots maximum)
        5. Argumentaire pour les libraires (5 points clés)
        """,
        agent=responsable_marketing,
        expected_output="Document marketing structuré en 5 sections"
    )

    task_redaction = Task(
        description=f"""
        Pour le livre "{titre}" ({genre}) de {auteur}.
        Synopsis de départ : {synopsis_brut}

        Rédige :
        1. Synopsis court (100 mots) pour catalogues
        2. Synopsis long (400 mots) pour dossier de presse
        3. Biographie auteur (150 mots)
        4. Note d'intention éditoriale (200 mots)
        """,
        agent=redacteur,
        expected_output="Quatre textes éditoriaux finalisés"
    )

    task_da = Task(
        description=f"""
        Sur la base du travail marketing et éditorial,
        pour le livre "{titre}" ({genre}) :

        Définis :
        1. Mood board en mots (5 références visuelles)
        2. Palette de couleurs avec codes hex
        3. Direction typographique
        4. Prompt pour générer la couverture avec Midjourney ou DALL-E
        5. Éléments visuels à éviter
        """,
        agent=directeur_artistique,
        context=[task_marketing, task_redaction],
        expected_output="Brief artistique complet avec prompt de couverture"
    )

    task_maquette = Task(
        description=f"""
        Sur la base de la direction artistique,
        pour le livre "{titre}" ({genre}) :

        Spécifie :
        1. Format du livre recommandé (dimensions en mm)
        2. Grille typographique (marges, gouttière)
        3. Styles de caractères avec taille et interligne
        4. Ordre des pages liminaires
        5. Gabarit d'ouverture de chapitre
        """,
        agent=maquettiste,
        context=[task_da],
        expected_output="Spécifications maquette complètes pour InDesign"
    )

    task_synthese = Task(
        description=f"""
        Compile tout le travail en un dossier éditorial final
        pour le livre "{titre}".

        Structure :
        - Page de garde
        - Synthèse exécutive (1 page)
        - Section Marketing
        - Section Textes éditoriaux
        - Section Direction artistique
        - Section Maquette
        - Points de cohérence à vérifier
        """,
        agent=chef_de_projet,
        context=[task_marketing, task_redaction, task_da, task_maquette],
        expected_output="Dossier éditorial complet et structuré"
    )

    equipe = Crew(
        agents=[
            responsable_marketing,
            redacteur,
            directeur_artistique,
            maquettiste,
            chef_de_projet
        ],
        tasks=[
            task_marketing,
            task_redaction,
            task_da,
            task_maquette,
            task_synthese
        ],
        process=Process.sequential,
        verbose=True
    )

    print("\n Lancement de l'équipe éditoriale...\n")
    resultat = equipe.kickoff()

    nom_fichier = f"dossier_{titre.replace(' ', '_')}.txt"
    with open(nom_fichier, "w", encoding="utf-8") as f:
        f.write(str(resultat))

    print(f"\n Dossier sauvegardé dans : {nom_fichier}")
    return resultat


if __name__ == "__main__":
    lancer_projet(
        titre="Les Jardins de Sel",
        genre="Roman littéraire",
        synopsis_brut="""Une femme de 40 ans retrouve dans le grenier familial
        les lettres de sa grand-mère marocaine. Elle part à Essaouira
        sur ses traces et découvre un secret de famille enfoui depuis 60 ans.""",
        auteur="Marie Lescot"
    )