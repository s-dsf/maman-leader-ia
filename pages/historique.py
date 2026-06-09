import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Historique", page_icon="📁",
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="collapsedControl"]{display:none;}
[data-testid="stSidebar"]{display:none;}
</style>""", unsafe_allow_html=True)

if st.button("← Retour au hub"):
    st.switch_page("app.py")

st.title("📁 Historique des dossiers")

dossiers = []
for f in sorted(Path("historique").glob("*.json"), reverse=True):
    with open(f,"r",encoding="utf-8") as fh:
        dossiers.append(json.load(fh))

if not dossiers:
    st.info("Aucun dossier pour l'instant.")
else:
    st.metric("Total dossiers produits", len(dossiers))
    for d in dossiers:
        with st.expander(f"📖 **{d['titre']}** — {d['auteur']} · {d['date']}"):
            st.caption(f"Genre : {d['genre']}")
            st.caption(f"Synopsis : {d['synopsis'][:200]}...")
            st.markdown(d["resultat"])
            st.download_button("⬇️ Télécharger",
                data=d["resultat"],
                file_name=f"dossier_{d['titre'].replace(' ','_')}.txt",
                mime="text/plain", key=f"dl_{d['id']}")