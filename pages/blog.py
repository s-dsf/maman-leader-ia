import streamlit as st
import os, json, datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Blog & Audit",
    page_icon="✍️",
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
        "date": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    }
    Path("historique").mkdir(exist_ok=True)
    with open(Path("historique") /
              f"{ts}_{titre[:20].replace(' ','_')}.json",
              "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
        goal="Produire un livrable premium aligné Maman & Leader",
        backstory=backstory,
        verbose=False,
        llm=claude
    )
    desc = f"{contexte}\n\n{instruction}" if contexte else instruction
    task = Task(
        description=desc,
        agent=agent,
        expected_output="Livrable structuré, professionnel, aligné Maman & Leader"
    )
    crew = Crew(agents=[agent], tasks=[task], verbose=False)
    return str(crew.kickoff())

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
    ✍️ Blog & Audit
</div>
<div style="font-family:'Lora',serif;font-size:14px;color:#8C5A49;
            font-style:italic;margin-bottom:24px;">
    Articles de blog premium · Audit éditorial et visuel du site
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

tab_blog, tab_audit = st.tabs(["✍️ Article de blog", "🔍 Audit site"])

# ══════════════════════════════════════════
# TAB BLOG
# ══════════════════════════════════════════
with tab_blog:
    st.markdown("### Article de blog")
    st.caption("Un article long, mature, aligné avec le positionnement Maman & Leader.")

    col1, col2 = st.columns(2)
    with col1:
        sujet_blog = st.text_input(
            "Sujet de l'article *",
            placeholder="ex : Comment déléguer sans perdre le fil"
        )
        angle_blog = st.selectbox(
            "Angle éditorial *",
            ["Identification — la lectrice se reconnaît",
             "Mise en conscience — comprendre le mécanisme",
             "Desserrage — un premier mouvement concret",
             "Article complet — les 4 phases"]
        )
    with col2:
        longueur = st.selectbox(
            "Longueur *",
            ["Article court (500-800 mots)",
             "Article moyen (1000-1500 mots)",
             "Article long (2000-2500 mots)"]
        )
        pilier_blog = st.selectbox(
            "Pilier *",
            ["À tes côtés — apaisant, introspectif",
             "Structurer sans s'épuiser — stable, ancré"]
        )

    contexte_blog = st.text_area(
        "Contexte supplémentaire", height=80,
        placeholder="Angle spécifique, lien avec un ebook, événement..."
    )

    cols_flux = st.columns(3)
    for col, (key, label) in zip(cols_flux, [
        ("marketing", "1. Angle SEO"),
        ("editoriale", "2. Plan article"),
        ("redactrice", "3. Rédaction")
    ]):
        with col:
            img = charger_image(key)
            if img:
                st.image(img, width=60)
            st.caption(label)

    st.markdown("<br/>", unsafe_allow_html=True)

    if st.button("✍️ Rédiger l'article",
                 type="primary", use_container_width=True,
                 key="btn_blog"):
        if not sujet_blog:
            st.error("Merci d'indiquer le sujet.")
        else:
            ctx = f"""
Maison : Maman & Leader | Sujet : {sujet_blog}
Angle : {angle_blog} | Longueur : {longueur}
Pilier : {pilier_blog}
"""
            resultats_blog = {}

            with st.expander("📊 Angle SEO & stratégique", expanded=True):
                col_i, col_t = st.columns([1, 4])
                with col_i:
                    img = charger_image("marketing")
                    if img:
                        st.image(img, width=55)
                with col_t:
                    with st.spinner("Angle en cours..."):
                        resultats_blog["marketing"] = lancer_agent(
                            "marketing",
                            f"Définis l'angle stratégique et SEO pour un article de blog sur : {sujet_blog}. Angle : {angle_blog}. Pilier : {pilier_blog}. Identifie les mots-clés pertinents, la promesse de l'article, et le positionnement différenciant.",
                            prompts, ctx
                        )
                    st.success("✦ Angle défini")
                    st.markdown(resultats_blog["marketing"])

            with st.expander("📚 Plan de l'article", expanded=True):
                col_i, col_t = st.columns([1, 4])
                with col_i:
                    img = charger_image("editoriale")
                    if img:
                        st.image(img, width=55)
                with col_t:
                    with st.spinner("Plan en cours..."):
                        resultats_blog["editoriale"] = lancer_agent(
                            "editoriale",
                            f"Construis le plan détaillé d'un article de blog sur : {sujet_blog}. Longueur : {longueur}. Angle : {resultats_blog['marketing'][:300]}. Structure chaque section avec son objectif et ses messages clés.",
                            prompts, ctx
                        )
                    st.success("✦ Plan structuré")
                    st.markdown(resultats_blog["editoriale"])

            with st.expander("✍️ Article rédigé", expanded=True):
                col_i, col_t = st.columns([1, 4])
                with col_i:
                    img = charger_image("redactrice")
                    if img:
                        st.image(img, width=55)
                with col_t:
                    with st.spinner("Rédaction en cours..."):
                        resultats_blog["redactrice"] = lancer_agent(
                            "redactrice",
                            f"Rédige l'article complet sur : {sujet_blog}. Plan : {resultats_blog['editoriale'][:600]}. Longueur : {longueur}. Ton mature, introspectif, non démonstratif. Jamais motivationnel. Uniquement le texte final.",
                            prompts, ctx
                        )
                    st.success("✦ Article rédigé")
                    st.markdown(resultats_blog["redactrice"])

            livrable = f"""
ARTICLE DE BLOG — {sujet_blog.upper()}
Maman & Leader | {datetime.datetime.now().strftime("%d/%m/%Y")}
{'='*50}

ANGLE & SEO
{resultats_blog['marketing']}

PLAN
{resultats_blog['editoriale']}

ARTICLE COMPLET
{resultats_blog['redactrice']}
"""
            sauvegarder_livrable(sujet_blog, "Article Blog", livrable)
            from notion_sync import envoyer_notion
            import datetime as dt
            ok, msg = envoyer_notion(
                titre=sujet_blog,
                type_mission="Article Blog",
                contenu=livrable,
                date_str=dt.datetime.now().strftime("%Y-%m-%d")
            )
            if ok:
                st.success("✦ Livrable envoyé dans Notion !")
            else:
                st.warning(f"Notion : {msg}")
            st.success("✦ Article sauvegardé !")
            st.download_button(
                "⬇️ Télécharger l'article",
                data=livrable,
                file_name=f"blog_{sujet_blog.replace(' ','_')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_blog"
            )

# ══════════════════════════════════════════
# TAB AUDIT
# ══════════════════════════════════════════
with tab_audit:
    st.markdown("### Audit du site internet")
    st.caption("Analyse éditoriale et visuelle du site Maman & Leader.")

    url_site = st.text_input(
        "URL du site à auditer *",
        placeholder="https://mamanandleader.com"
    )

    elements_audit = st.multiselect(
        "Éléments à auditer *",
        ["Page d'accueil", "Pages ebooks", "Blog",
         "Page À propos", "Tunnel de vente",
         "Cohérence visuelle globale",
         "Alignement avec le positionnement éditorial"],
        default=["Page d'accueil",
                 "Cohérence visuelle globale",
                 "Alignement avec le positionnement éditorial"]
    )

    notes_audit = st.text_area(
        "Notes sur le site",
        height=120,
        placeholder="Décris les pages existantes, les contenus actuels..."
    )

    cols_audit = st.columns(3)
    for col, (key, label) in zip(cols_audit, [
        ("marketing", "1. Audit positionnement"),
        ("editoriale", "2. Audit éditorial"),
        ("da", "3. Audit visuel")
    ]):
        with col:
            img = charger_image(key)
            if img:
                st.image(img, width=60)
            st.caption(label)

    st.markdown("<br/>", unsafe_allow_html=True)

    if st.button("🔍 Lancer l'audit",
                 type="primary", use_container_width=True,
                 key="btn_audit"):
        if not notes_audit and not url_site:
            st.error("Merci de décrire le site ou d'indiquer l'URL.")
        else:
            ctx_audit = f"""
Maison : Maman & Leader
URL : {url_site if url_site else 'Non fournie'}
Éléments : {', '.join(elements_audit)}
Notes : {notes_audit}
"""
            resultats_audit = {}

            with st.expander("📊 Audit positionnement", expanded=True):
                col_i, col_t = st.columns([1, 4])
                with col_i:
                    img = charger_image("marketing")
                    if img:
                        st.image(img, width=55)
                with col_t:
                    with st.spinner("Audit marketing..."):
                        resultats_audit["marketing"] = lancer_agent(
                            "marketing",
                            f"Audite le positionnement marketing du site Maman & Leader. Éléments : {', '.join(elements_audit)}. Notes : {notes_audit}. Analyse la cohérence avec le positionnement éditorial. Forces, faiblesses, recommandations.",
                            prompts, ctx_audit
                        )
                    st.success("✦ Audit marketing produit")
                    st.markdown(resultats_audit["marketing"])

            with st.expander("📚 Audit éditorial", expanded=True):
                col_i, col_t = st.columns([1, 4])
                with col_i:
                    img = charger_image("editoriale")
                    if img:
                        st.image(img, width=55)
                with col_t:
                    with st.spinner("Audit éditorial..."):
                        resultats_audit["editoriale"] = lancer_agent(
                            "editoriale",
                            f"Audite le contenu éditorial du site Maman & Leader. Notes : {notes_audit}. Analyse la structure des textes, le ton, la progression Identification→Invitation. Recommandations concrètes.",
                            prompts, ctx_audit
                        )
                    st.success("✦ Audit éditorial produit")
                    st.markdown(resultats_audit["editoriale"])

            with st.expander("🎨 Audit visuel", expanded=True):
                col_i, col_t = st.columns([1, 4])
                with col_i:
                    img = charger_image("da")
                    if img:
                        st.image(img, width=55)
                with col_t:
                    with st.spinner("Audit visuel..."):
                        resultats_audit["da"] = lancer_agent(
                            "da",
                            f"Audite la cohérence visuelle du site Maman & Leader. Notes : {notes_audit}. Analyse palette, typographie, piliers visuels, cohérence globale. Recommandations précises.",
                            prompts, ctx_audit
                        )
                    st.success("✦ Audit visuel produit")
                    st.markdown(resultats_audit["da"])

            livrable_audit = f"""
AUDIT SITE — MAMAN & LEADER
{datetime.datetime.now().strftime("%d/%m/%Y")}
URL : {url_site}
{'='*50}

AUDIT POSITIONNEMENT
{resultats_audit['marketing']}

AUDIT ÉDITORIAL
{resultats_audit['editoriale']}

AUDIT VISUEL
{resultats_audit['da']}
"""
            sauvegarder_livrable(
                f"Audit site {datetime.datetime.now().strftime('%d/%m')}",
                "Audit Site", livrable_audit
            )
            from notion_sync import envoyer_notion
            import datetime as dt
            ok, msg = envoyer_notion(
                titre=f"Audit site {dt.datetime.now().strftime('%d/%m/%Y')}",
                type_mission="Audit Site",
                contenu=livrable_audit,
                date_str=dt.datetime.now().strftime("%Y-%m-%d")
            )
            if ok:
                st.success("✦ Audit envoyé dans Notion !")
            else:
                st.warning(f"Notion : {msg}")
            st.success("✦ Audit sauvegardé !")
            st.download_button(
                "⬇️ Télécharger l'audit",
                data=livrable_audit,
                file_name="audit_site_maman_leader.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_audit"
            )