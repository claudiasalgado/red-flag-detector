import streamlit as st
import pandas as pd
import altair as alt
from google import genai
from datetime import datetime
import streamlit.components.v1 as components
import html as _html

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Red Flag Detector 🚩",
    page_icon="🚩",
    layout="wide"
)

if "page" not in st.session_state:
    st.session_state.page = "inicio"

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def stamp():
    return datetime.now().strftime("%H:%M")

def compute_score(a):
    puntos_dict = {
        "Categoría": ["Comunicación", "Ego/Vibe", "Modales", "Factor Location"],
        "Peligro": [
            (a["ex_locas"]*30 + a["interrupciones"]*20 + a["futuro"]*40),
            (a["crypto"]*40 + a["selfies"]*20 + (20 if a["perfume"] == "Tóxico" else 0)),
            (a["movil"]*5 + (50 if a["camareros"] == "Maleducado" else 0)),
            (50 if a["location"] == "Su casa (🚩)" else 0)
        ]
    }
    df = pd.DataFrame(puntos_dict)
    nivel_total = min(int(df["Peligro"].sum()), 100)
    return df, nivel_total

def inject_chat_css():
    st.markdown("""
    <style>
      .chat-wrap{
          height: 65vh;
          overflow-y: auto;
          padding: 18px 14px;
          border-radius: 22px;
          background: rgba(255,255,255,0.60);
          border: 1px solid rgba(255, 20, 147, 0.18);
          box-shadow: 0 10px 30px rgba(199, 21, 133, 0.08);
          backdrop-filter: blur(6px);
      }
      .row{display:flex;gap:10px;margin:10px 0;align-items:flex-end;}
      .row.user{justify-content:flex-end;}
      .row.assistant{justify-content:flex-start;}
      .avatar{
          width:34px;height:34px;border-radius:50%;
          display:flex;align-items:center;justify-content:center;
          font-size:16px;flex:0 0 34px;
          box-shadow:0 6px 18px rgba(0,0,0,0.06);
          border:1px solid rgba(0,0,0,0.06);
          background: rgba(255,255,255,0.85);
      }
      .bubble{
          max-width:70%;
          padding:12px 14px;border-radius:18px;
          line-height:1.3rem;font-size:15.5px;
          box-shadow:0 10px 25px rgba(0,0,0,0.06);
          border:1px solid rgba(0,0,0,0.05);
          word-wrap:break-word;white-space:pre-wrap;
      }
      .bubble.user{
          background: linear-gradient(90deg, rgba(255,20,147,0.95) 0%, rgba(199,21,133,0.95) 100%);
          color:white;border-bottom-right-radius:6px;
      }
      .bubble.assistant{
          background: rgba(255,255,255,0.92);
          color:#2b2b2b;border-bottom-left-radius:6px;
      }
      .meta{font-size:11px;opacity:0.7;margin-top:6px;}
    </style>
    """, unsafe_allow_html=True)

def render_custom_chat(messages):
    parts = ['<div class="chat-wrap" id="chatbox">']
    for m in messages:
        role = m.get("role", "assistant")
        content = _html.escape(m.get("content", "") or "").replace("\n", "<br>")
        ts = _html.escape(m.get("ts", "") or "")

        if role == "user":
            parts.append(
                f'<div class="row user">'
                f'  <div class="bubble user">{content}<div class="meta">{ts}</div></div>'
                f'  <div class="avatar">🫵</div>'
                f'</div>'
            )
        else:
            parts.append(
                f'<div class="row assistant">'
                f'  <div class="avatar">💅</div>'
                f'  <div class="bubble assistant">{content}<div class="meta">{ts}</div></div>'
                f'</div>'
            )

    parts.append("</div>")
    parts.append("""
    <script>
      const el = document.getElementById('chatbox');
      if (el) { el.scrollTop = el.scrollHeight; }
    </script>
    """)

    html_block = "".join(parts)

    # OJO: el CSS lo sigues inyectando con inject_chat_css() en la página
    components.html(html_block, height=520, scrolling=True)


# ---------------------------------------------------
# PAGE 1 — INICIO
# ---------------------------------------------------

if st.session_state.page == "inicio":

    st.markdown("<h1 style='text-align:center;color:#C71585;'>✨ Red Flag Detector ✨</h1>", unsafe_allow_html=True)
    st.write("Analiza tu cita antes de que analice tu estabilidad emocional.")

    api_key = st.text_input("Introduce tu Google API Key", type="password")

    if st.button("🚀 Empezar"):
        if api_key:
            st.session_state.api_key = api_key
            st.session_state.page = "cuestionario"
            st.rerun()
        else:
            st.error("Necesitas API key para invocar al Oráculo.")

# ---------------------------------------------------
# PAGE 2 — CUESTIONARIO
# ---------------------------------------------------

elif st.session_state.page == "cuestionario":

    st.markdown("## 🕵️‍♀️ Cuéntame los detalles…")

    with st.sidebar:
        location = st.selectbox(
            "¿Dónde fue la cita?",
            ["Restaurante chic", "Cafetería mona", "Cita en el parque", "Cine", "Su casa (🚩)"]
        )
        alcohol = st.toggle("¿Hubo vinito? 🍷")
        if st.button("⬅️ Volver"):
            st.session_state.page = "inicio"
            st.rerun()

    col1, col2, col3 = st.columns(3)

    with col1:
        ex_locas = st.checkbox("Menciona a la ex")
        interrupciones = st.checkbox("Te corta hablando")
        futuro = st.checkbox("Love bombing")

    with col2:
        selfies = st.checkbox("Se hace selfies")
        crypto = st.checkbox("Habla de crypto")
        perfume = st.select_slider("Nivel de perfume",
                                   ["Elegante","Aceptable","Mareante","Tóxico"],
                                   value="Aceptable")

    with col3:
        movil = st.number_input("Veces que miró el móvil",0,50,0)
        camareros = st.radio("Trato al personal",
                             ["Ejemplar","Seco","Maleducado"])

    if st.button("⚖️ Analizar"):

        answers = {
            "location": location,
            "alcohol": alcohol,
            "ex_locas": int(ex_locas),
            "interrupciones": int(interrupciones),
            "futuro": int(futuro),
            "selfies": int(selfies),
            "crypto": int(crypto),
            "perfume": perfume,
            "movil": int(movil),
            "camareros": camareros
        }

        df, nivel_total = compute_score(answers)

        st.session_state.answers = answers
        st.session_state.score_df = df
        st.session_state.nivel_total = nivel_total
        st.session_state.verdict_chat = [
            {"role":"assistant","content":"Bestie… he analizado el informe confidencial 🚨","ts":stamp()},
            {"role":"assistant","content":f"Índice de toxicidad: {nivel_total}%","ts":stamp()},
        ]

        st.session_state.page = "veredicto"
        st.rerun()

# ---------------------------------------------------
# PAGE 3 — VEREDICTO + CHAT
# ---------------------------------------------------

elif st.session_state.page == "veredicto":

    st.markdown("## 💬 Veredicto oficial de tu bestie")

    with st.sidebar:
        if st.button("🔁 Rehacer cuestionario"):
            st.session_state.page = "cuestionario"
            st.rerun()
        if st.button("🏠 Inicio"):
            st.session_state.page = "inicio"
            st.rerun()

    df = st.session_state.score_df
    nivel_total = st.session_state.nivel_total
    answers = st.session_state.answers

    st.subheader("📊 Perfil de riesgo")
    chart = alt.Chart(df).mark_bar().encode(
        x='Categoría',
        y=alt.Y('Peligro', scale=alt.Scale(domain=[0,100])),
        color=alt.value("#C71585")
    )
    st.altair_chart(chart, use_container_width=True)

    if nivel_total >= 75:
        st.error(f"Toxicidad alta: {nivel_total}%")
    elif nivel_total >= 30:
        st.warning(f"Toxicidad moderada: {nivel_total}%")
    else:
        st.success(f"Green-ish flag: {nivel_total}%")
        st.balloons()

    inject_chat_css()

    if st.button("🔮 Preguntar a Gemini"):
        prompt = (
            "Eres la mejor amiga protectora y sarcástica. "
            f"Índice: {nivel_total}%.\n"
            f"Trato a camareros: {answers['camareros']}.\n"
            f"Habló de crypto: {bool(answers['crypto'])}.\n"
            f"Ubicación: {answers['location']}.\n"
            "Responde en máximo 4 frases cortas, estilo chat."
        )

        client = genai.Client(api_key=st.session_state.api_key)
        with st.spinner("Bestie está escribiendo..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"temperature":1.2}
            )

        st.session_state.verdict_chat.append(
            {"role":"assistant","content":response.text,"ts":stamp()}
        )
        st.rerun()

    render_custom_chat(st.session_state.verdict_chat)
