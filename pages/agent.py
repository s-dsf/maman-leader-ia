import streamlit as st
import json, os, datetime
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Agent",
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

def chat_avec_agent(agent_key, message, prompts):
    from crewai import Agent, Task, Crew, LLM
    from rag import rechercher
    if agent_key in prompts and agent_key != "agents_custom":
        p = prompts[agent_key]
    else:
        p = next((a for a in prompts.get("agents_custom", [])
                  if a["id"] == agent_key), None)
        if not p:
            return "Agent introuvable."
    rag_ctx = rechercher(message, n=3)
    backstory = p["backstory"]
    if rag_ctx:
        backstory += f"\n\nRÉFÉRENCES MAISON :\n{rag_ctx}"
    claude = LLM(
        model="anthropic/claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    agent = Agent(
        role=p["role"],
        goal="Répondre avec expertise dans ton domaine exclusif",
        backstory=backstory,
        verbose=False,
        llm=claude
    )
    task = Task(
        description=message,
        agent=agent,
        expected_output="Réponse structurée, professionnelle, alignée avec Maman & Leader"
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

.agent-nom {
    font-family: 'Playfair Display', serif;
    font-size: 22px;
    font-weight: 700;
    color: #4A3833;
    margin: 10px 0 4px;
}
.agent-role-label {
    font-family: 'Lora', serif;
    font-size: 11px;
    color: #C77A5C;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 12px;
}
.badge {
    display: inline-block;
    background: #FAEAE3;
    color: #C77A5C;
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 11px;
    font-family: 'Lora', serif;
    border: 1px solid #EDD9CF;
    margin: 2px;
}
.stat-ligne {
    display: flex;
    justify-content: space-between;
    padding: 7px 0;
    border-bottom: 1px solid #F2E8E3;
    font-size: 13px;
    font-family: 'Lora', serif;
    color: #6E5A52;
}
.stat-val {
    font-weight: 600;
    color: #C77A5C;
    font-family: 'Playfair Display', serif;
}

.suggestion-pill {
    display: inline-block;
    background: #FFFFFF;
    border: 1px solid #EDD9CF;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 12px;
    font-family: 'Lora', serif;
    color: #8C5A49;
    cursor: pointer;
    margin: 4px;
    transition: all 0.2s;
}
.suggestion-pill:hover {
    background: #FAEAE3;
    border-color: #C77A5C;
}

.nav-agent {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
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
.stChatMessage {
    background: #FFFFFF !important;
    border: 1px solid #F2E8E3 !important;
    border-radius: 12px !important;
}
hr { border-color: #EDD9CF !important; opacity: 0.5 !important; }
</style>
""", unsafe_allow_html=True)

prompts = charger_prompts()
historique = charger_historique()
agent_key = st.session_state.get("agent_actif", "marketing")

# Charger les données de l'agent
agents_base = ["marketing", "editoriale", "redactrice", "da", "maquette"]
if agent_key in agents_base:
    p = prompts.get(agent_key, prompts["marketing"])
else:
    p = next((a for a in prompts.get("agents_custom", [])
               if a["id"] == agent_key), prompts["marketing"])

# ── NAVIGATION ───────────────────────────────────────────
nav1, nav2 = st.columns([1, 5])
with nav1:
    if st.button("← Hub", use_container_width=True):
        st.switch_page("app.py")

with nav2:
    agents_nav = [
        ("marketing",  "Marketing"),
        ("editoriale", "Éditoriale"),
        ("redactrice", "Rédactrice"),
        ("da",         "Artistique"),
        ("maquette",   "Maquette"),
    ]
    nav_cols = st.columns(len(agents_nav))
    for col, (key, label) in zip(nav_cols, agents_nav):
        with col:
            img = charger_image(key)
            if img:
                st.image(img, width=44)
            is_active = (key == agent_key)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{key}",
                        use_container_width=True,
                        type=btn_type):
                st.session_state["agent_actif"] = key
                st.rerun()

st.markdown("<hr/>", unsafe_allow_html=True)

# ── LAYOUT PRINCIPAL ────────────────────────────────────
col_gauche, col_droite = st.columns([1, 2.8])

# ── COLONNE GAUCHE ───────────────────────────────────────
with col_gauche:
    with st.container(border=True):
        img = charger_image(agent_key)
        if img:
            st.image(img, width=160)

        st.markdown(f'<div class="agent-nom">{p["nom"]}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="agent-role-label">{p["role"]}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<span class="badge">✦ Disponible</span>'
            '<span class="badge">🌐 En ligne</span>',
            unsafe_allow_html=True
        )
        st.markdown("<br/>", unsafe_allow_html=True)

        # Stats
        nb_livrables = len(historique)
        st.markdown(f"""
        <div class="stat-ligne">
            <span>Livrables produits</span>
            <span class="stat-val">{nb_livrables}</span>
        </div>
        <div class="stat-ligne">
            <span>Disponibilité</span>
            <span class="stat-val">24/7</span>
        </div>
        <div class="stat-ligne">
            <span>Statut</span>
            <span class="stat-val">Active</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("**Spécialités :**")
        for ligne in p["taches"].split("\n")[:4]:
            if ligne.strip():
                st.caption(f"→ {ligne.strip()[:50]}")

        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("✦ Modifier cette agente",
                     use_container_width=True):
            st.switch_page("pages/configuration.py")

# ── COLONNE DROITE — Onglets ─────────────────────────────
with col_droite:
    tab_chat, tab_analytics, tab_fichiers, tab_historique = st.tabs([
        "💬 Chat", "📊 Analytics", "📂 Fichiers", "🕐 Historique"
    ])

    # ── TAB CHAT ─────────────────────────────────────────
    with tab_chat:
        chat_key = f"chat_{agent_key}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        if not st.session_state[chat_key]:
            st.markdown(f"""
            <div style="text-align:center;padding:32px 20px 16px;">
                <div style="font-family:'Playfair Display',serif;
                            font-size:20px;color:#4A3833;
                            margin-bottom:8px;">
                    Conversation avec {p['nom']}
                </div>
                <div style="font-family:'Lora',serif;font-size:13px;
                            color:#8C5A49;font-style:italic;
                            max-width:400px;margin:0 auto;">
                    {p['nom']} connaît ta maison éditoriale, ta charte
                    et ton positionnement. Pose-lui une question ou
                    choisis un point de départ.
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Suggestions par agent
            suggestions = {
                "marketing": [
                    "Analyse le marché des ebooks premium féminins",
                    "Quelle intention marketing pour ce mois ?",
                    "Idées de nouveaux ebooks Maman & Leader",
                ],
                "editoriale": [
                    "Structure un ebook sur la délégation sereine",
                    "Sommaire pour 'Maman leader en tension'",
                    "Messages clés pour femmes dirigeantes épuisées",
                ],
                "redactrice": [
                    "Rédige une introduction introspective",
                    "Texte d'identification pour femme surmenée",
                    "Chapitre sur la structure sans rigidité",
                ],
                "da": [
                    "Direction artistique couverture ebook",
                    "Palette et typographie pour pilier 'À tes côtés'",
                    "Système visuel Instagram Maman & Leader",
                ],
                "maquette": [
                    "Mise en page page d'ouverture ebook",
                    "Structure page chapitre pilier 2",
                    "Gabarit bloc OUTIL pour ebook PDF",
                ],
            }
            suggs = suggestions.get(agent_key, [
                "Comment puis-je t'aider ?",
                "Quel est ton rôle exact ?",
                "Lance un projet",
            ])

            st.markdown("<br/>", unsafe_allow_html=True)
            cols_s = st.columns(len(suggs))
            for col_s, sugg in zip(cols_s, suggs):
                with col_s:
                    if st.button(sugg, key=f"sugg_{sugg[:15]}",
                                 use_container_width=True):
                        st.session_state[chat_key].append(
                            {"role": "user", "content": sugg}
                        )
# Sauvegarde automatique dans l'historique
            import datetime, json
            from pathlib import Path
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            titre_conv = f"Chat {p['nom']} — {user_input[:30]}"
            data = {
                "id": ts,
                "titre": titre_conv,
                "auteur": "Maman & Leader",
                "genre": "Conversation",
                "type_mission": f"Chat — {p['nom']}",
                "synopsis": user_input[:100],
                "resultat": f"Question : {user_input}\n\nRéponse : {rep}",
                "date": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
            }
            Path("historique").mkdir(exist_ok=True)
            with open(Path("historique") / f"{ts}_chat_{p['nom'][:10]}.json",
                      "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                        with st.spinner(f"{p['nom']} réfléchit..."):
                            rep = chat_avec_agent(
                                agent_key, sugg, prompts
                            )
                        st.session_state[chat_key].append(
                            {"role": "assistant", "content": rep}
                        )
# Sauvegarde automatique dans l'historique
            import datetime, json
            from pathlib import Path
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            titre_conv = f"Chat {p['nom']} — {user_input[:30]}"
            data = {
                "id": ts,
                "titre": titre_conv,
                "auteur": "Maman & Leader",
                "genre": "Conversation",
                "type_mission": f"Chat — {p['nom']}",
                "synopsis": user_input[:100],
                "resultat": f"Question : {user_input}\n\nRéponse : {rep}",
                "date": datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
            }
            Path("historique").mkdir(exist_ok=True)
            with open(Path("historique") / f"{ts}_chat_{p['nom'][:10]}.json",
                      "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=2)
                        st.rerun()

        # Affichage conversation
        for msg in st.session_state[chat_key]:
            avatar = "🌸" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        # Saisie
        user_input = st.chat_input(
            f"Demandez à {p['nom']}..."
        )
        if user_input:
            st.session_state[chat_key].append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            with st.chat_message("assistant", avatar="🌸"):
                with st.spinner(f"{p['nom']} réfléchit..."):
                    rep = chat_avec_agent(
                        agent_key, user_input, prompts
                    )
                st.markdown(rep)
            st.session_state[chat_key].append(
                {"role": "assistant", "content": rep}
            )

        if st.session_state.get(chat_key):
            if st.button("🗑️ Effacer la conversation",
                         key="clear_chat"):
                st.session_state[chat_key] = []
                st.rerun()

    # ── TAB ANALYTICS ─────────────────────────────────────
    with tab_analytics:
        st.markdown(f"### Activité de {p['nom']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Livrables", len(historique))
        c2.metric("Disponibilité", "24/7")
        c3.metric("Statut", "Active ✦")
        c4.metric("Spécialité", p["role"][:15] + "...")

        st.markdown("<br/>", unsafe_allow_html=True)

        if historique:
            st.markdown("**Derniers projets traités :**")
            for d in historique[:5]:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{d['titre']}**")
                        st.caption(f"{d.get('genre','—')} · {d['date']}")
                    with c2:
                        st.caption(d.get("type_mission", "Livrable"))
                    with c3:
                        st.download_button(
                            "⬇️",
                            data=d["resultat"],
                            file_name=f"{d['titre'].replace(' ','_')}.txt",
                            key=f"ana_{d['id']}",
                            mime="text/plain"
                        )
        else:
            st.markdown("""
            <div style="padding:40px;text-align:center;
                        font-family:'Lora',serif;
                        color:#8C5A49;font-style:italic;">
                Aucun projet produit pour l'instant.
            </div>
            """, unsafe_allow_html=True)

    # ── TAB FICHIERS ──────────────────────────────────────
    with tab_fichiers:
        st.markdown("### Livrables produits")

        if historique:
            for d in historique:
                with st.expander(
                    f"✦ {d['titre']} — {d.get('auteur','—')} · {d['date']}"
                ):
                    col_i, col_d = st.columns([3, 1])
                    with col_i:
                        st.caption(
                            f"Type : {d.get('type_mission','Livrable')}"
                        )
                        st.caption(
                            f"Synopsis : {d.get('synopsis','—')[:150]}..."
                        )
                    with col_d:
                        st.download_button(
                            "⬇️ Télécharger",
                            data=d["resultat"],
                            file_name=f"{d['titre'].replace(' ','_')}.txt",
                            mime="text/plain",
                            key=f"fich_{d['id']}"
                        )
        else:
            st.markdown("""
            <div style="padding:40px;text-align:center;
                        font-family:'Lora',serif;
                        color:#8C5A49;font-style:italic;">
                Aucun fichier pour l'instant.
            </div>
            """, unsafe_allow_html=True)

    # ── TAB HISTORIQUE ────────────────────────────────────
    with tab_historique:
        st.markdown(f"### Historique des conversations avec {p['nom']}")
        chat_key = f"chat_{agent_key}"

        if st.session_state.get(chat_key):
            for i, msg in enumerate(
                reversed(st.session_state[chat_key])
            ):
                role_label = "Toi" if msg["role"] == "user" \
                    else p["nom"]
                icon = "👤" if msg["role"] == "user" else "✦"
                with st.container(border=True):
                    st.caption(f"{icon} **{role_label}**")
                    st.markdown(msg["content"][:300] +
                                ("..." if len(msg["content"]) > 300
                                 else ""))
        else:
            st.markdown("""
            <div style="padding:40px;text-align:center;
                        font-family:'Lora',serif;
                        color:#8C5A49;font-style:italic;">
                Aucune conversation pour l'instant.
            </div>
            """, unsafe_allow_html=True)