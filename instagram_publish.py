import os
import time
import requests

GRAPH_URL = "https://graph.instagram.com/v21.0"

def _token():
    return os.getenv("INSTAGRAM_ACCESS_TOKEN")

def _account_id():
    return os.getenv("INSTAGRAM_ACCOUNT_ID")

def _attendre_container(container_id, timeout=60):
    """Attend que le container soit pret (status FINISHED)."""
    url = f"{GRAPH_URL}/{container_id}"
    params = {"fields": "status_code", "access_token": _token()}
    for _ in range(timeout // 3):
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        statut = data.get("status_code")
        if statut == "FINISHED":
            return True
        if statut == "ERROR":
            raise Exception(f"Erreur container {container_id}: {data}")
        time.sleep(3)
    raise Exception(f"Timeout container {container_id}")

def publier_story(image_url, caption=""):
    """Publie une image en story sur Instagram."""
    account_id = _account_id()
    token = _token()

    # 1. Creer le container
    url_creer = f"{GRAPH_URL}/{account_id}/media"
    params_creer = {
        "image_url": image_url,
        "media_type": "STORIES",
        "access_token": token,
    }
    resp = requests.post(url_creer, params=params_creer, timeout=30)
    data = resp.json()
    if "id" not in data:
        return False, f"Erreur creation container: {data}"
    container_id = data["id"]

    # 2. Attendre que le container soit pret
    try:
        _attendre_container(container_id)
    except Exception as e:
        return False, str(e)

    # 3. Publier
    url_publier = f"{GRAPH_URL}/{account_id}/media_publish"
    params_publier = {"creation_id": container_id, "access_token": token}
    resp_pub = requests.post(url_publier, params=params_publier, timeout=30)
    data_pub = resp_pub.json()
    if "id" not in data_pub:
        return False, f"Erreur publication: {data_pub}"

    return True, f"Story publiee (id: {data_pub['id']})"

def publier_carrousel(image_urls, caption=""):
    """Publie un carrousel (2-10 images) sur Instagram."""
    account_id = _account_id()
    token = _token()

    if len(image_urls) < 2:
        return False, "Un carrousel necessite au moins 2 images"
    if len(image_urls) > 10:
        image_urls = image_urls[:10]

    # 1. Creer un container enfant par image
    children_ids = []
    for img_url in image_urls:
        url_creer = f"{GRAPH_URL}/{account_id}/media"
        params_creer = {
            "image_url": img_url,
            "is_carousel_item": "true",
            "access_token": token,
        }
        resp = requests.post(url_creer, params=params_creer, timeout=30)
        data = resp.json()
        if "id" not in data:
            return False, f"Erreur container enfant: {data}"
        children_ids.append(data["id"])

    # 2. Creer le container parent (carrousel)
    url_carrousel = f"{GRAPH_URL}/{account_id}/media"
    params_carrousel = {
        "media_type": "CAROUSEL",
        "caption": caption,
        "children": ",".join(children_ids),
        "access_token": token,
    }
    resp_c = requests.post(url_carrousel, params=params_carrousel, timeout=30)
    data_c = resp_c.json()
    if "id" not in data_c:
        return False, f"Erreur container carrousel: {data_c}"
    container_id = data_c["id"]

    # 3. Attendre que le container soit pret
    try:
        _attendre_container(container_id)
    except Exception as e:
        return False, str(e)

    # 4. Publier
    url_publier = f"{GRAPH_URL}/{account_id}/media_publish"
    params_publier = {"creation_id": container_id, "access_token": token}
    resp_pub = requests.post(url_publier, params=params_publier, timeout=30)
    data_pub = resp_pub.json()
    if "id" not in data_pub:
        return False, f"Erreur publication: {data_pub}"

    return True, f"Carrousel publie (id: {data_pub['id']})"