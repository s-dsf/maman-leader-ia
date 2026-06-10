import streamlit as st
import os, json, datetime, requests, re, calendar
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Maman & Leader — Calendrier Social",
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

def envoyer_airtable(posts):
    token = os.getenv("AIRTABLE_TOKEN")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_id = os.getenv("AIRTABLE_TABLE_ID")
    if not token or not base_id or not table_id:
        return False, "Cles Airtable manquantes dans .env"
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    erreurs = []
    succes = 0
    for i in range(0, len(posts), 10):
        batch = posts[i:i+10]
        records = []
        for post in batch:
            fields = {}
            for key in ["Date","Support","Pilier","Angle","Hook",
                        "ContenuPost","Caption","BriefCouleur",
                        "BriefAlignement","BriefBloc","BriefAmbiance"]:
                if key in post:
                    fields[key] = str(post[key])
            fields["Statut production"] = "Fait"
            records.append({"fields": fields})
        try:
            resp = requests.post(url, headers=headers,
                                 json={"records": records}, timeout=30)
            if resp.status_code == 200:
                succes += len(batch)
            else:
                erreurs.append(f"Batch {i//10+1}: {resp.text[:200]}")
        except Exception as e:
            erreurs.append(str(e))
    if erreurs:
        return False, f"{succes} posts envoyes. Erreurs : {'; '.join(erreurs)}"
    return True, f"{succes} posts envoyes dans Airtable"

def generer_semaine(client, date_debut, date_fin, intention_data):
    prompt = f"""
Tu generes un calendrier editorial Instagram pour Maman & Leader.

DONNEES :
Intention marketing : {intention_data.get('Intentions marketing', '')}
Phase marketing : {intention_data.get('Phase marketing', 'Consolidation')}
Pilier dominant : {intention_data.get('Pilier dominant', 'A tes cotes')}
Date debut : {date_debut}
Date fin : {date_fin}

POSITIONNEMENT :
Maison editoriale pour femmes dirigeantes et meres.
Leadership feminin incarne. Responsabilite sans durete.
Structure sans rigidite. Douceur sans effacement.
Ton : sobre, stable, introspectif, non injonctif.

RYTHME :
- 5 publications principales par semaine (Reel ou Carrousel)
- Minimum 2 Reels par semaine
- Stories quotidiennes obligatoires
- Maximum 1 Reel par jour, 1 Carrousel par jour

STRUCTURE : Une entree par jour entre {date_debut} et {date_fin} inclus.
Chaque jour : minimum 1 Story. Publications en complement.

REPARTITION : 60% Identification / 20% Conscience / 10% Stabilisation / 10% Invitation

HOOKS : Courts, concrets, varies.
Formats possibles : "Tu es celle qu'on appelle quand..." / "Ce qui fatigue vraiment..." / "5 signes que..." / "Personne ne voit..." / "Pourquoi tu es epuisee meme quand..."

STRUCTURE PAR SUPPORT :
Carrousel : Slide 1 / Slide 2 / Slide 3 / Slide 4 / Slide 5. Min 4 slides. Max 7.
Story : Story 1 / Story 2 / Story 3 / Story 4. Min 3. Max 6.
Reel : Plan / Texte 1 / Silence / Texte 2 / Texte final.

CAPTION : Entre 400 et 600 caracteres maximum. Concise mais impactante. Mots-cles : charge mentale, maman active, fatigue decisionnelle, leadership feminin. Question ouverte en fin.

VALEURS AUTORISEES UNIQUEMENT :
Support : Reel / Story / Carrousel
Pilier : A tes cotes / Structurer sans s'epuiser
Angle : Identification / Conscience / Desserrage / Invitation

FORMAT : Tableau JSON valide uniquement. Commence par [ termine par ].
Aucun texte avant ou apres.
Chaque element : Date, Support, Pilier, Angle, Hook, ContenuPost, Caption, BriefCouleur, BriefAlignement, BriefBloc, BriefAmbiance
"""
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    reponse = msg.content[0].text.strip()
    if "```" in reponse:
        reponse = re.sub(r'```json?\s*', '', reponse)
        reponse = re.sub(r'```', '', reponse)
    reponse = reponse.strip()
    start = reponse.find('[')
    end = reponse.rfind(']') + 1
    if start >= 0 and end > start:
        return json.loads(reponse[start:end])
    return json.loads(reponse)

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
.badge-support {
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
    Calendrier Social Mensuel
</div>
<div style="font-family:'Lora',serif;font-size:14px;color:#8C5A49;
            font-style:italic;margin-bottom:24px;">
    La Directrice Marketing definit l'intention — le calendrier est genere automatiquement
</div>
""", unsafe_allow_html=True)

st.markdown("<hr/>", unsafe_allow_html=True)

# ── FORMULAIRE ───────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    mois = st.selectbox("Mois *", [
        "Janvier","Fevrier","Mars","Avril","Mai","Juin",
        "Juillet","Aout","Septembre","Octobre","Novembre","Decembre"
    ])
    annee = st.number_input("Annee *", min_value=2025,
                             max_value=2030,
                             value=datetime.datetime.now().year)
with col2:
    contexte_supp = st.text_area(
        "Contexte du mois (optionnel)",
        placeholder="Lancement ebook, evenement, periode particuliere...",
        height=100
    )

st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown("### Le flux de production")

cols_f = st.columns(2)
for col, (key, label, desc) in zip(cols_f, [
    ("marketing", "1. Directrice Marketing",
     "Definit intention, phase et pilier dominant du mois"),
    ("redactrice", "2. Generation calendrier",
     "Calendrier complet jour par jour avec hooks, captions et briefs"),
]):
    with col:
        img = charger_image(key)
        if img:
            st.image(img, width=70)
        st.markdown(f"""
        <div style="font-family:'Playfair Display',serif;font-size:13px;
                    font-weight:600;color:#4A3833;margin:6px 0 2px;">{label}</div>
        <div style="font-family:'Lora',serif;font-size:11px;
                    color:#8C5A49;font-style:italic;">{desc}</div>
        """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

if st.button("Generer le calendrier du mois",
             type="primary", use_container_width=True):

    mois_num = ["Janvier","Fevrier","Mars","Avril","Mai","Juin",
                 "Juillet","Aout","Septembre","Octobre","Novembre",
                 "Decembre"].index(mois) + 1
    nb_jours = calendar.monthrange(int(annee), mois_num)[1]
    date_debut = f"{int(annee):04d}-{mois_num:02d}-01"
    date_fin = f"{int(annee):04d}-{mois_num:02d}-{nb_jours:02d}"

    # ── ETAPE 1 — Marketing ──────────────────────────────
    with st.expander("Etape 1 — Directrice Marketing", expanded=True):
        col_i, col_t = st.columns([1, 4])
        with col_i:
            img = charger_image("marketing")
            if img:
                st.image(img, width=60)
        with col_t:
            with st.spinner("Analyse marketing en cours..."):
                instr_mkt = f"""
Tu es la Directrice Marketing de Maman & Leader.
Definis l'intention marketing pour {mois} {annee}.
Contexte : {contexte_supp if contexte_supp else 'Aucun'}

Reponds UNIQUEMENT avec ce JSON exact (rien d'autre) :
{{
  "Intentions marketing": "...",
  "Phase marketing": "Installation",
  "Pilier dominant": "A tes cotes"
}}

Phase doit etre : Installation ou Consolidation ou Stabilisation
Pilier doit etre : A tes cotes ou Structurer sans s'epuiser
"""
            import anthropic as _ant
            _client = _ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            _msg = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1000,
                messages=[{"role": "user", "content": instr_mkt}]
            )
            reponse_mkt = _msg.content[0].text

            try:
                json_match = re.search(r'\{[^{}]+\}', reponse_mkt,
                                       re.DOTALL)
                if json_match:
                    intention_data = json.loads(json_match.group())
                else:
                    intention_data = {
                        "Intentions marketing": reponse_mkt[:200],
                        "Phase marketing": "Consolidation",
                        "Pilier dominant": "A tes cotes"
                    }
            except Exception:
                intention_data = {
                    "Intentions marketing": reponse_mkt[:200],
                    "Phase marketing": "Consolidation",
                    "Pilier dominant": "A tes cotes"
                }

            st.success("Intention marketing definie")
            c1, c2, c3 = st.columns(3)
            c1.metric("Phase", intention_data.get("Phase marketing","—"))
            c2.metric("Pilier", intention_data.get("Pilier dominant","—"))
            c3.metric("Periode", f"{date_debut} -> {date_fin}")
            st.caption(intention_data.get("Intentions marketing","")[:300])

    # ── ETAPE 2 — Calendrier par semaines ────────────────
    with st.expander("Etape 2 — Generation du calendrier",
                     expanded=True):
        col_i, col_t = st.columns([1, 4])
        with col_i:
            img = charger_image("redactrice")
            if img:
                st.image(img, width=60)
        with col_t:
            import anthropic as ant_module
            client_ant = ant_module.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

            # Découper en semaines
            tous_les_jours = []
            d = datetime.date(int(annee), mois_num, 1)
            d_fin = datetime.date(int(annee), mois_num, nb_jours)
            while d <= d_fin:
                tous_les_jours.append(d)
                d += datetime.timedelta(days=1)

            semaines = []
            for i in range(0, len(tous_les_jours), 7):
                semaines.append(tous_les_jours[i:i+7])

            tous_posts = []
            progress = st.progress(0)

            for idx, semaine in enumerate(semaines):
                ds = semaine[0].strftime("%Y-%m-%d")
                df = semaine[-1].strftime("%Y-%m-%d")
                st.caption(f"Semaine {idx+1}/{len(semaines)} : {ds} -> {df}")
                progress.progress(int((idx / len(semaines)) * 90))
                try:
                    posts_s = generer_semaine(
                        client_ant, ds, df, intention_data
                    )
                    tous_posts.extend(posts_s)
                    st.caption(f"  -> {len(posts_s)} posts generes")
                except Exception as e:
                    st.warning(f"Semaine {idx+1} erreur : {str(e)[:100]}")

            progress.progress(100)

            if tous_posts:
                st.success(
                    f"{len(tous_posts)} entrees generees pour {mois} {annee}"
                )
                st.session_state["calendrier_posts"] = tous_posts
                st.session_state["calendrier_mois"] = f"{mois} {annee}"
            else:
                st.error("Aucun post genere")
                st.session_state["calendrier_posts"] = []

# ── AFFICHAGE ─────────────────────────────────────────────
if st.session_state.get("calendrier_posts"):
    posts = st.session_state["calendrier_posts"]

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown(
        f"### Calendrier — {st.session_state.get('calendrier_mois','')}"
    )

    nb_reels = len([p for p in posts if p.get("Support") == "Reel"])
    nb_carr  = len([p for p in posts if p.get("Support") == "Carrousel"])
    nb_story = len([p for p in posts if p.get("Support") == "Story"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(posts))
    c2.metric("Reels", nb_reels)
    c3.metric("Carrousels", nb_carr)
    c4.metric("Stories", nb_story)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Envoyer dans Airtable",
                     type="primary", use_container_width=True):
            with st.spinner("Envoi en cours..."):
                ok, msg = envoyer_airtable(posts)
            if ok:
                st.success(f"✦ {msg}")
            else:
                st.error(msg)
    with col_b2:
        st.download_button(
            "Telecharger JSON",
            data=json.dumps(posts, ensure_ascii=False, indent=2),
            file_name=f"calendrier_{st.session_state.get('calendrier_mois','')}.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)

    for post in posts:
        support = post.get("Support", "")
        with st.expander(
            f"📅 {post.get('Date','—')} — {support} — {post.get('Hook','')[:50]}"
        ):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <span class="badge-support">{support}</span>
                <span class="badge-support">{post.get('Pilier','')}</span>
                <span class="badge-support">{post.get('Angle','')}</span>
                """, unsafe_allow_html=True)
                st.markdown(f"**Hook :** {post.get('Hook','')}")
                st.markdown("**Contenu :**")
                st.text(post.get("ContenuPost",""))
            with col_b:
                st.markdown("**Caption :**")
                st.text(post.get("Caption","")[:600] + "...")
                st.markdown("**Brief visuel :**")
                st.caption(f"Couleur : {post.get('BriefCouleur','')}")
                st.caption(f"Alignement : {post.get('BriefAlignement','')}")
                st.caption(f"Bloc : {post.get('BriefBloc','')}")
                st.caption(f"Ambiance : {post.get('BriefAmbiance','')}")