import streamlit as st
import os, json, datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Social",
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

def sauvegarder_livrable(titre, type_mission, resultat):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "id": ts, "titre": titre,
        "auteur": "Maman & Leader",
        "genre": type_mission,
        "type_mission": type_mission,
        "synopsis": titre,
        "resultat": str(resultat),
        "date": datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")
    }
    Path("historique").mkdir(exist_ok=True)
    with open(Path("historique") /
              f"{ts}_{titre[:20].replace(' ','_')}.json",
              "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def lancer_agent(role_key, instruction, prompts, contexte=""):
    from agent_direct import lancer_agent as _lancer
    return _lancer(role_key, instruction, prompts, contexte)
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
.canal-card {
    background: #FFFFFF;
    border: 1px solid #EDD9CF;
    border-radius: 14px;
    padding: 20px;
    text-align: center;
    margin-bottom: 12px;
}
.canal-titre {
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    font-weight: 600;
    color: #4A3833;
    margin-bottom: 4px;
}
.canal-desc {
    font-family: 'Lora', serif;
    font-size: 12px;
    color: #8C5A49;
    font-style: italic;
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
    Contenus Social
</div>
<div style="font-family:'Lora',serif;font-size:14px;color:#8C5A49;
            font-style:italic;margin-bottom:24px;">
    Instagram — relation et presence · Pinterest — acquisition et croissance
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

col_ig, col_pi = st.columns(2)
with col_ig:
    st.markdown("""
    <div class="canal-card">
        <div class="canal-titre">Instagram</div>
        <div class="canal-desc">
            Espace de relation — nourrir la reconnaissance
            emotionnelle, construire la confiance, incarner
            le positionnement dans la duree.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_pi:
    st.markdown("""
    <div class="canal-card">
        <div class="canal-titre">Pinterest</div>
        <div class="canal-desc">
            Moteur d'acquisition — capter les femmes en phase
            de recherche active. Indexation longue duree.
            Croissance organique de la maison.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    theme = st.text_input(
        "Theme du contenu *",
        placeholder="ex : La delegation sereine"
    )
    canal = st.selectbox(
        "Canal prioritaire *",
        ["Instagram + Pinterest",
         "Instagram uniquement",
         "Pinterest uniquement"]
    )
with col2:
    pilier = st.selectbox(
        "Pilier editorial *",
        ["A tes cotes — apaisant, introspectif, respirant",
         "Structurer sans s'epuiser — stable, ancre, mature"]
    )
    nb_posts = st.slider("Nombre de posts", 1, 10, 5)

phase = st.selectbox(
    "Phase marketing *",
    ["Installation — faire connaitre la maison",
     "Consolidation — approfondir la relation",
     "Stabilisation — ancrer la confiance"]
)

contexte_supp = st.text_area(
    "Contexte supplementaire (optionnel)",
    placeholder="Actualite, evenement, lancement en cours...",
    height=80
)

st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("### Le flux de production")

etapes_social = [
    ("marketing",  "1. Intention marketing", "Pilier dominant, angle, promesse"),
    ("editoriale", "2. Angles et formats",   "Structure des posts, messages cles"),
    ("redactrice", "3. Redaction",            "Captions, textes, accroches"),
    ("da",         "4. Direction visuelle",   "Systeme visuel par post"),
]

cols_e = st.columns(4)
for col, (key, titre, desc) in zip(cols_e, etapes_social):
    with col:
        img = charger_image(key)
        if img:
            st.image(img, width=70)
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-family:'Playfair Display',serif;
                        font-size:12px;font-weight:600;
                        color:#4A3833;margin:6px 0 2px;">{titre}</div>
            <div style="font-family:'Lora',serif;font-size:10px;
                        color:#8C5A49;font-style:italic;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

if st.button("Lancer la production sociale",
             type="primary", use_container_width=True):
    if not theme:
        st.error("Merci d'indiquer le theme du contenu.")
    else:
        contexte_global = f"""
Maison editoriale : Maman & Leader
Theme : {theme}
Canal : {canal}
Pilier : {pilier}
Nombre de posts : {nb_posts}
Phase marketing : {phase}
Contexte : {contexte_supp if contexte_supp else 'Aucun'}
Strategie : Identification 60% Mise en conscience 25% Desserrage 10% Invitation 5%
Instagram = relation | Pinterest = acquisition
"""
        resultats = {}

        with st.expander("Etape 1 — Directrice Marketing", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("marketing")
                if img:
                    st.image(img, width=60)
            with col_t:
                with st.spinner("Intention marketing en cours..."):
                    instr = f"""
Definis l'intention marketing pour ce contenu social :
Theme : {theme}
Canal : {canal}
Pilier : {pilier}
Phase : {phase}
Nombre de posts : {nb_posts}
Produis : pilier dominant et justification, angle editorial
pour chaque post, promesse emotionnelle centrale,
repartition Identification/Conscience/Desserrage/Invitation.
"""
                    resultats["marketing"] = lancer_agent(
                        "marketing", instr, prompts, contexte_global
                    )
                st.success("Intention marketing definie")
                st.markdown(resultats["marketing"])

        with st.expander("Etape 2 — Directrice Editoriale", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("editoriale")
                if img:
                    st.image(img, width=60)
            with col_t:
                with st.spinner("Structure des contenus en cours..."):
                    instr = f"""
Sur la base de cette intention marketing :
{resultats['marketing'][:500]}
Structure {nb_posts} posts pour {canal} :
Theme : {theme} | Pilier : {pilier}
Pour chaque post definis : format, angle specifique,
message cle, phase de progression.
"""
                    resultats["editoriale"] = lancer_agent(
                        "editoriale", instr, prompts, contexte_global
                    )
                st.success("Structure des posts definie")
                st.markdown(resultats["editoriale"])

        with st.expander("Etape 3 — Redactrice", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("redactrice")
                if img:
                    st.image(img, width=60)
            with col_t:
                with st.spinner("Redaction des posts en cours..."):
                    instr = f"""
Sur la base de cette structure :
{resultats['editoriale'][:600]}
Redige les {nb_posts} posts complets pour {canal}.
Theme : {theme}
Pour chaque post : texte complet pret a publier,
ton mature introspectif non demonstratif,
jamais motivationnel jamais agressif,
adapte au canal Instagram relation / Pinterest acquisition.
Format : Post 1 / Post 2 / etc.
Uniquement le texte final. Pas de commentaires.
"""
                    resultats["redactrice"] = lancer_agent(
                        "redactrice", instr, prompts, contexte_global
                    )
                st.success("Posts rediges")
                st.markdown(resultats["redactrice"])

        with st.expander("Etape 4 — Directrice Artistique", expanded=True):
            col_i, col_t = st.columns([1, 4])
            with col_i:
                img = charger_image("da")
                if img:
                    st.image(img, width=60)
            with col_t:
                with st.spinner("Direction visuelle en cours..."):
                    instr = f"""
Pour {nb_posts} posts sur {canal} :
Theme : {theme} | Pilier : {pilier}
Definis pour chaque post : type de visuel,
palette utilisee codes hex Maman & Leader,
composition et disposition, intentions typographiques,
prompt de generation visuelle si applicable.
"""
                    resultats["da"] = lancer_agent(
                        "da", instr, prompts, contexte_global
                    )
                st.success("Direction visuelle produite")
                st.markdown(resultats["da"])

        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### Plan social complet")

        livrable = f"""
PLAN SOCIAL — {theme.upper()}
Maman & Leader — {canal}
{datetime.datetime.now().strftime("%d/%m/%Y")}
{'='*50}

PILIER : {pilier}
PHASE : {phase}
POSTS : {nb_posts}

INTENTION MARKETING
{resultats['marketing']}

STRUCTURE DES CONTENUS
{resultats['editoriale']}

TEXTES DES POSTS
{resultats['redactrice']}

DIRECTION VISUELLE
{resultats['da']}
"""
        sauvegarder_livrable(theme, "Contenus Social", livrable)
        from notion_sync import envoyer_notion
        import datetime as dt
        ok, msg = envoyer_notion(
            titre=theme,
            type_mission="Contenus Social",
            contenu=livrable,
            date_str=dt.datetime.now().strftime("%Y-%m-%d")
        )
        if ok:
            st.success("✦ Livrable envoyé dans Notion !")
        else:
            st.warning(f"Notion : {msg}")
        st.success("Plan social genere et sauvegarde !")
        st.download_button(
            "Telecharger le plan social",
            data=livrable,
            file_name=f"social_{theme.replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True
        )