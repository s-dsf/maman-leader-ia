import streamlit as st
import json
from pathlib import Path
from PIL import Image

st.set_page_config(
    page_title="Maman & Leader — Équipe IA",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def charger_prompts():
    with open("prompts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def charger_historique():
    dossiers = []
    for f in sorted(Path("historique").glob("*.json"), reverse=True):
        with open(f, "r", encoding="utf-8") as fh:
            dossiers.append(json.load(fh))
    return dossiers

def charger_image(key):
    chemin = Path(f"avatar_{key}.png")
    if chemin.exists():
        return Image.open(chemin)
    return None

prompts = charger_prompts()
historique = charger_historique()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');
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
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 44px;
    font-weight: 700;
    color: #4A3833;
    line-height: 1.15;
    margin-bottom: 8px;
}
.hero-accent { color: #C77A5C; font-style: italic; }
.hero-sub {
    font-family: 'Lora', serif;
    font-size: 15px;
    color: #8C5A49;
    margin-bottom: 28px;
    font-style: italic;
}
.agent-nom {
    font-family: 'Playfair Display', serif;
    font-size: 14px;
    font-weight: 600;
    color: #4A3833;
    margin: 8px 0 3px;
    text-align: center;
}
.agent-role {
    font-family: 'Lora', serif;
    font-size: 10px;
    color: #C77A5C;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
    text-align: center;
}
.badge {
    display: inline-block;
    background: #FAEAE3;
    color: #C77A5C;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 10px;
    font-family: 'Lora', serif;
    letter-spacing: 0.5px;
    border: 1px solid #EDD9CF;
}
.mission-card {
    background: #FFFFFF;
    border: 1px solid #EDD9CF;
    border-left: 3px solid #C77A5C;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 10px;
}
.mission-titre {
    font-family: 'Playfair Display', serif;
    font-size: 16px;
    font-weight: 600;
    color: #4A3833;
    margin-bottom: 3px;
}
.mission-desc {
    font-family: 'Lora', serif;
    font-size: 12px;
    color: #8C5A49;
    font-style: italic;
}
.stat-card {
    background: #FAEAE3;
    border-radius: 12px;
    padding: 14px 16px;
    text-align: center;
    border: 1px solid #EDD9CF;
}
.stat-val {
    font-family: 'Playfair Display', serif;
    font-size: 26px;
    font-weight: 700;
    color: #C77A5C;
    line-height: 1;
}
.stat-lab {
    font-family: 'Lora', serif;
    font-size: 10px;
    color: #8C5A49;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 4px;
}
.stButton > button {
    font-family: 'Lora', serif !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
.stButton > button[kind="primary"] {
    background-color: #C77A5C !important;
    border: none !important;
    color: #FBF8F6 !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #B05C44 !important;
}
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid #C77A5C !important;
    color: #C77A5C !important;
}
hr { border-color: #EDD9CF !important; opacity: 0.6 !important; }
.footer-ml {
    text-align: center;
    font-family: 'Lora', serif;
    font-size: 12px;
    color: #C77A5C;
    padding: 16px 0 8px;
    letter-spacing: 1px;
}
</style>
""", unsafe_allow_html=True)

# ── EN-TÊTE ──────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div class="hero-title">
        Maman <span class="hero-accent">&</span> Leader
    </div>
    <div class="hero-sub">
        Ton équipe éditoriale IA — disponible, alignée, prête.
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("✦ Nouveau projet", type="primary",
                     use_container_width=True):
            st.switch_page("pages/nouveau_projet.py")
    with c2:
        if st.button("📖 Ebook", use_container_width=True):
            st.switch_page("pages/ebooks.py")
    with c3:
        if st.button("✦ Social", use_container_width=True):
            st.switch_page("pages/social.py")
    with c4:
        if st.button("✦ Blog & Audit", use_container_width=True):
            st.switch_page("pages/blog.py")

    c5, c6 = st.columns(2)
    with c5:
        if st.button("🎨 Visuels", use_container_width=True):
            st.switch_page("pages/visuels.py")

    c7, c8 = st.columns(2)
    with c7:
        if st.button("✅ Validation posts", use_container_width=True):
            st.switch_page("pages/validation.py")

with col_h2:
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="stat-card"><div class="stat-val">5</div><div class="stat-lab">Agentes</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-card"><div class="stat-val">{len(historique)}</div><div class="stat-lab">Livrables</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-card"><div class="stat-val">24/7</div><div class="stat-lab">En ligne</div></div>', unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── L'ÉQUIPE ─────────────────────────────────────────────
st.markdown("### L'équipe")

agents_ordre = [
    ("marketing",  "Directrice Marketing",  "Stratégie & analyse"),
    ("editoriale", "Directrice Éditoriale", "Architecture & structure"),
    ("redactrice", "Rédactrice",            "Écriture longue premium"),
    ("da",         "Directrice Artistique", "Cohérence visuelle"),
    ("maquette",   "Maquettiste",           "Mise en page éditoriale"),
]

cols = st.columns(5)
for col, (key, nom, role_court) in zip(cols, agents_ordre):
    with col:
        img = charger_image(key)
        if img:
            st.image(img, width=120, use_container_width=False)
        else:
            st.markdown("""
            <div style="width:110px;height:110px;margin:0 auto;
                        border-radius:50%;background:#FAEAE3;
                        border:2px solid #EDD9CF;display:flex;
                        align-items:center;justify-content:center;
                        font-size:32px;">✦</div>
            """, unsafe_allow_html=True)
        st.markdown(f'<div class="agent-nom">{nom}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="agent-role">{role_court}</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-bottom:8px;">'
                    '<span class="badge">✦ Disponible</span></div>',
                    unsafe_allow_html=True)
        if st.button("Ouvrir", key=f"open_{key}",
                     use_container_width=True):
            st.session_state["agent_actif"] = key
            st.switch_page("pages/agent.py")

st.markdown("<hr/>", unsafe_allow_html=True)

# ── MISSIONS & LIVRABLES ─────────────────────────────────
col_m1, col_m2 = st.columns([1, 1])

with col_m1:
    st.markdown("### Missions")

    missions = [
        ("📖", "Rédaction Ebook",
         "De la stratégie à la mise en page complète",
         "pages/ebooks.py"),
        ("✦", "Contenus Social",
         "Instagram & Pinterest — relation et acquisition",
         "pages/social.py"),
        ("✍️", "Articles de Blog",
         "Rédaction longue pour le site",
         "pages/blog.py"),
        ("🔍", "Audit Site",
         "Analyse éditoriale et visuelle",
         "pages/audit_site.py"),
    ]

    for emoji, titre, desc, page in missions:
        st.markdown(f"""
        <div class="mission-card">
            <div class="mission-titre">{emoji} {titre}</div>
            <div class="mission-desc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Lancer — {titre}",
                     key=f"miss_{titre}",
                     use_container_width=True):
            st.switch_page(page)

with col_m2:
    st.markdown("### Derniers livrables")
    if historique:
        for d in historique[:4]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{d['titre']}**")
                    st.caption(
                        f"{d.get('type_mission','Livrable')} · {d['date']}"
                    )
                with c2:
                    st.download_button(
                        "⬇️",
                        data=d["resultat"],
                        file_name=f"{d['titre'].replace(' ','_')}.txt",
                        key=f"dl_{d['id']}",
                        mime="text/plain"
                    )
    else:
        st.markdown("""
        <div style="padding:48px 20px;text-align:center;">
            <div style="font-family:'Playfair Display',serif;
                        font-size:17px;color:#8C5A49;
                        margin-bottom:8px;font-style:italic;">
                Aucun livrable pour l'instant
            </div>
            <div style="font-family:'Lora',serif;
                        font-size:13px;color:#C77A5C;">
                Lance ton premier projet pour voir tes productions ici.
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("""
<div class="footer-ml">
    M A M A N  &  L E A D E R  ✦  Maison éditoriale premium
</div>
""", unsafe_allow_html=True)