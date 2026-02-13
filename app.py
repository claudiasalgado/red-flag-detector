import streamlit as st
import pandas as pd
import altair as alt
from google import genai
from datetime import datetime

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
          height: 68vh;
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
          line-height:1.25rem;font-size:15.5px;
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
    html = '<div class="chat-wrap" id="chatbox">'
    for m in messages:
        role = m.get("role","assistant")
        content = (m.get("content","") or "").replace("<","&lt;").replace(">","&gt;")
        ts = m.get("ts","")
        if role == "user":
            html += f"""
              <div class="row user">
                <div class="bubble user">{content}<div class="meta">{ts}</div></div>
                <div class="avatar">🫵</div>
              </div>
            """
        else:
            html += f"""
              <div class="row assistant">
                <div class="avatar">💅</div>
                <div class="bubble assistant">{content}<div class="meta">{ts}</div></div>
              </div>
            """
    html += "</div>"
    html += """
    <script>
      const el = window.parent.document.querySelector('#chatbox');
      if (el) { el.scrollTop = el.scrollHeight; }
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)

juzgar = st.button("⚖️ EJECUTAR ANÁLISIS DE SEGURIDAD")

if juzgar:
    answers = {
        "location": location,
        "alcohol": alcohol,
        "ex_locas": int(ex_locas),
        "interrupciones": int(interrupciones),
        "futuro": int(futuro),
        "selfies": int(selfies),
        "crypto": int(crypto),
        "perfume": perfume,
        "puntualidad": puntualidad,
        "outfit_effort": outfit_effort,
        "movil": int(movil),
        "camareros": camareros
    }

    df, nivel_total = compute_score(answers)

    st.session_state.answers = answers
    st.session_state.score_df = df
    st.session_state.nivel_total = nivel_total

    # Inicializa el chat de veredicto (mensajes)
    st.session_state.verdict_chat = [
        {"role":"assistant","content":"Bestie… acabo de recibir el informe confidencial 🚨", "ts": stamp()},
        {"role":"assistant","content":f"Índice de toxicidad: {nivel_total}%.", "ts": stamp()},
    ]

    st.session_state.page = "veredicto"
    st.rerun()

elif st.session_state.page == "veredicto":
    st.markdown("<h1 class='main-title'>💬 Tu bestie tiene un veredicto</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 🧾 Navegación")
        if st.button("🔁 Rehacer cuestionario"):
            st.session_state.page = "cuestionario"
            st.rerun()
        if st.button("🏠 Volver al inicio"):
            st.session_state.page = "inicio"
            st.rerun()

    df = st.session_state.get("score_df")
    nivel_total = st.session_state.get("nivel_total")
    answers = st.session_state.get("answers")

    if df is None or nivel_total is None or answers is None:
        st.error("No hay datos del análisis. Vuelve al cuestionario.")
        st.stop()

    # 1) Gráfica + veredicto visual
    st.subheader("📊 Perfil de Riesgo")
    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
        x=alt.X('Categoría', sort=None),
        y=alt.Y('Peligro', scale=alt.Scale(domain=[0, 100])),
        color=alt.value("#C71585")
    ).properties(height=260)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("✨ Resultado")
    if nivel_total >= 75:
        st.error(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
    elif nivel_total >= 30:
        st.warning(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
    else:
        st.success(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
        st.balloons()

    # 2) Chat UI custom
    inject_chat_css()
    if "verdict_chat" not in st.session_state:
        st.session_state.verdict_chat = [{"role":"assistant","content":"Bestie…", "ts": stamp()}]

    # Botón para pedir a Gemini (si no quieres que se llame siempre)
    colA, colB = st.columns([1,1])
    with colA:
        gen = st.button("🔮 Pedir veredicto a Gemini")
    with colB:
        if st.button("🧹 Limpiar chat"):
            st.session_state.verdict_chat = [{"role":"assistant","content":"Vale, empezamos de cero 😌", "ts": stamp()}]
            st.rerun()

    if gen:
        prompt_ia = (
            "Eres la mejor amiga de la chica que está teniendo esta cita. "
            "Hablas como una girl actual, divertida, un poco sarcástica pero protectora. "
            "Analiza si el chico es red flag o green flag y da consejo real.\n\n"
            f"Contexto:\n"
            f"- Índice de toxicidad: {nivel_total}%\n"
            f"- Trato a camareros: {answers['camareros']}\n"
            f"- ¿Habló de crypto?: {bool(answers['crypto'])}\n"
            f"- Ubicación: {answers['location']}\n\n"
            "Responde en máximo 4 frases cortas como si estuvieras chateando. "
            "Sé graciosa y directa. Termina con un consejo práctico."
        )

        try:
            client = genai.Client(api_key=st.session_state.api_key)
            with st.spinner("✨ Bestie está escribiendo..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_ia,
                    config={"temperature": 1.2},
                )

            st.session_state.verdict_chat.append(
                {"role":"assistant","content": response.text, "ts": stamp()}
            )
            st.rerun()

        except Exception as e:
            if "429" in str(e):
                st.error("El oráculo está saturado. Espera un poco y reintenta.")
            else:
                st.error(f"Error Gemini: {e}")

    render_custom_chat(st.session_state.verdict_chat)

