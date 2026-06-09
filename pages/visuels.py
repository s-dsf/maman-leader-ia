import streamlit as st
import os, json, datetime, requests, io
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Visuels",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def charger_prompts():
    with open("prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def charger_image(key):
    chemin = Path(f"avatar_{key}.png")
    if chemin.exists():
        return Image.open(chemin)
    return None

def lancer_agent(role_key, instruction, prompts, contexte=""):
    from agent_direct import lancer_agent as _lancer
    return _lancer(role_key, instruction, prompts, contexte)

def generer_image_hf(prompt, format_visuel="instagram"):
    api_key = os.getenv("HUGGINGFACE_API_KEY", "")
    if not api_key:
        return None, "Cle Hugging Face manquante dans .env"

    tailles = {
    "instagram":       (1024, 1024),
    "pinterest":       (768, 1152),
    "story":           (768, 1366),
    "blog":            (1024, 576),
    "ebook_couverture":(768, 1024),
    "ebook_interieur": (768, 1024),
}
    w, h = tailles.get(format_visuel, (1024, 1024))

    prompt_complet = (
        f"{prompt}, "
        f"elegant editorial style, warm terracotta ivory tones, "
        f"soft nude background, premium feminine editorial, "
        f"structured and soothing, no text, high quality"
    )

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt_complet,
        "parameters": {
            "width": min(w, 1024),
            "height": min(h, 1024),
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
        }
    }

    try:
        response = requests.post(
            API_URL, headers=headers,
            json=payload, timeout=120
        )
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))
            return img, None
        elif response.status_code == 503:
            return None, "Modele en chargement — attends 30 secondes et relance"
        else:
            return None, f"Erreur {response.status_code}"
    except Exception as e:
        return None, str(e)

def sauvegarder_livrable(titre, resultat):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "id": ts, "titre": titre,
        "auteur": "Maman & Leader",
        "genre": "Visuels",
        "type_mission": "Visuels",
        "synopsis": titre,
        "resultat": str(resultat),
        "date": datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")
    }
    Path("historique").mkdir(exist_ok=True)
    with open(Path("historique") /
              f"{ts}_{titre[:20].replace(' ','_')}.json",
              "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');
* { box-sizing: border-box; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
html, body, .stApp {
    background-color: #FBF8F6 !important;
    font-family: 'Lora', serif !important;
}
h1, h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: #4A3833 !important;
}
.stButton > button {
    font-family: 'Lora', serif !important;
    border-radius: 8px !important;
}
.stButton > button[kind="primary"] {
    background-color: #C77A5C !important;
    border: none !important;
    color: #FBF8F6 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #B05C44 !important;
}
hr { border-color: #EDD9CF !important; opacity: 0.5 !important; }
</style>
""", unsafe_allow_html=True)

prompts = charger_prompts()

if st.button("← Hub"):
    st.switch_page("app.py")

st.markdown("""
<div style="font-family:'Playfair Display',serif;font-size:32px;
            font-weight:700;color:#4A3833;margin-bottom:4px;">
    Visuels Instagram & Pinterest
</div>
<div style="font-family:'Lora',serif;font-size:14px;color:#8C5A49;
            font-style:italic;margin-bottom:24px;">
    La DA dirige — Hugging Face genere le fond — Canva finalise
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── FORMULAIRE ───────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    sujet = st.text_input(
        "Sujet du visuel *",
        placeholder="ex : La fatigue du dimanche soir"
    )
    format_visuel = st.selectbox(
        "Format *",
        ["instagram", "pinterest", "story", "blog", "ebook_couverture", "ebook_interieur"],
        format_func=lambda x: {
    "instagram":        "Instagram carre (1080x1080)",
    "pinterest":        "Pinterest vertical (1000x1500)",
    "story":            "Story Instagram (1080x1920)",
    "blog":             "Blog entete (1200x630)",
    "ebook_couverture": "Ebook couverture (1600x2560)",
    "ebook_interieur":  "Ebook interieur chapitre (A4)",
}[x]
    )
with col2:
    pilier = st.selectbox(
        "Pilier *",
        ["A tes cotes — apaisant, introspectif",
         "Structurer sans s'epuiser — stable, ancre"]
    )
    type_visuel = st.selectbox(
        "Type de visuel *",
        ["Citation / texte fort",
         "Fond illustre + espace texte",
         "Ambiance editoriale pure",
         "Visuel avec element graphique"]
    )

texte_post = st.text_area(
    "Texte du post (optionnel — pour que la DA adapte le visuel)",
    height=80,
    placeholder="Colle ici le texte de ton post si tu en as un..."
)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── FLUX ─────────────────────────────────────────────────
st.markdown("### Le flux")
cols_f = st.columns(3)
for col, (key, label) in zip(cols_f, [
    ("da",        "1. Direction artistique"),
    ("maquette",  "2. Instructions Canva"),
    ("da",        "3. Generation visuel"),
]):
    with col:
        img = charger_image(key)
        if img:
            st.image(img, width=70)
        st.caption(label)

st.markdown("<br/>", unsafe_allow_html=True)

if st.button("Generer le visuel",
             type="primary", use_container_width=True):
    if not sujet:
        st.error("Merci d'indiquer le sujet.")
    else:
        contexte = f"""
Maison : Maman & Leader
Sujet : {sujet}
Format : {format_visuel}
Pilier : {pilier}
Type : {type_visuel}
Texte du post : {texte_post if texte_post else 'Non fourni'}
Palette : #FBF8F6 #F2E8E3 #EADCD4 #C77A5C #B05C44 #8C5A49
Typographies : Playfair Display titres / Lora corps
"""
        resultats = {}

        # ── ÉTAPE 1 — Direction artistique ───────────────
        with st.expander("Direction artistique", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("da")
                if img:
                    st.image(img, width=55)
            with col_t:
                with st.spinner("Direction artistique en cours..."):
                    instr_da = f"""
{prompts['da']['taches']}

Pour ce visuel :
Sujet : {sujet}
Format : {format_visuel}
Pilier : {pilier}
Type : {type_visuel}
Texte : {texte_post if texte_post else 'Aucun'}

Produis la direction artistique complete avec :
- Ambiance et mood
- Palette exacte avec codes hex
- Composition detaillee
- Typographie
- Prompt de generation image (en anglais, precis)
- Elements visuels a eviter
"""
                    resultats["da"] = lancer_agent(
                        "da", instr_da, prompts, contexte
                    )
                st.success("Direction artistique produite")
                st.markdown(resultats["da"])

        # ── ÉTAPE 2 — Instructions Canva ─────────────────
        with st.expander("Instructions Canva detaillees", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("maquette")
                if img:
                    st.image(img, width=55)
            with col_t:
                with st.spinner("Instructions Canva en cours..."):
                    instr_maq = f"""
Sur la base de cette direction artistique :
{resultats['da'][:600]}

Produis les instructions Canva pas a pas ultra-precises :
Format : {format_visuel}
Sujet : {sujet}

Instructions format :
1. Taille du document en pixels
2. Couleur de fond exacte (hex)
3. Elements a ajouter (formes, lignes, blocs)
4. Placement du texte (zone, police, taille, couleur, alignement)
5. Effets et opacites
6. Ordre des calques
7. Conseil pour utiliser le template existant

Sois ultra-precis comme si tu guidais quelqu'un
qui ne connait pas le design.
"""
                    resultats["canva"] = lancer_agent(
                        "maquette", instr_maq, prompts, contexte
                    )
                st.success("Instructions Canva produites")
                st.markdown(resultats["canva"])

        # ── ÉTAPE 3 — Génération image HF ────────────────
        with st.expander("Visuel genere (fond)", expanded=True):
            st.caption(
                "Image de fond generee par Hugging Face SDXL — "
                "ajoute ton texte par dessus dans Canva"
            )

            # Extraire le prompt de la DA
            prompt_img = f"{sujet}, {pilier}, editorial feminine style, Maman Leader brand"
            if "Prompt" in resultats["da"]:
                lignes = resultats["da"].split("\n")
                for ligne in lignes:
                    if "prompt" in ligne.lower() and len(ligne) > 30:
                        prompt_img = ligne.split(":")[-1].strip()
                        break

            st.caption(f"Prompt utilise : {prompt_img[:100]}...")

            with st.spinner("Generation en cours (30-60 secondes)..."):
                img_generee, erreur = generer_image_hf(
                    prompt_img, format_visuel
                )

            if erreur:
                st.warning(f"Generation impossible : {erreur}")
                st.info(
                    "Utilise directement les instructions Canva "
                    "ci-dessus avec un fond de ta bibliotheque."
                )
            else:
                st.image(img_generee, caption="Fond genere — a utiliser dans Canva")
                buf = io.BytesIO()
                img_generee.save(buf, format="PNG")
                st.download_button(
                    "Telecharger le fond (PNG)",
                    data=buf.getvalue(),
                    file_name=f"fond_{sujet.replace(' ','_')}.png",
                    mime="image/png",
                    use_container_width=True
                )

        # ── RÉCAP COMPLET ─────────────────────────────────
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### Recapitulatif complet")

        livrable = f"""
BRIEF VISUEL — {sujet.upper()}
Maman & Leader | {format_visuel} | {datetime.datetime.now().strftime("%d/%m/%Y")}
{'='*50}

PILIER : {pilier}
TYPE : {type_visuel}
TEXTE DU POST : {texte_post if texte_post else 'Non fourni'}

DIRECTION ARTISTIQUE
{resultats['da']}

INSTRUCTIONS CANVA
{resultats['canva']}
"""
        sauvegarder_livrable(f"Visuel {sujet}", livrable)
        st.success("Brief visuel sauvegarde !")
        st.download_button(
            "Telecharger le brief complet",
            data=livrable,
            file_name=f"visuel_{sujet.replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True
        )