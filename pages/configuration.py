import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Configuration", page_icon="⚙️",
                   layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
[data-testid="collapsedControl"]{display:none;}
[data-testid="stSidebar"]{display:none;}
</style>""", unsafe_allow_html=True)

def avatar_url(seed, bg="b6e3f4"):
    return f"https://api.dicebear.com/9.x/personas/svg?seed={seed}&backgroundColor={bg}&radius=50"

def charger_prompts():
    with open("prompts.json","r",encoding="utf-8") as f:
        return json.load(f)

def sauvegarder_prompts(p):
    with open("prompts.json","w",encoding="utf-8") as f:
        json.dump(p,f,ensure_ascii=False,indent=2)

if st.button("← Retour au hub"):
    st.switch_page("app.py")

st.title("⚙️ Configuration de l'équipe")
prompts = charger_prompts()

for key, label in [("marketing","Sophie"),("redacteur","Marc"),
                   ("da","Léa"),("maquette","Thomas"),("chef","Claire")]:
    with st.expander(f"✏️ {label} — {prompts[key]['role']}"):
        c1, c2 = st.columns([1,3])
        with c1:
            st.image(avatar_url(prompts[key].get("avatar_seed",key),
                                prompts[key].get("avatar_bg","b6e3f4")), width=80)
            prompts[key]["nom"] = st.text_input("Prénom",
                value=prompts[key]["nom"], key=f"nom_{key}")
            new_bg = st.color_picker("Couleur",
                value="#"+prompts[key].get("avatar_bg","b6e3f4"), key=f"bg_{key}")
            prompts[key]["avatar_bg"] = new_bg.lstrip("#")
        with c2:
            prompts[key]["role"] = st.text_input("Rôle",
                value=prompts[key]["role"], key=f"role_{key}")
            prompts[key]["backstory"] = st.text_area("Personnalité",
                value=prompts[key]["backstory"], height=100, key=f"bs_{key}")
            prompts[key]["taches"] = st.text_area("Tâches",
                value=prompts[key]["taches"], height=120, key=f"t_{key}")

st.divider()
st.subheader("➕ Ajouter un agent")
with st.expander("Nouvel agent"):
    n_nom = st.text_input("Prénom", placeholder="Jean")
    n_role = st.text_input("Rôle", placeholder="Attaché de presse")
    n_bs = st.text_area("Personnalité", height=80)
    n_t = st.text_area("Tâches", height=100)
    if st.button("✅ Ajouter", type="primary"):
        if n_nom and n_role and n_t:
            import uuid
            if "agents_custom" not in prompts:
                prompts["agents_custom"] = []
            prompts["agents_custom"].append({
                "id": f"custom_{uuid.uuid4().hex[:8]}",
                "nom": n_nom, "avatar_seed": n_nom,
                "avatar_bg": "ffd5dc", "role": n_role,
                "backstory": n_bs, "taches": n_t
            })
            sauvegarder_prompts(prompts)
            st.success(f"✅ {n_nom} ajouté !")
            st.rerun()

if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
    sauvegarder_prompts(prompts)
    st.success("✅ Sauvegardé !")