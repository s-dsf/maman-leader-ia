import streamlit as st
import os, json, datetime, requests, re
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Validation Posts",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def charger_image(key):
    chemin = Path(f"avatar_{key}.png")
    if chemin.exists():
        return Image.open(chemin)
    return None

def charger_prompts():
    with open("prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def lire_airtable():
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {"Authorization": f"Bearer {token}"}
    tous_records = []
    offset = None
    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset
        resp = requests.get(url, headers=headers,
                            params=params, timeout=30)
        if resp.status_code != 200:
            return [], f"Erreur {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        tous_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return tous_records, None

def mettre_a_jour_airtable(record_id, fields):
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.patch(url, headers=headers,
                          json={"fields": fields}, timeout=30)
    return resp.status_code == 200, resp.text[:200]

def modifier_post_ia(post, demande):
    import anthropic as ant
    client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""
Tu es la Redactrice de la maison editoriale Maman & Leader.
Ton ton : sobre, stable, introspectif, non injonctif.

POST ACTUEL :
Support : {post.get('Support','')}
Pilier : {post.get('Pilier','')}
Angle : {post.get('Angle','')}
Hook : {post.get('Hook','')}
Contenu : {post.get('ContenuPost','')}
Caption : {post.get('Caption','')}

DEMANDE DE MODIFICATION :
{demande}

Reponds UNIQUEMENT avec un JSON valide contenant les champs modifies :
{{
  "Hook": "...",
  "ContenuPost": "...",
  "Caption": "..."
}}
Ne modifie que ce qui est demande. Garde le meme format (Slides / Stories / Plan Reel).
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    reponse = msg.content[0].text.strip()
    if "```" in reponse:
        reponse = re.sub(r'```json?\s*', '', reponse)
        reponse = re.sub(r'```', '', reponse)
    start = reponse.find('{')
    end = reponse.rfind('}') + 1
    if start >= 0 and end > start:
        return json.loads(reponse[start:end])
    return json.loads(reponse)

def generer_brief_canva(post):
    import anthropic as ant
    client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    prompt = f"""
Tu es la Directrice Artistique de Maman & Leader.
Palette : #FBF8F6 #F2E8E3 #EADCD4 #C77A5C #B05C44 #8C5A49 #6E5A52 #4A3833
Polices : Playfair Display (titres) / Lora (corps)

POST A METTRE EN PAGE :
Support : {post.get('Support','')}
Pilier : {post.get('Pilier','')}
Hook : {post.get('Hook','')}
Contenu : {post.get('ContenuPost','')}
BriefCouleur : {post.get('BriefCouleur','')}
BriefAlignement : {post.get('BriefAlignement','')}
BriefBloc : {post.get('BriefBloc','')}
BriefAmbiance : {post.get('BriefAmbiance','')}

Produis des instructions Canva ultra-precises pas a pas :
1. Format exact en pixels
2. Couleur de fond (code hex)
3. Chaque element a placer (texte, forme, ligne)
4. Police, taille, couleur, alignement pour chaque texte
5. Ordre des calques
6. Conseil pour adapter depuis un template existant

Sois concrete comme si tu guidais quelqu'un devant Canva.
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

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
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-family: 'Lora', serif;
    margin-right: 4px;
    background: #FAEAE3;
    color: #C77A5C;
    border: 1px solid #EDD9CF;
}
.badge-ok { background: #E1F5EE; color: #0F6E56; border-color: #B2DFD0; }
.badge-modif { background: #FFF3E0; color: #E65100; border-color: #FFB74D; }
.badge-crea { background: #EEF4FB; color: #1565C0; border-color: #90CAF9; }
.row-post {
    background: #FFFFFF;
    border: 1px solid #EDD9CF;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.stButton > button {
    font-family: 'Lora', serif !important;
    border-radius: 8px !important;
    font-size: 12px !important;
}
.stButton > button[kind="primary"] {
    background-color: #C77A5C !important;
    border: none !important;
    color: #FBF8F6 !important;
}
hr { border-color: #EDD9CF !important; opacity: 0.5 !important; }
</style>
""", unsafe_allow_html=True)

# ── NAVIGATION ───────────────────────────────────────────
col_nav1, col_nav2 = st.columns([1, 4])
with col_nav1:
    if st.button("← Hub"):
        st.switch_page("app.py")
with col_nav2:
    if st.button("✦ Calendrier Social"):
        st.switch_page("pages/social.py")

st.markdown("""
<div style="font-family:'Playfair Display',serif;font-size:28px;
            font-weight:700;color:#4A3833;margin-bottom:4px;">
    Validation des posts
</div>
<div style="font-family:'Lora',serif;font-size:13px;color:#8C5A49;
            font-style:italic;margin-bottom:16px;">
    Valide, modifie ou envoie en creation chaque post du calendrier
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── CHARGEMENT AIRTABLE ──────────────────────────────────
if "records_airtable" not in st.session_state:
    st.session_state["records_airtable"] = []

col_load1, col_load2, col_load3 = st.columns(3)
with col_load1:
    if st.button("Charger les posts depuis Airtable",
                 type="primary", use_container_width=True):
        with st.spinner("Chargement..."):
            records, err = lire_airtable()
        if err:
            st.error(err)
        else:
            st.session_state["records_airtable"] = records
            st.success(f"{len(records)} posts charges")

with col_load2:
    filtre_support = st.selectbox(
        "Filtrer par support",
        ["Tous", "Reel", "Carrousel", "Story"]
    )
with col_load3:
    filtre_statut = st.selectbox(
        "Filtrer par statut",
        ["Tous", "Fait", "A valider", "En creation", "Publie"]
    )

records = st.session_state.get("records_airtable", [])

if not records:
    st.info("Clique sur 'Charger les posts' pour voir le calendrier.")
    st.stop()

# Filtrer
posts_filtres = records
if filtre_support != "Tous":
    posts_filtres = [r for r in posts_filtres
                     if r.get("fields", {}).get("Support") == filtre_support]
if filtre_statut != "Tous":
    posts_filtres = [r for r in posts_filtres
                     if r.get("fields", {}).get("Statut production") == filtre_statut]

# Trier par date
posts_filtres = sorted(
    posts_filtres,
    key=lambda r: r.get("fields", {}).get("Date", "")
)

st.markdown("<hr/>", unsafe_allow_html=True)

# Stats
nb_total = len(records)
nb_valides = len([r for r in records
                  if r.get("fields",{}).get("Statut production") == "A valider"])
nb_crea = len([r for r in records
               if r.get("fields",{}).get("Statut production") == "En creation"])
nb_publie = len([r for r in records
                 if r.get("fields",{}).get("Statut production") == "Publie"])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total posts", nb_total)
c2.metric("A traiter", nb_total - nb_valides - nb_crea - nb_publie)
c3.metric("Valides", nb_valides)
c4.metric("En creation", nb_crea)
c5.metric("Publies", nb_publie)

st.markdown(f"**{len(posts_filtres)} posts affichés**")
st.markdown("<hr/>", unsafe_allow_html=True)

# ── TABLEAU DES POSTS ─────────────────────────────────────
for idx, record in enumerate(posts_filtres):
    f = record.get("fields", {})
    record_id = record.get("id", "")
    statut = f.get("Statut production", "Fait")
    support = f.get("Support", "")
    date = f.get("Date", "")
    hook = f.get("Hook", "")[:60]
    pilier = f.get("Pilier", "")
    angle = f.get("Angle", "")

    # Couleur badge statut
    badge_class = {
        "A valider": "badge-ok",
        "En creation": "badge-crea",
        "Publie": "badge-ok",
    }.get(statut, "")

    with st.expander(
        f"📅 {date} — {support} — {hook}...",
        expanded=False
    ):
        # Header badges
        st.markdown(f"""
        <span class="badge">{support}</span>
        <span class="badge">{pilier}</span>
        <span class="badge">{angle}</span>
        <span class="badge {badge_class}">{statut}</span>
        """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Contenu en 2 colonnes
        col_gauche, col_droite = st.columns(2)

        with col_gauche:
            st.markdown("**Hook :**")
            st.write(f.get("Hook", ""))
            st.markdown("**Contenu du post :**")
            st.text(f.get("ContenuPost", ""))

        with col_droite:
            st.markdown("**Caption :**")
            st.text(f.get("Caption", "")[:400] + "...")
            st.markdown("**Brief visuel :**")
            st.caption(f"Couleur : {f.get('BriefCouleur','')}")
            st.caption(f"Alignement : {f.get('BriefAlignement','')}")
            st.caption(f"Ambiance : {f.get('BriefAmbiance','')}")

        st.markdown("<br/>", unsafe_allow_html=True)

        # ── ACTIONS ──────────────────────────────────────
        col_a1, col_a2, col_a3 = st.columns(3)

        # VALIDER
        with col_a1:
            if st.button("✅ Valider ce post",
                         key=f"val_{record_id}",
                         use_container_width=True):
                ok, msg = mettre_a_jour_airtable(
                    record_id,
                    {"Statut production": "A valider"}
                )
                if ok:
                    st.success("Post valide !")
                    # Mettre a jour localement
                    record["fields"]["Statut production"] = "A valider"
                    st.rerun()
                else:
                    st.error(f"Erreur : {msg}")

        # DEMANDER MODIFICATION
        with col_a2:
            with st.form(key=f"form_modif_{record_id}"):
                demande = st.text_area(
                    "Demande de modification",
                    placeholder="Ex : Rendre le hook plus direct, raccourcir la caption...",
                    height=80,
                    key=f"demande_{record_id}"
                )
                if st.form_submit_button("✏️ Modifier avec IA",
                                          use_container_width=True):
                    if demande:
                        with st.spinner("Modification en cours..."):
                            try:
                                modifs = modifier_post_ia(f, demande)
                                # Mettre a jour Airtable
                                fields_update = {}
                                if "Hook" in modifs:
                                    fields_update["Hook"] = modifs["Hook"]
                                if "ContenuPost" in modifs:
                                    fields_update["ContenuPost"] = modifs["ContenuPost"]
                                if "Caption" in modifs:
                                    fields_update["Caption"] = modifs["Caption"]
                                fields_update["Statut production"] = "Brouillon"

                                ok, msg_at = mettre_a_jour_airtable(
                                    record_id, fields_update
                                )
                                if ok:
                                    st.success("Post modifie et mis a jour dans Airtable !")
                                    # Mettre a jour localement
                                    record["fields"].update(fields_update)
                                    st.rerun()
                                else:
                                    st.error(f"Erreur Airtable : {msg_at}")
                            except Exception as e:
                                st.error(f"Erreur : {str(e)[:200]}")
                    else:
                        st.warning("Ecris ta demande de modification.")

        # ENVOYER EN CREA
        with col_a3:
            if st.button("🎨 Brief Canva",
                         key=f"crea_{record_id}",
                         use_container_width=True):
                with st.spinner("Generation du brief Canva..."):
                    brief = generer_brief_canva(f)

                # Mettre a jour statut
                mettre_a_jour_airtable(
                    record_id,
                    {"Statut production": "En creation"}
                )
                record["fields"]["Statut production"] = "En creation"

                # Afficher le brief
                st.markdown("**Brief Canva complet :**")
                st.markdown(brief)
                st.download_button(
                    "Telecharger le brief",
                    data=brief,
                    file_name=f"brief_canva_{date}_{support}.txt",
                    mime="text/plain",
                    key=f"dl_brief_{record_id}"
                )