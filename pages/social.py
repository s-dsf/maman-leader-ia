import streamlit as st
import os, json, datetime, requests, re, calendar, base64
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

st.set_page_config(page_title="Maman & Leader — Social", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

FONT_PATH = "fonts/PlayfairDisplay-VariableFont_wght.ttf"
FOND_BEIGE = "assets/fond_de_page_beige_avec_logo.png"
FOND_TERRA = "assets/fond_de_page_terracota_avec_logo.png"
VISUELS_DIR = Path("visuels_temp")
VISUELS_DIR.mkdir(exist_ok=True)

def charger_prompts():
    with open("prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def charger_image(key):
    chemin = Path(f"avatar_{key}.png")
    if chemin.exists():
        return Image.open(chemin)
    return None

def upload_vers_drive(filepath: str, filename: str = None):
    try:
        from drive_upload import upload_png
        result = upload_png(filepath, filename)
        return result
    except Exception as e:
        st.warning(f"Upload Drive impossible : {str(e)[:100]}")
        return None

def envoyer_airtable(posts):
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        return False, "Cles Airtable manquantes"
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    erreurs = []
    succes = 0
    for i in range(0, len(posts), 10):
        batch = posts[i:i+10]
        records = []
        for post in batch:
            fields = {}
            for key in ["Date","Support","Pilier","Angle","Hook","ContenuPost","Caption","BriefGeneral"]:
                if key in post:
                    fields[key] = str(post[key])
            fields["StatutPublication"] = "Brouillon"
            records.append({"fields": fields})
        try:
            resp = requests.post(url, headers=headers, json={"records": records}, timeout=30)
            if resp.status_code == 200:
                returned = resp.json().get("records", [])
                for post_obj, rec in zip(batch, returned):
                    post_obj["_record_id"] = rec.get("id", "")
                    post_obj["StatutPublication"] = "Brouillon"
                succes += len(batch)
            else:
                erreurs.append(f"Batch {i//10+1}: {resp.status_code} — {resp.text[:150]}")
        except Exception as e:
            erreurs.append(str(e))
    if erreurs:
        return False, f"{succes} posts envoyes. Erreurs : {'; '.join(erreurs)}"
    return True, f"✦ {succes} posts envoyes dans Airtable"

def lire_airtable():
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        return [], "Cles Airtable manquantes"
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {"Authorization": f"Bearer {token}"}
    tous = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            return [], f"Erreur {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        tous.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return tous, None

def mettre_a_jour_airtable(record_id, fields):
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.patch(url, headers=headers, json={"fields": fields}, timeout=30)
    return resp.status_code == 200, resp.text[:200]

def modifier_post_ia(post, demande):
    import anthropic as ant
    client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""Tu es la Redactrice de Maman & Leader.
Ton : sobre, stable, introspectif, non injonctif.
Equilibre : identification + ressource positive + appel a l'action bienveillant.
Jamais uniquement un constat negatif. Toujours une ouverture.

POST ACTUEL :
Support : {post.get('Support','')}
Pilier : {post.get('Pilier','')}
Hook : {post.get('Hook','')}
Contenu : {post.get('ContenuPost','')}
Caption : {post.get('Caption','')}

DEMANDE : {demande}

Reponds UNIQUEMENT avec ce JSON valide :
{{"Hook": "...", "ContenuPost": "...", "Caption": "..."}}
Garde le meme format de ContenuPost.
Termine par une note douce invitant au partage."""
    msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=2000, messages=[{"role": "user", "content": prompt}])
    reponse = msg.content[0].text.strip()
    if "```" in reponse:
        reponse = re.sub(r'```json?\s*', '', reponse)
        reponse = re.sub(r'```', '', reponse)
    start = reponse.find('{')
    end = reponse.rfind('}') + 1
    modifs = json.loads(reponse[start:end])
    if isinstance(modifs.get("ContenuPost"), dict):
        modifs["ContenuPost"] = json.dumps(modifs["ContenuPost"], ensure_ascii=False)
    return modifs

def wrap_text_pillow(texte, font, draw, max_width):
    mots = texte.split()
    lignes = []
    courante = ""
    for mot in mots:
        test = (courante + " " + mot).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            courante = test
        else:
            if courante:
                lignes.append(courante)
            courante = mot
    if courante:
        lignes.append(courante)
    return lignes

def generer_png_story(post):
    hook = str(post.get("Hook", ""))
    contenu = str(post.get("ContenuPost", ""))
    pilier = str(post.get("Pilier", ""))
    try:
        jour = int(str(post.get("Date", "0000-00-00")).split("-")[2])
    except Exception:
        jour = 1
    is_terra = jour % 2 == 0
    fond = FOND_TERRA if is_terra else FOND_BEIGE
    couleur = (251, 248, 246) if is_terra else (74, 56, 51)
    slides = []
    morceaux = re.split(r'Story\s*\d+\s*[:/]?\s*', contenu)
    for morceau in morceaux:
        texte = morceau.strip().replace('\n', ' ')
        if texte:
            slides.append(texte)
    if not slides:
        slides = [hook]
    pngs = []
    for idx, texte in enumerate(slides[:6]):
        img = Image.open(fond).convert("RGB").copy()
        draw = ImageDraw.Draw(img)
        W, H = img.size
        try:
            font = ImageFont.truetype(FONT_PATH, 96)
        except Exception:
            font = ImageFont.load_default()
        lignes = wrap_text_pillow(texte, font, draw, W - 200)
        line_height = int(96 * 1.5)
        total_h = len(lignes) * line_height
        y_start = (H - total_h) // 2 - 200
        for i, ligne in enumerate(lignes):
            bbox = draw.textbbox((0, 0), ligne, font=font)
            w = bbox[2] - bbox[0]
            x = (W - w) // 2
            y = y_start + i * line_height
            draw.text((x, y), ligne, font=font, fill=couleur)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        date_str = str(post.get("Date", "")).replace("-", "")
        pngs.append((f"{date_str}_Story_{idx+1}", buf.getvalue()))
    return pngs

def generer_png_carrousel(post):
    hook = str(post.get("Hook", ""))
    contenu = str(post.get("ContenuPost", ""))
    pilier = str(post.get("Pilier", ""))
    try:
        jour = int(str(post.get("Date", "0000-00-00")).split("-")[2])
    except Exception:
        jour = 1
    is_terra = jour % 2 == 0
    fond_unique = FOND_TERRA if is_terra else FOND_BEIGE
    couleur_unique = (251, 248, 246) if is_terra else (74, 56, 51)
    fond_cover = fond_unique
    fond_slides = fond_unique
    couleur_cover = couleur_unique
    couleur_slides = couleur_unique
    slides_textes = []
    morceaux = re.split(r'Slide\s*\d+\s*[:/]?\s*', contenu)
    for morceau in morceaux:
        texte = morceau.strip().replace('\n', ' ')
        if texte:
            slides_textes.append(texte)
    if not slides_textes:
        slides_textes = [hook]
    elif slides_textes and slides_textes[0].strip() == hook.strip():
        slides_textes = slides_textes[1:]

    def faire_slide(fond, couleur, texte):
        img = Image.open(fond).convert("RGB").copy()
        W_orig, H_orig = img.size
        top = H_orig - 1080
        img = img.crop((0, top, 1080, H_orig))
        draw = ImageDraw.Draw(img)
        W, H = img.size
        taille = 88
        if len(texte) > 120:
            taille = 60
        elif len(texte) > 80:
            taille = 72
        try:
            font = ImageFont.truetype(FONT_PATH, taille)
        except Exception:
            font = ImageFont.load_default()
        lignes = wrap_text_pillow(texte, font, draw, W - 200)
        line_height = int(88 * 1.5)
        total_h = len(lignes) * line_height
        y_start = (H - total_h) // 2 - 60
        for i, ligne in enumerate(lignes):
            bbox = draw.textbbox((0, 0), ligne, font=font)
            w = bbox[2] - bbox[0]
            x = (W - w) // 2
            y = y_start + i * line_height
            draw.text((x, y), ligne, font=font, fill=couleur)
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    def faire_slide_logo(fond):
        img = Image.open(fond).convert("RGB").copy()
        W_orig, H_orig = img.size
        top = H_orig - 1080
        img = img.crop((0, top, 1080, H_orig))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    date_str = str(post.get("Date", "")).replace("-", "")
    pngs = []
    pngs.append((f"{date_str}_Carrousel_1", faire_slide(fond_cover, couleur_cover, hook)))
    for idx, texte in enumerate(slides_textes[:7]):
        pngs.append((f"{date_str}_Carrousel_{idx+2}", faire_slide(fond_slides, couleur_slides, texte)))
    pngs.append((f"{date_str}_Carrousel_{len(pngs)+1}", faire_slide_logo(fond_cover)))
    return pngs

def generer_brief_canva(post):
    import anthropic as ant
    client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    support = post.get('Support', '')
    if support in ["BD", "Infographie"]:
        prompt = f"""Tu es la Directrice Artistique de Maman & Leader.
Style : {support}

POST :
Hook : {post.get('Hook','')}
Contenu : {post.get('ContenuPost','')}
Angle : {post.get('Angle','')}
Brief general : {post.get('BriefGeneral','')}

{"BD — 6 cases CARREES grille 2x3, illustration douce realiste, femme brune, scenes quotidiennes, bulles dialogue, derniere case fond nude texte editorial fort, 1080x1350px." if support == "BD" else "INFOGRAPHIE — structure graphique, icones lineaires, fond nude, typo editoriale, palette terracotta, 1080x1350px."}

Produis :
1. Prompt ChatGPT/Designer complet et precis
2. Textes exacts pour chaque case/bloc
3. Conclusion editoriale forte"""
    else:
        prompt = f"""Tu es la Directrice Artistique de Maman & Leader.
Palette : #FBF8F6 #F2E8E3 #C77A5C #4A3833
Polices : Playfair Display (titres) / Lora (corps)

POST {support.upper()} :
Hook : {post.get('Hook','')}
Contenu : {post.get('ContenuPost','')}
Brief general : {post.get('BriefGeneral','')}

Instructions Canva pas a pas :
1. Format pixels et fond
2. Chaque element avec police/taille/couleur
3. Textes prets a coller"""
    msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=1500, messages=[{"role": "user", "content": prompt}])
    return msg.content[0].text

def formater_texte_canva(post):
    return f"""MAMAN & LEADER — {post.get('Date','')}
Support : {post.get('Support','')} | Pilier : {post.get('Pilier','')}

HOOK :
{post.get('Hook','')}

CONTENU :
{post.get('ContenuPost','')}

CAPTION :
{post.get('Caption','')}
"""

def lien_canva(support):
    return {"Carrousel": "https://www.canva.com/design/DAHIKTFXpoc/edit", "Story": "https://www.canva.com/create/instagram-stories/", "Reel": "https://www.canva.com/create/instagram-stories/", "Infographie": "https://www.canva.com/create/infographics/"}.get(support, "https://www.canva.com")

def generer_semaine(client, date_debut, date_fin, intention_data, historique_hooks=[], historique_sujets=[]):
    historique_section = ""
    if historique_hooks:
        hooks_str = "\n".join([f"- {h}" for h in historique_hooks[:30]])
        sujets_str = "\n".join([f"- {s}" for s in historique_sujets[:20]]) if historique_sujets else ""
        historique_section = f"""HISTORIQUE A EVITER :
Hooks deja utilises :
{hooks_str}
Sujets deja traites :
{sujets_str}
Propose des situations entierement nouvelles.

"""
    prompt = f"""Tu generes un calendrier editorial Instagram pour Maman & Leader.

IMPORTANT : Ecris en francais correct avec tous les accents (e accent aigu/grave, c cedille, etc.). N'utilise jamais de texte sans accents.

DONNEES :
{historique_section}Intention : {intention_data.get('Intentions marketing','')}
Phase : {intention_data.get('Phase marketing','Consolidation')}
Pilier : {intention_data.get('Pilier dominant','A tes cotes')}
Date debut : {date_debut}
Date fin : {date_fin}

POSITIONNEMENT : Maison editoriale femmes dirigeantes et meres.
Ton : sobre, stable, introspectif, non injonctif.

EQUILIBRE OBLIGATOIRE : identification + ressource positive + appel a l'action bienveillant.
Jamais uniquement un constat negatif. Toujours une ouverture.

NOTE DE CLOTURE OBLIGATOIRE :
"Garde ce post pour le jour ou tu en auras besoin." /
"Si une femme de ton entourage vit ca, envoie-lui ce post." /
"Partage ca a quelqu'un qui porte trop en ce moment."

RYTHME : 5 publications par semaine, min 1 Reel, min 1 BD ou Infographie, Stories quotidiennes.
STRUCTURE : Une entree par jour. Min 1 Story par jour.
REPARTITION : 60% Identification / 20% Conscience / 10% Stabilisation / 10% Invitation
REPARTITION SUPPORTS : 30% Story / 25% Carrousel / 20% Reel / 15% Infographie / 10% BD

HOOKS : Courts, concrets, varies, jamais repetes.

STRUCTURE PAR SUPPORT :
Carrousel : Slide 1 / Slide 2 / Slide 3 / Slide 4 (min 4, max 7, une phrase par slide)
Story : Story 1 / Story 2 / Story 3 (min 3, max 6, courtes)
Reel : Plan / Texte 1 / Silence / Texte 2 / Texte final
Infographie : Titre / Sous-titre / Contenu bloc 1 a 5 / Conclusion / Prompt ChatGPT : ...
BD : Case 1 a 5 : Scene/Dialogue/Ambiance / Case 6 : Conclusion/Texte fort / Prompt ChatGPT : ...

CAPTION : 300-400 caracteres max. Pas de guillemets.
Question ouverte positive en fin.
50% sans mention / 30% guide gratuit / 15% ebook 9.90 / 5% ebook 24.90
Si mention : Le lien est en bio.

BRIEF GENERAL : Uniquement pour Reel, BD et Infographie — un texte libre de quelques phrases decrivant l'ambiance visuelle, les couleurs, la mise en scene et le style attendu pour la creation. Laisser vide ("") pour Story et Carrousel.

VALEURS AUTORISEES :
Support : Reel / Story / Carrousel / Infographie / BD
Pilier : A tes cotes / Structurer sans s'epuiser
Angle : Identification / Conscience / Desserrage / Invitation

FORMAT : Tableau JSON valide uniquement [ ... ]. Aucun texte avant ou apres.
Champs : Date, Support, Pilier, Angle, Hook, ContenuPost, Caption, BriefGeneral"""
    msg = client.messages.create(model="claude-sonnet-4-6", max_tokens=8192, messages=[{"role": "user", "content": prompt}])
    reponse = msg.content[0].text.strip()
    if "```" in reponse:
        reponse = re.sub(r'```json?\s*', '', reponse)
        reponse = re.sub(r'```', '', reponse)
    reponse = reponse.strip()
    start = reponse.find('[')
    end = reponse.rfind(']') + 1
    if start >= 0 and end > start:
        return json.loads(reponse[start:end])
    return json.loads(reponse)

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');
* { box-sizing: border-box; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
html, body, .stApp { background-color: #FBF8F6 !important; font-family: 'Lora', serif !important; }
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: #4A3833 !important; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-family: 'Lora', serif; margin-right: 4px; background: #FAEAE3; color: #C77A5C; border: 1px solid #EDD9CF; }
.badge-ok { background: #E1F5EE !important; color: #0F6E56 !important; border-color: #B2DFD0 !important; }
.badge-crea { background: #EEF4FB !important; color: #1565C0 !important; border-color: #90CAF9 !important; }
.badge-modif { background: #FFF3E0 !important; color: #E65100 !important; border-color: #FFB74D !important; }
.stButton > button { font-family: 'Lora', serif !important; border-radius: 8px !important; }
.stButton > button[kind="primary"] { background-color: #C77A5C !important; border: none !important; color: #FBF8F6 !important; }
hr { border-color: #EDD9CF !important; opacity: 0.5 !important; }
.drive-badge { display:inline-flex; align-items:center; gap:6px; background:#E8F5E9; border:1px solid #A5D6A7; border-radius:20px; padding:4px 12px; font-size:12px; color:#2E7D32; font-family:'Lora',serif; margin:4px 0; }
</style>
""", unsafe_allow_html=True)

prompts = charger_prompts()

if st.button("← Hub"):
    st.switch_page("app.py")

st.markdown("""
<div style="font-family:'Playfair Display',serif;font-size:32px;font-weight:700;color:#4A3833;margin-bottom:4px;">Calendrier Social</div>
<div style="font-family:'Lora',serif;font-size:14px;color:#8C5A49;font-style:italic;margin-bottom:16px;">Genere, valide et envoie en creation chaque post du mois</div>
""", unsafe_allow_html=True)
st.markdown("<hr/>", unsafe_allow_html=True)

tab_gen, tab_val = st.tabs(["✦ Generer le calendrier", "✅ Valider les posts"])

# ONGLET 1 — GENERER
with tab_gen:
    col1, col2, col3 = st.columns(3)
    with col1:
        date_debut_input = st.date_input("Date de début *", value=datetime.date.today())
    with col2:
        date_fin_input = st.date_input("Date de fin *", value=datetime.date.today() + datetime.timedelta(days=6))
    with col3:
        contexte_supp = st.text_area("Contexte (optionnel)", placeholder="Lancement ebook, evenement...", height=70)

    st.markdown("<br/>", unsafe_allow_html=True)
    cols_f = st.columns(2)
    for col, (key, label, desc) in zip(cols_f, [
        ("marketing", "1. Directrice Marketing", "Definit intention et pilier du mois"),
        ("redactrice", "2. Generation calendrier", "Calendrier complet jour par jour"),
    ]):
        with col:
            img = charger_image(key)
            if img:
                st.image(img, width=60)
            st.caption(f"**{label}** — {desc}")

    st.markdown("<br/>", unsafe_allow_html=True)

    if st.button("Generer le calendrier", type="primary", use_container_width=True):
        date_debut = date_debut_input.strftime("%Y-%m-%d")
        date_fin = date_fin_input.strftime("%Y-%m-%d")

        with st.expander("Etape 1 — Directrice Marketing", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("marketing")
                if img:
                    st.image(img, width=55)
            with col_t:
                with st.spinner("Intention marketing..."):
                    import anthropic as ant_m
                    client_m = ant_m.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                    instr_mkt = f"""Definis l'intention marketing de Maman & Leader pour la periode du {date_debut} au {date_fin}.
Contexte : {contexte_supp if contexte_supp else 'Aucun'}
Reponds UNIQUEMENT avec ce JSON :
{{"Intentions marketing": "...", "Phase marketing": "Consolidation", "Pilier dominant": "A tes cotes"}}
Phase : Installation ou Consolidation ou Stabilisation
Pilier : A tes cotes ou Structurer sans s'epuiser"""
                    msg_m = client_m.messages.create(model="claude-sonnet-4-6", max_tokens=500, messages=[{"role": "user", "content": instr_mkt}])
                    reponse_mkt = msg_m.content[0].text
                try:
                    json_match = re.search(r'\{[^{}]+\}', reponse_mkt, re.DOTALL)
                    intention_data = json.loads(json_match.group()) if json_match else {"Intentions marketing": reponse_mkt[:200], "Phase marketing": "Consolidation", "Pilier dominant": "A tes cotes"}
                except Exception:
                    intention_data = {"Intentions marketing": reponse_mkt[:200], "Phase marketing": "Consolidation", "Pilier dominant": "A tes cotes"}
                st.success("Intention definie")
                c1, c2, c3 = st.columns(3)
                c1.metric("Phase", intention_data.get("Phase marketing","—"))
                c2.metric("Pilier", intention_data.get("Pilier dominant","—"))
                c3.metric("Periode", f"{date_debut} -> {date_fin}")
                st.caption(intention_data.get("Intentions marketing","")[:300])
                st.session_state["intention_data"] = intention_data

        with st.expander("Etape 2 — Generation du calendrier", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("redactrice")
                if img:
                    st.image(img, width=55)
            with col_t:
                import anthropic as ant_c
                client_c = ant_c.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                historique_hooks = []
                historique_sujets = []
                historique_angles = []
                try:
                    token_at = os.getenv("AIRTABLE_TOKEN")
                    base_at = os.getenv("AIRTABLE_BASE_ID")
                    table_at = os.getenv("AIRTABLE_TABLE_ID")
                    if token_at and base_at and table_at:
                        url_at = f"https://api.airtable.com/v0/{base_at}/{table_at}"
                        headers_at = {"Authorization": f"Bearer {token_at}"}
                        resp_at = requests.get(url_at, headers=headers_at, params={"pageSize": 100}, timeout=15)
                        if resp_at.status_code == 200:
                            records_at = resp_at.json().get("records", [])
                            for r in records_at:
                                f_at = r.get("fields", {})
                                if f_at.get("Hook"):
                                    historique_hooks.append(f_at["Hook"])
                                if f_at.get("ContenuPost"):
                                    historique_sujets.append(str(f_at["ContenuPost"])[:80])
                                if f_at.get("Angle"):
                                    historique_angles.append(f_at["Angle"])
                            angles_count = Counter(historique_angles)
                            st.caption(f"Historique : {len(historique_hooks)} posts charges")
                            st.caption(f"Angles — Id: {angles_count.get('Identification',0)} / Co: {angles_count.get('Conscience',0)} / De: {angles_count.get('Desserrage',0)} / In: {angles_count.get('Invitation',0)}")
                except Exception:
                    st.caption("Historique non charge")

                tous_les_jours = []
                d = date_debut_input
                d_fin = date_fin_input
                while d <= d_fin:
                    tous_les_jours.append(d)
                    d += datetime.timedelta(days=1)
                semaines = [tous_les_jours[i:i+7] for i in range(0, len(tous_les_jours), 7)]
                tous_posts = []
                progress = st.progress(0)
                for idx, semaine in enumerate(semaines):
                    ds = semaine[0].strftime("%Y-%m-%d")
                    df = semaine[-1].strftime("%Y-%m-%d")
                    if ds == df:
                        st.caption(f"Jour : {ds}")
                    else:
                        st.caption(f"Periode {idx+1}/{len(semaines)} : {ds} -> {df}")
                    progress.progress(int((idx / len(semaines)) * 90))
                    try:
                        posts_s = generer_semaine(client_c, ds, df, st.session_state.get("intention_data", {}), historique_hooks, historique_sujets)
                        tous_posts.extend(posts_s)
                        for p in posts_s:
                            if p.get("Hook"):
                                historique_hooks.append(p["Hook"])
                            if p.get("ContenuPost"):
                                historique_sujets.append(str(p["ContenuPost"])[:80])
                        st.caption(f"  -> {len(posts_s)} posts")
                    except Exception as e:
                        st.warning(f"Semaine {idx+1} : {str(e)[:100]}")
                progress.progress(100)
                if tous_posts:
                    st.success(f"{len(tous_posts)} posts generes du {date_debut} au {date_fin}")
                    st.session_state["calendrier_posts"] = tous_posts
                    st.session_state["calendrier_mois"] = f"{date_debut}_au_{date_fin}"
                else:
                    st.error("Aucun post genere")
                    st.session_state["calendrier_posts"] = []

    if st.session_state.get("calendrier_posts"):
        posts = st.session_state["calendrier_posts"]
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Total", len(posts))
        c2.metric("Reels", len([p for p in posts if p.get("Support")=="Reel"]))
        c3.metric("Carrousels", len([p for p in posts if p.get("Support")=="Carrousel"]))
        c4.metric("Stories", len([p for p in posts if p.get("Support")=="Story"]))
        c5.metric("Infographies", len([p for p in posts if p.get("Support")=="Infographie"]))
        c6.metric("BD", len([p for p in posts if p.get("Support")=="BD"]))
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Envoyer dans Airtable", type="primary", use_container_width=True):
                with st.spinner("Envoi en cours..."):
                    ok, msg_at = envoyer_airtable(posts)
                st.session_state["msg_airtable"] = (ok, msg_at)
            if "msg_airtable" in st.session_state:
                ok_s, msg_s = st.session_state["msg_airtable"]
                if ok_s:
                    st.success(msg_s)
                else:
                    st.error(msg_s)
        with col_b2:
            st.download_button("Telecharger JSON", data=json.dumps(posts, ensure_ascii=False, indent=2), file_name=f"calendrier_{st.session_state.get('calendrier_mois','')}.json", mime="application/json", use_container_width=True)

# ONGLET 2 — VALIDER
with tab_val:
    col_src, col_btn, col_sup, col_stat = st.columns([2, 2, 1.5, 1.5])
    with col_src:
        source = st.radio("Source", ["Posts generes (session en cours)", "Charger depuis Airtable"], horizontal=True, label_visibility="collapsed")

    if source == "Charger depuis Airtable":
        with col_btn:
            if st.button("Charger depuis Airtable", type="primary", use_container_width=True, key="btn_charger"):
                with st.spinner("Chargement..."):
                    records, err = lire_airtable()
                if err:
                    st.error(err)
                else:
                    posts_at = []
                    for r in records:
                        f = r.get("fields", {})
                        f["_record_id"] = r.get("id", "")
                        posts_at.append(f)
                    posts_at_tries = sorted(posts_at, key=lambda x: x.get("Date", ""))
                    st.session_state["posts_validation"] = posts_at_tries
                    st.success(f"{len(posts_at_tries)} posts charges")
        with col_sup:
            filtre_support = st.selectbox("Support", ["Tous","Reel","Carrousel","Story","Infographie","BD"], key="filt_sup")
        with col_stat:
            filtre_statut = st.selectbox("Statut", ["Brouillon","Valide","Tous","Publie"], key="filt_stat")
        posts_a_valider = st.session_state.get("posts_validation", [])
    else:
        with col_sup:
            filtre_support = st.selectbox("Support", ["Tous","Reel","Carrousel","Story","Infographie","BD"], key="filt_sup2")
        with col_stat:
            filtre_statut = st.selectbox("Statut", ["Brouillon","Valide","Tous","Publie"], key="filt_stat2")
        posts_session = st.session_state.get("calendrier_posts", [])
        for p in posts_session:
            if "_record_id" not in p:
                p["_record_id"] = ""
        posts_a_valider = posts_session

    if not posts_a_valider:
        if source == "Posts generes (session en cours)":
            st.info("Genere d'abord un calendrier dans l'onglet Generer.")
        else:
            st.info("Clique sur 'Charger depuis Airtable'.")
    else:
        posts_filtres = list(posts_a_valider)
        if filtre_support != "Tous":
            posts_filtres = [p for p in posts_filtres if p.get("Support") == filtre_support]
        if filtre_statut == "Brouillon":
            posts_filtres = [p for p in posts_filtres if p.get("StatutPublication", "Brouillon") in ["Brouillon","Fait","",None]]
        elif filtre_statut == "Valide":
            posts_filtres = [p for p in posts_filtres if p.get("StatutPublication") == "Valide"]
        elif filtre_statut == "Publie":
            posts_filtres = [p for p in posts_filtres if p.get("StatutPublication") == "Publie"]
        posts_filtres = sorted(posts_filtres, key=lambda p: p.get("Date",""))

        nb_total = len(posts_a_valider)
        nb_val = len([p for p in posts_a_valider if p.get("StatutPublication") == "Valide"])
        nb_crea = len([p for p in posts_a_valider if p.get("StatutPublication") == "En creation"])
        nb_pub = len([p for p in posts_a_valider if p.get("StatutPublication") == "Publie"])
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total", nb_total)
        c2.metric("Brouillon", nb_total - nb_val - nb_crea - nb_pub)
        c3.metric("Valides", nb_val)
        c4.metric("En creation", nb_crea)
        c5.metric("Publies", nb_pub)
        st.caption(f"**{len(posts_filtres)} posts affiches**")
        st.markdown("<hr/>", unsafe_allow_html=True)

        for idx, post in enumerate(posts_filtres):
            record_id = post.get("_record_id","")
            support = post.get("Support","")
            date = post.get("Date","")
            hook = str(post.get("Hook",""))[:55]
            statut = post.get("StatutPublication","Brouillon")
            badge_class = {"Valide":"badge-ok","En creation":"badge-crea","Publie":"badge-ok","Brouillon":""}.get(statut,"")

            with st.expander(f"📅 {date} — {support} — {hook}...", expanded=False):
                st.markdown(f"""
                <span class="badge">{support}</span>
                <span class="badge">{post.get('Pilier','')}</span>
                <span class="badge">{post.get('Angle','')}</span>
                <span class="badge {badge_class}">{statut}</span>
                """, unsafe_allow_html=True)
                st.markdown("<br/>", unsafe_allow_html=True)

                col_g, col_d = st.columns(2)
                with col_g:
                    st.markdown("**Hook :**")
                    st.write(str(post.get("Hook","")))
                    st.markdown("**Contenu :**")
                    st.text(str(post.get("ContenuPost","")))
                with col_d:
                    st.markdown("**Caption :**")
                    caption_str = str(post.get("Caption","") or "")
                    st.text(caption_str[:400] + ("..." if len(caption_str) > 400 else ""))
                    brief_general = post.get("BriefGeneral", "")
                    if brief_general:
                        st.markdown("**Brief général :**")
                        st.caption(brief_general)

                st.markdown("<br/>", unsafe_allow_html=True)
                col_a1, col_a2, col_a3 = st.columns(3)

                with col_a1:
                    if st.button("✅ Valider", key=f"val_{idx}_{date}", use_container_width=True):
                        if record_id:
                            ok, msg_at = mettre_a_jour_airtable(record_id, {"StatutPublication": "Valide"})
                            if ok:
                                post["StatutPublication"] = "Valide"
                                st.success("✦ Valide !")
                            else:
                                st.error(f"Erreur : {msg_at}")
                        else:
                            token = os.getenv("AIRTABLE_TOKEN")
                            base_id_at = os.getenv("AIRTABLE_BASE_ID")
                            table_id_at = os.getenv("AIRTABLE_TABLE_ID")
                            url_at = f"https://api.airtable.com/v0/{base_id_at}/{table_id_at}"
                            headers_at = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                            fields_at = {k: str(post[k]) for k in ["Date","Support","Pilier","Angle","Hook","ContenuPost","Caption","BriefGeneral"] if post.get(k)}
                            fields_at["StatutPublication"] = "Valide"
                            try:
                                resp_at = requests.post(url_at, headers=headers_at, json={"records": [{"fields": fields_at}]}, timeout=30)
                                if resp_at.status_code == 200:
                                    post["_record_id"] = resp_at.json()["records"][0]["id"]
                                    post["StatutPublication"] = "Valide"
                                    st.success("✦ Envoye et valide !")
                                else:
                                    st.error(resp_at.text[:150])
                            except Exception as e:
                                st.error(str(e)[:200])

                with col_a2:
                    with st.form(key=f"form_{idx}_{date}"):
                        demande = st.text_area("Demande", placeholder="Hook plus direct, caption plus courte...", height=60, key=f"dem_{idx}")
                        submitted = st.form_submit_button("✏️ Modifier avec IA", use_container_width=True)
                        if submitted:
                            if demande:
                                with st.spinner("Modification..."):
                                    try:
                                        modifs = modifier_post_ia(post, demande)
                                        for k, v in modifs.items():
                                            post[k] = v
                                        post["StatutPublication"] = "Brouillon"
                                        if record_id:
                                            fields_up = dict(modifs)
                                            fields_up["StatutPublication"] = "Brouillon"
                                            ok_m, msg_m = mettre_a_jour_airtable(record_id, fields_up)
                                            if ok_m:
                                                st.success("✦ Modifie et mis a jour !")
                                            else:
                                                st.error(f"Modifie mais erreur : {msg_m}")
                                        else:
                                            st.success("✦ Modifie en session !")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(str(e)[:200])
                            else:
                                st.warning("Ecris ta demande.")

                with col_a3:
                    if support in ["Reel", "BD", "Infographie"]:
                        if st.button("🎨 Brief creation", key=f"crea_{idx}_{date}", use_container_width=True):
                            with st.spinner("Generation..."):
                                brief = generer_brief_canva(post)
                            post["PromptCrea"] = brief
                            if record_id:
                                mettre_a_jour_airtable(record_id, {"StatutPublication": "En creation", "PromptCrea": brief})
                            post["StatutPublication"] = "En creation"
                            st.session_state[f"brief_{idx}_{date}"] = brief
                            st.session_state[f"show_brief_{idx}_{date}"] = True

                st.markdown("<br/>", unsafe_allow_html=True)
                col_v1, col_v2 = st.columns(2)

                with col_v1:
                    if support in ["Story", "Carrousel"]:
                        label_btn = "🖼️ Modifier les visuels generes" if post.get("URLVisuel") else f"🖼️ Generer visuel {support}"
                        if st.button(label_btn, key=f"btn_png_{idx}_{date}", use_container_width=True):
                            with st.spinner("Generation du visuel..."):
                                try:
                                    if support == "Story":
                                        pngs = generer_png_story(post)
                                    else:
                                        pngs = generer_png_carrousel(post)
                                    pngs_avec_drive = []
                                    for nom, png_bytes in pngs:
                                        filename = f"{nom}.png"
                                        tmp_path = VISUELS_DIR / filename
                                        tmp_path.write_bytes(png_bytes)
                                        drive_result = upload_vers_drive(str(tmp_path), filename)
                                        pngs_avec_drive.append((nom, png_bytes, drive_result))
                                    st.session_state[f"pngs_{idx}_{date}"] = pngs_avec_drive
                                    st.session_state[f"show_png_{idx}_{date}"] = True
                                    st.success(f"{len(pngs)} visuel(s) genere(s) !")
                                except Exception as e:
                                    st.error(f"Erreur : {str(e)[:200]}")

                        if post.get("URLVisuel"):
                            with st.form(key=f"form_visuel_{idx}_{date}"):
                                demande_visuel = st.text_area("Demande de modification", placeholder="Hook plus court, ton plus doux...", height=60, key=f"dem_vis_{idx}")
                                submit_visuel = st.form_submit_button("🔄 Regenerer avec IA")
                                if submit_visuel:
                                    if demande_visuel:
                                        with st.spinner("Modification du texte..."):
                                            try:
                                                modifs = modifier_post_ia(post, demande_visuel)
                                                for k, v in modifs.items():
                                                    post[k] = v
                                                if record_id:
                                                    mettre_a_jour_airtable(record_id, modifs)
                                            except Exception as e:
                                                st.error(f"Erreur modification texte : {str(e)[:200]}")
                                                st.stop()
                                        with st.spinner("Regeneration des visuels..."):
                                            try:
                                                if support == "Story":
                                                    pngs = generer_png_story(post)
                                                else:
                                                    pngs = generer_png_carrousel(post)
                                                pngs_avec_drive = []
                                                for nom, png_bytes in pngs:
                                                    filename = f"{nom}.png"
                                                    tmp_path = VISUELS_DIR / filename
                                                    tmp_path.write_bytes(png_bytes)
                                                    drive_result = upload_vers_drive(str(tmp_path), filename)
                                                    pngs_avec_drive.append((nom, png_bytes, drive_result))
                                                    if drive_result and record_id:
                                                        urls_existantes = post.get("URLVisuel", "") or ""
                                                        nouvelle_url = drive_result["url_directe"]
                                                        if nouvelle_url not in urls_existantes.split("\n"):
                                                            urls_combinees = (urls_existantes + "\n" + nouvelle_url).strip() if urls_existantes else nouvelle_url
                                                            post["URLVisuel"] = urls_combinees
                                                if record_id:
                                                    mettre_a_jour_airtable(record_id, {"URLVisuel": post.get("URLVisuel", "")})
                                                st.session_state[f"pngs_{idx}_{date}"] = pngs_avec_drive
                                                st.session_state[f"show_png_{idx}_{date}"] = True
                                                st.success("✦ Hook, contenu et visuels mis a jour !")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erreur regeneration : {str(e)[:200]}")
                                    else:
                                        st.warning("Ecris ta demande.")
                    elif support in ["Reel", "BD", "Infographie"]:
                        st.markdown(f"**Upload {support}**")
                        uploaded = st.file_uploader(f"Fichier {support}", type=["mp4","mov","jpg","jpeg","png","gif"], key=f"upload_{idx}_{date}")
                        if uploaded is not None:
                            if st.button("Envoyer statut Airtable", key=f"send_up_{idx}_{date}", use_container_width=True):
                                if record_id:
                                    ok_up, msg_up = mettre_a_jour_airtable(record_id, {"StatutPublication": "En creation"})
                                    if ok_up:
                                        st.success("Statut mis a jour !")
                                    else:
                                        st.error(msg_up)
                                else:
                                    st.warning("Envoie d'abord dans Airtable.")

                with col_v2:
                    date_pub = st.date_input("Date publication", key=f"dp_{idx}_{date}", value=None)
                    heure_pub = st.time_input("Heure", key=f"hp_{idx}_{date}", value=datetime.time(9, 0))
                    if st.button("📅 Programmer", key=f"prog_{idx}_{date}", use_container_width=True):
                        if date_pub and record_id:
                            dt_pub = datetime.datetime.combine(date_pub, heure_pub)
                            dt_str = dt_pub.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                            ok_p, msg_p = mettre_a_jour_airtable(record_id, {"DatePublication": dt_str, "StatutPublication": "Programme"})
                            if ok_p:
                                st.success(f"✦ Programme le {date_pub} a {heure_pub} !")
                            else:
                                st.error(msg_p)
                        elif not record_id:
                            st.warning("Envoie d'abord dans Airtable.")
                        else:
                            st.warning("Choisis une date.")

                # VIGNETTES VISUELS DEJA GENERES (depuis Airtable)
                urls_visuel_existant = post.get("URLVisuel", "")
                if urls_visuel_existant:
                    with st.expander("🖼️ Visuels deja generes", expanded=False):
                        urls_list = [u.strip() for u in urls_visuel_existant.split("\n") if u.strip()]
                        cols_vignettes = st.columns(min(len(urls_list), 4) or 1)
                        for i, url_v in enumerate(urls_list):
                            with cols_vignettes[i % len(cols_vignettes)]:
                                try:
                                    img_resp = requests.get(url_v, timeout=10)
                                    if img_resp.status_code == 200:
                                        st.image(img_resp.content, use_container_width=True)
                                    else:
                                        st.markdown(f"[Voir l'image]({url_v})")
                                except Exception:
                                    st.markdown(f"[Voir l'image]({url_v})")

                # AFFICHAGE PNG
                if st.session_state.get(f"show_png_{idx}_{date}"):
                    pngs_avec_drive = st.session_state.get(f"pngs_{idx}_{date}", [])
                    st.markdown("---")
                    st.markdown("**Visuels generes :**")
                    urls_pour_publication = []
                    for nom, png_bytes, drive_result in pngs_avec_drive:
                        st.markdown(f"*{nom}*")
                        b64 = base64.b64encode(png_bytes).decode()
                        st.markdown(f'<div style="border:1px solid #EDD9CF;border-radius:8px;margin:8px 0;overflow:hidden;"><img src="data:image/png;base64,{b64}" style="width:100%;max-width:380px;"/></div>', unsafe_allow_html=True)
                        if drive_result:
                            st.markdown(f'''
                            <div class="drive-badge">
                                ☁️ Sur Drive —
                                <a href="{drive_result["url_publique"]}" target="_blank" style="color:#2E7D32;">Voir</a>
                                &nbsp;|&nbsp;
                                <a href="{drive_result["url_directe"]}" target="_blank" style="color:#2E7D32;">Lien direct</a>
                            </div>
                            ''', unsafe_allow_html=True)
                            urls_pour_publication.append(drive_result["url_directe"])
                            if record_id:
                                urls_existantes = post.get("URLVisuel", "") or ""
                                nouvelle_url = drive_result["url_directe"]
                                if nouvelle_url not in urls_existantes:
                                    urls_combinees = (urls_existantes + "\n" + nouvelle_url).strip() if urls_existantes else nouvelle_url
                                    post["URLVisuel"] = urls_combinees
                                    mettre_a_jour_airtable(record_id, {"URLVisuel": urls_combinees})
                        st.download_button(f"⬇️ {nom}.png", data=png_bytes, file_name=f"{nom}_{date}.png", mime="image/png", key=f"dl_{idx}_{date}_{nom}")

                    st.markdown("---")
                    if support == "Story" and urls_pour_publication:
                        if st.button("📤 Publier sur Instagram (Story)", key=f"pub_ig_{idx}_{date}", use_container_width=True):
                            from instagram_publish import publier_story
                            with st.spinner("Publication en cours..."):
                                ok_ig, msg_ig = publier_story(urls_pour_publication[0])
                            if ok_ig:
                                st.success(msg_ig)
                            else:
                                st.error(msg_ig)
                    elif support == "Carrousel" and len(urls_pour_publication) >= 2:
                        if st.button("📤 Publier sur Instagram (Carrousel)", key=f"pub_ig_{idx}_{date}", use_container_width=True):
                            from instagram_publish import publier_carrousel
                            with st.spinner("Publication en cours..."):
                                ok_ig, msg_ig = publier_carrousel(urls_pour_publication, post.get("Caption", ""))
                            if ok_ig:
                                st.success(msg_ig)
                            else:
                                st.error(msg_ig)

                    if st.button("Fermer visuels", key=f"close_png_{idx}_{date}"):
                        st.session_state[f"show_png_{idx}_{date}"] = False

                # AFFICHAGE BRIEF
                if st.session_state.get(f"show_brief_{idx}_{date}"):
                    brief = st.session_state.get(f"brief_{idx}_{date}","")
                    st.markdown("---")
                    st.markdown('<div style="background:#FBF8F6;border:1px solid #EDD9CF;border-left:4px solid #C77A5C;border-radius:12px;padding:20px;">', unsafe_allow_html=True)
                    st.markdown("**Prompt pour creation :**")
                    st.download_button("📄 Telecharger le prompt", data=brief, file_name=f"prompt_{support}_{date}.txt", mime="text/plain", key=f"dl_br_{idx}_{date}")
                    st.markdown("**Instructions :**")
                    st.markdown(brief)
                    if st.button("Fermer", key=f"close_br_{idx}_{date}"):
                        st.session_state[f"show_brief_{idx}_{date}"] = False
                    st.markdown("</div>", unsafe_allow_html=True)