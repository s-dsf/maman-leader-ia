import streamlit as st
import os, json, datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Nouveau projet — Maison d'édition IA",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
[data-testid="collapsedControl"] { display: none; }
[data-testid="stSidebar"] { display: none; }
</style>
""", unsafe_allow_html=True)

def avatar_url(seed, bg="b6e3f4"):
    return (f"https://api.dicebear.com/9.x/personas/svg"
            f"?seed={seed}&backgroundColor={bg}&radius=50")

def charger_prompts():
    with open("prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def sauvegarder_dossier(titre, auteur, genre, synopsis, resultat):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "id": ts, "titre": titre, "auteur": auteur,
        "genre": genre, "synopsis": synopsis,
        "resultat": str(resultat),
        "date": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
    }
    nom = f"{ts}_{titre[:20].replace(' ','_')}.json"
    with open(Path("historique") / nom, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

if st.button("← Retour au hub"):
    st.switch_page("app.py")

st.title("✨ Nouveau projet éditorial")
st.caption("L'équipe complète va travailler en chaîne pour produire ton dossier.")

prompts = charger_prompts()

col1, col2 = st.columns(2)
with col1:
    titre  = st.text_input("Titre *", placeholder="Les Jardins de Sel")
    auteur = st.text_input("Auteur *", placeholder="Marie Lescot")
with col2:
    genre = st.selectbox("Genre *", [
        "Roman littéraire", "Roman policier", "Roman historique",
        "Science-fiction", "Fantasy", "Essai", "Biographie",
        "Roman jeunesse", "Bande dessinée", "Autre"
    ])

synopsis = st.text_area("Synopsis *", height=120,
    placeholder="Décris l'histoire en quelques phrases...")

st.divider()
st.caption("L'équipe qui va travailler :")

agents_info = [
    ("marketing","Sophie"), ("redacteur","Marc"),
    ("da","Léa"), ("maquette","Thomas"), ("chef","Claire")
] + [(a["id"], a["nom"]) for a in prompts.get("agents_custom", [])]

cols = st.columns(len(agents_info))
for col, (key, nom) in zip(cols, agents_info):
    with col:
        p = prompts[key] if key in prompts else next(
            x for x in prompts["agents_custom"] if x["id"] == key
        )
        st.image(avatar_url(
            p.get("avatar_seed", nom),
            p.get("avatar_bg", "b6e3f4")
        ), width=60)
        st.caption(f"**{nom}**")

st.divider()

if st.button("🚀 Lancer l'équipe", type="primary", use_container_width=True):
    if not titre or not auteur or not synopsis:
        st.error("Merci de remplir tous les champs *")
    else:
        from crewai import Agent, Task, Crew, Process, LLM
        from rag import rechercher

        claude = LLM(
            model="anthropic/claude-sonnet-4-6",
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        cols2 = st.columns(len(agents_info))
        ph = {}
        for col, (key, nom) in zip(cols2, agents_info):
            with col:
                p = prompts[key] if key in prompts else next(
                    x for x in prompts["agents_custom"] if x["id"] == key
                )
                st.image(avatar_url(
                    p.get("avatar_seed", nom),
                    p.get("avatar_bg", "b6e3f4")
                ), width=50)
                ph[key] = st.empty()
                ph[key].caption(f"**{nom}** ⏳")

        progress = st.progress(0)
        status = st.empty()
        status.info("🚀 Démarrage...")

        try:
            def make_agent(key):
                p = prompts[key] if key in prompts else next(
                    a for a in prompts["agents_custom"] if a["id"] == key
                )
                ctx = rechercher(key, n=3)
                bs = p["backstory"] + (f"\n\nRÉFÉRENCES :\n{ctx}" if ctx else "")
                return Agent(
                    role=p["role"],
                    goal="Produire un travail éditorial de qualité",
                    backstory=bs,
                    verbose=False,
                    llm=claude,
                    allow_delegation=(key == "chef")
                )

            ctx_livre = f'Livre : "{titre}" ({genre}) de {auteur}.\nSynopsis : {synopsis}'

            ph["marketing"].caption("**Sophie** 🔵")
            progress.progress(10)
            t_mkt = Task(
                description=f"{ctx_livre}\n\n{prompts['marketing']['taches']}",
                agent=make_agent("marketing"),
                expected_output="Document marketing"
            )
            ph["redacteur"].caption("**Marc** 🔵")
            progress.progress(25)
            t_red = Task(
                description=f"{ctx_livre}\n\n{prompts['redacteur']['taches']}",
                agent=make_agent("redacteur"),
                expected_output="Textes éditoriaux"
            )
            ph["da"].caption("**Léa** 🔵")
            progress.progress(40)
            t_da = Task(
                description=f"{ctx_livre}\n\n{prompts['da']['taches']}",
                agent=make_agent("da"),
                context=[t_mkt, t_red],
                expected_output="Brief artistique"
            )
            ph["maquette"].caption("**Thomas** 🔵")
            progress.progress(55)
            t_maq = Task(
                description=f"{ctx_livre}\n\n{prompts['maquette']['taches']}",
                agent=make_agent("maquette"),
                context=[t_da],
                expected_output="Spécifications maquette"
            )
            ph["chef"].caption("**Claire** 🔵")
            progress.progress(70)
            t_syn = Task(
                description=f"{ctx_livre}\n\n{prompts['chef']['taches']}",
                agent=make_agent("chef"),
                context=[t_mkt, t_red, t_da, t_maq],
                expected_output="Dossier complet"
            )

            equipe = Crew(
                agents=[make_agent(k) for k, _ in agents_info],
                tasks=[t_mkt, t_red, t_da, t_maq, t_syn],
                process=Process.sequential,
                verbose=False
            )
            resultat = equipe.kickoff()
            progress.progress(100)

            for key, nom in agents_info:
                ph[key].caption(f"**{nom}** ✅")

            status.success("✅ Dossier généré !")
            sauvegarder_dossier(titre, auteur, genre, synopsis, resultat)

            st.subheader("📄 Dossier éditorial")
            st.markdown(str(resultat))
            st.download_button(
                "⬇️ Télécharger",
                data=str(resultat),
                file_name=f"dossier_{titre.replace(' ','_')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        except Exception as e:
            progress.progress(0)
            status.error(f"Erreur : {str(e)}")