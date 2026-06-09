import streamlit as st
import os, json, datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Ebook",
    page_icon="📖",
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
        "id": ts,
        "titre": titre,
        "auteur": "Maman & Leader",
        "genre": "Ebook premium",
        "type_mission": type_mission,
        "synopsis": titre,
        "resultat": str(resultat),
        "date": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    }
    Path("historique").mkdir(exist_ok=True)
    with open(Path("historique") / f"{ts}_{titre[:20].replace(' ','_')}.json",
              "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

def lancer_agent(role_key, instruction, prompts, contexte=""):
    from crewai import Agent, Task, Crew, LLM
    from rag import rechercher
    p = prompts[role_key]
    rag_ctx = rechercher(instruction, n=3)
    backstory = p["backstory"]
    if rag_ctx:
        backstory += f"\n\nRÉFÉRENCES MAISON :\n{rag_ctx}"
    claude = LLM(
        model="anthropic/claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    agent = Agent(
        role=p["role"],
        goal="Produire un livrable de qualité premium pour Maman & Leader",
        backstory=backstory,
        verbose=False,
        llm=claude
    )
    desc = instruction
    if contexte:
        desc = f"CONTEXTE DU PROJET :\n{contexte}\n\n{instruction}"
    task = Task(
        description=desc,
        agent=agent,
        expected_output="Livrable structuré, professionnel, aligné Maman & Leader"
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    return str(crew.kickoff())

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
.etape-card {
    background: #FFFFFF;
    border: 1px solid #EDD9CF;
    border-left: 4px solid #EDD9CF;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: all 0.2s;
}
.etape-card.active {
    border-left-color: #C77A5C;
    box-shadow: 0 4px 16px rgba(199,122,92,0.12);
}
.etape-card.done {
    border-left-color: #1D9E75;
    background: #F0FBF7;
}
.etape-titre {
    font-family: 'Playfair Display', serif;
    font-size: 15px;
    font-weight: 600;
    color: #4A3833;
    margin-bottom: 3px;
}
.etape-desc {
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

# ── NAVIGATION ───────────────────────────────────────────
if st.button("← Hub"):
    st.switch_page("app.py")

st.markdown("""
<div style="font-family:'Playfair Display',serif;font-size:32px;
            font-weight:700;color:#4A3833;margin-bottom:4px;">
    📖 Rédaction Ebook
</div>
<div style="font-family:'Lora',serif;font-size:14px;color:#8C5A49;
            font-style:italic;margin-bottom:24px;">
    L'équipe travaille en chaîne — de la stratégie à la mise en page.
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── FORMULAIRE ───────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    sujet = st.text_input(
        "Sujet de l'ebook *",
        placeholder="ex : Déléguer sans culpabiliser"
    )
    dynamique = st.selectbox(
        "Dynamique lectrice *",
        ["Maman leader en tension — surcharge, fatigue, arbitrages complexes",
         "Maman leader en optimisation — structuration, performance durable"]
    )
with col2:
    format_ebook = st.selectbox(
        "Format *",
        ["Guide gratuit — miroir émotionnel",
         "Ebook 9,90€ — desserrage concret",
         "Ebook 24,90€ — stabilisation durable"]
    )
    nb_chapitres = st.slider("Nombre de chapitres", 3, 10, 5)

contexte_supp = st.text_area(
    "Contexte supplémentaire (optionnel)",
    placeholder="Brief spécifique, contraintes particulières, angle souhaité...",
    height=80
)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── ÉTAPES VISUELLES ─────────────────────────────────────
st.markdown("### Le flux de production")

etapes = [
    ("marketing",  "1. Stratégie marketing",
     "Analyse marché, positionnement, promesse de l'ebook"),
    ("editoriale", "2. Architecture éditoriale",
     "Sommaire, objectifs par chapitre, messages clés"),
    ("redactrice", "3. Rédaction",
     "Texte complet, ton mature et introspectif"),
    ("da",         "4. Direction artistique",
     "Identité visuelle, palette, direction couverture"),
    ("maquette",   "5. Mise en page",
     "Structure page par page, gabarits PDF/EPUB"),
]

cols_e = st.columns(5)
for col, (key, titre, desc) in zip(cols_e, etapes):
    with col:
        img = charger_image(key)
        if img:
            st.image(img, width=70)
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-family:'Playfair Display',serif;
                        font-size:12px;font-weight:600;
                        color:#4A3833;margin:6px 0 2px;">
                {titre}
            </div>
            <div style="font-family:'Lora',serif;font-size:10px;
                        color:#8C5A49;font-style:italic;">
                {desc}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# ── LANCEMENT ────────────────────────────────────────────
if st.button("📖 Lancer la production de l'ebook",
             type="primary", use_container_width=True):
    if not sujet:
        st.error("Merci d'indiquer le sujet de l'ebook.")
    else:
        contexte_global = f"""
Maison éditoriale : Maman & Leader
Sujet de l'ebook : {sujet}
Format : {format_ebook}
Dynamique lectrice : {dynamique}
Nombre de chapitres : {nb_chapitres}
Contexte supplémentaire : {contexte_supp if contexte_supp else 'Aucun'}
"""

        resultats = {}

        # ── ÉTAPE 1 — Marketing ──────────────────────────
        st.markdown("---")
        with st.expander("📊 Étape 1 — Directrice Marketing", expanded=True):
            col_img, col_txt = st.columns([1, 4])
            with col_img:
                img = charger_image("marketing")
                if img:
                    st.image(img, width=60)
            with col_txt:
                st.markdown("**Directrice Marketing** — Stratégie en cours...")
                with st.spinner("Analyse du marché et positionnement..."):
                    instruction_mkt = f"""
{prompts['marketing']['taches']}

Applique cette analyse au projet suivant :
Sujet : {sujet}
Format : {format_ebook}
Dynamique : {dynamique}
Produis le positionnement stratégique complet de cet ebook.
"""
                    resultats["marketing"] = lancer_agent(
                        "marketing", instruction_mkt, prompts
                    )
                st.success("✦ Stratégie marketing produite")
                st.markdown(resultats["marketing"])

        # ── ÉTAPE 2 — Éditoriale ─────────────────────────
        with st.expander("📚 Étape 2 — Directrice Éditoriale", expanded=True):
            col_img, col_txt = st.columns([1, 4])
            with col_img:
                img = charger_image("editoriale")
                if img:
                    st.image(img, width=60)
            with col_txt:
                st.markdown("**Directrice Éditoriale** — Architecture en cours...")
                with st.spinner("Structure éditoriale en cours..."):
                    instruction_ed = f"""
{prompts['editoriale']['taches']}

Projet : {sujet}
Format : {format_ebook}
Nombre de chapitres : {nb_chapitres}
Dynamique : {dynamique}

Stratégie marketing validée :
{resultats['marketing'][:500]}

Produis le sommaire complet et les objectifs par chapitre.
"""
                    resultats["editoriale"] = lancer_agent(
                        "editoriale", instruction_ed, prompts,
                        contexte_global
                    )
                st.success("✦ Architecture éditoriale produite")
                st.markdown(resultats["editoriale"])

        # ── ÉTAPE 3 — Rédactrice ─────────────────────────
        with st.expander("✍️ Étape 3 — Rédactrice", expanded=True):
            col_img, col_txt = st.columns([1, 4])
            with col_img:
                img = charger_image("redactrice")
                if img:
                    st.image(img, width=60)
            with col_txt:
                st.markdown("**Rédactrice** — Rédaction en cours...")
                with st.spinner("Rédaction du contenu..."):
                    instruction_red = f"""
{prompts['redactrice']['taches']}

Sur la base de cette architecture éditoriale :
{resultats['editoriale'][:800]}

Rédige l'introduction complète de l'ebook et le premier chapitre
complet. Ton mature, introspectif, dense mais respirant.
Aucun commentaire méthodologique — uniquement le texte final.
"""
                    resultats["redactrice"] = lancer_agent(
                        "redactrice", instruction_red, prompts,
                        contexte_global
                    )
                st.success("✦ Introduction et chapitre 1 rédigés")
                st.markdown(resultats["redactrice"])

        # ── ÉTAPE 4 — DA ─────────────────────────────────
        with st.expander("🎨 Étape 4 — Directrice Artistique", expanded=True):
            col_img, col_txt = st.columns([1, 4])
            with col_img:
                img = charger_image("da")
                if img:
                    st.image(img, width=60)
            with col_txt:
                st.markdown("**Directrice Artistique** — Direction visuelle...")
                with st.spinner("Direction artistique en cours..."):
                    instruction_da = f"""
{prompts['da']['taches']}

Pour l'ebook : {sujet}
Format : {format_ebook}
Dynamique : {dynamique}

Produis la direction artistique complète :
couverture, intérieur, système visuel cohérent.
"""
                    resultats["da"] = lancer_agent(
                        "da", instruction_da, prompts,
                        contexte_global
                    )
                st.success("✦ Direction artistique produite")
                st.markdown(resultats["da"])

        # ── ÉTAPE 5 — Maquette ───────────────────────────
        with st.expander("📐 Étape 5 — Maquettiste", expanded=True):
            col_img, col_txt = st.columns([1, 4])
            with col_img:
                img = charger_image("maquette")
                if img:
                    st.image(img, width=60)
            with col_txt:
                st.markdown("**Maquettiste** — Mise en page en cours...")
                with st.spinner("Structure page par page..."):
                    instruction_maq = f"""
{prompts['maquette']['taches']}

Sur la base de :
- Architecture : {resultats['editoriale'][:400]}
- Direction artistique : {resultats['da'][:400]}

Produis la structure de mise en page page par page
pour l'introduction et le premier chapitre.
Format PDF lecture écran et EPUB 3.
"""
                    resultats["maquette"] = lancer_agent(
                        "maquette", instruction_maq, prompts,
                        contexte_global
                    )
                st.success("✦ Mise en page produite")
                st.markdown(resultats["maquette"])

        # ── COMPILATION FINALE ───────────────────────────
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### ✦ Dossier ebook complet")

        livrable_complet = f"""
═══════════════════════════════════════════════════
DOSSIER EBOOK — {sujet.upper()}
Maman & Leader — Maison éditoriale premium
{datetime.datetime.now().strftime("%d/%m/%Y")}
═══════════════════════════════════════════════════

FORMAT : {format_ebook}
DYNAMIQUE : {dynamique}
CHAPITRES : {nb_chapitres}

───────────────────────────────────────────────────
1. STRATÉGIE MARKETING
───────────────────────────────────────────────────
{resultats['marketing']}

───────────────────────────────────────────────────
2. ARCHITECTURE ÉDITORIALE
───────────────────────────────────────────────────
{resultats['editoriale']}

───────────────────────────────────────────────────
3. RÉDACTION — INTRODUCTION & CHAPITRE 1
───────────────────────────────────────────────────
{resultats['redactrice']}

───────────────────────────────────────────────────
4. DIRECTION ARTISTIQUE
───────────────────────────────────────────────────
{resultats['da']}

───────────────────────────────────────────────────
5. MISE EN PAGE
───────────────────────────────────────────────────
{resultats['maquette']}
"""
        sauvegarder_livrable(sujet, "Ebook", livrable_complet)
        from notion_sync import envoyer_notion
        import datetime as dt
        ok, msg = envoyer_notion(
            titre=sujet,
            type_mission="Ebook",
            contenu=livrable_complet,
            date_str=dt.datetime.now().strftime("%Y-%m-%d")
        )
        if ok:
            st.success("✦ Livrable envoyé dans Notion !")
        else:
            st.warning(f"Notion : {msg}")

        st.success("✦ Dossier ebook complet généré et sauvegardé !")
        st.download_button(
            "⬇️ Télécharger le dossier complet",
            data=livrable_complet,
            file_name=f"ebook_{sujet.replace(' ','_')}.txt",
            mime="text/plain",
            use_container_width=True
        )