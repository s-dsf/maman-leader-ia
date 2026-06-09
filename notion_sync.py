import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

DB_IDS = {
    "Ebook":          os.getenv("NOTION_DB_EBOOKS"),
    "Contenus Social": os.getenv("NOTION_DB_SOCIAL"),
    "Article Blog":   os.getenv("NOTION_DB_BLOG"),
    "Audit Site":     os.getenv("NOTION_DB_AUDIT"),
    "Visuels":        os.getenv("NOTION_DB_BLOG"),
}

def envoyer_notion(titre, type_mission, contenu, date_str):
    db_id = DB_IDS.get(type_mission)
    if not db_id:
        return False, f"Base Notion introuvable pour : {type_mission}"

    # Notion limite les blocs de texte à 2000 caractères
    # On découpe le contenu en plusieurs blocs
    def decouper(texte, taille=1900):
        return [texte[i:i+taille] for i in range(0, len(texte), taille)]

    blocs_texte = decouper(contenu[:50000])

    children = []
    for bloc in blocs_texte:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": bloc}
                }]
            }
        })

    try:
        notion.pages.create(
            parent={"database_id": db_id},
            properties={
                "Titre": {
                    "title": [{
                        "type": "text",
                        "text": {"content": titre[:100]}
                    }]
                },
                "Type": {
                    "select": {"name": type_mission}
                },
                "Date": {
                    "date": {"start": date_str}
                },
                "Statut": {
                    "select": {"name": "Brouillon"}
                }
            },
            children=children[:100]
        )
        return True, "Livrable envoyé dans Notion"
    except Exception as e:
        return False, str(e)