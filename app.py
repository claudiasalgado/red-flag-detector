import streamlit as st
import pandas as pd
import altair as alt
from google import genai

# --- helpers ---
def init_chat_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Bestie 😌💅 cuéntamelo todo. Voy a analizar al susodicho sin piedad. Primero: ¿dónde es la cita?"}
        ]
    if "step" not in st.session_state:
        st.session_state.step = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {
            "location": None,
            "alcohol": None,
            "ex_locas": None,
            "interrupciones": None,
            "futuro": None,
            "selfies": None,
            "crypto": None,
            "perfume": None,
            "puntualidad": None,
            "outfit_effort": None,
            "movil": None,
            "camareros": None,
        }
    if "analysis_done" not in st.session_state:
        st.session_state.analysis_done = False

def add_user(msg: str):
    st.session_state.messages.append({"role": "user", "content": msg})

def add_bestie(msg: str):
    st.session_state.messages.append({"role": "assistant", "content": msg})

def render_chat():
    for m in st.session_state.messages:
        if m["role"] == "assistant":
            st.chat_message("assistant", avatar="💅").write(m["content"])
        else:
            st.chat_message("user").write(m["content"])

def quick_replies(options, key_prefix="qr"):
    cols = st.columns(len(options))
    clicked = None
    for i, opt in enumerate(options):
        if cols[i].button(opt, key=f"{key_prefix}_{st.session_state.step}_{i}"):
            clicked = opt
    return clicked

def compute_score(a):
    # Map boolean-ish answers safely
    ex_locas = 1 if a["ex_locas"] else 0
    interrupciones = 1 if a["interrupciones"] else 0
    futuro = 1 if a["futuro"] else 0
    selfies = 1 if a["selfies"] else 0
    crypto = 1 if a["crypto"] else 0

    movil = int(a["movil"] or 0)
    camareros = a["camareros"] or "Ejemplar"
    perfume = a["perfume"] or "Aceptable"
    location = a["location"] or "Cafetería mona"

    puntos_dict = {
        "Categoría": ["Comunicación", "Ego/Vibe", "Modales", "Factor Location"],
        "Peligro": [
            (ex_locas*30 + interrupciones*20 + futuro*40),
            (crypto*40 + selfies*20 + (20 if perfume == "Tóxico" else 0)),
            (movil*5 + (50 if camareros == "Maleducado" else 0)),
            (50 if location == "Su casa (🚩)" else 0)
        ]
    }
    df = pd.DataFrame(puntos_dict)
    nivel_total = min(int(df["Peligro"].sum()), 100)
    return df, nivel_total

# --- PAGE: cuestionario as chat ---
st.markdown("<h1 class='main-title'>💬 Bestie Chat: Red Flag Detector</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧾 Control Panel (para humanas ansiosas)")
    if st.button("🔄 Reiniciar chat"):
        for k in ["messages","step","answers","analysis_done"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    if st.button("⬅️ Volver al inicio"):
        st.session_state.page = "inicio"
        st.rerun()

init_chat_state()
render_chat()

# --- conversational flow ---
a = st.session_state.answers
step = st.session_state.step

# Step 0: location (quick replies)
if step == 0 and a["location"] is None:
    choice = quick_replies(["Restaurante chic", "Cafetería mona", "Cita en el parque", "Cine", "Su casa (🚩)"], "loc")
    if choice:
        add_user(choice)
        a["location"] = choice
        add_bestie("Ok. Siguiente: ¿hay vinito de por medio? 🍷 (di Sí/No)")
        st.session_state.step = 1
        st.rerun()

# Step 1: alcohol
elif step == 1 and a["alcohol"] is None:
    choice = quick_replies(["Sí 🍷", "No 🚰"], "alc")
    if choice:
        add_user(choice)
        a["alcohol"] = True if "Sí" in choice else False
        add_bestie("Vale. ¿Menciona a la ex en la primera hora? 👀")
        st.session_state.step = 2
        st.rerun()

# Steps 2-6: checkboxes as yes/no chat
elif step in [2,3,4,5,6]:
    prompts = {
        2: ("ex_locas", "¿Menciona a la ex en la primera hora? 👀"),
        3: ("interrupciones", "¿Te corta mientras hablas? 🙃"),
        4: ("futuro", "¿Ya está planeando boda? (love bombing) 💍🚩"),
        5: ("selfies", "¿Se ha hecho un selfie en la mesa? 📸"),
        6: ("crypto", "Pregunta clave: ¿habla de crypto/invertir? 🪙"),
    }
    field, question = prompts[step]
    if a[field] is None:
        # if the question wasn't just asked, bestie asks again (safe)
        if st.session_state.messages[-1]["role"] != "assistant" or question not in st.session_state.messages[-1]["content"]:
            add_bestie(question)
            st.rerun()

        choice = quick_replies(["Sí", "No"], f"yn_{field}")
        if choice:
            add_user(choice)
            a[field] = True if choice == "Sí" else False

            next_step = step + 1
            if next_step == 7:
                add_bestie("Sensaciones olfativas: ¿nivel de perfume? 👃")
            st.session_state.step = next_step
            st.rerun()

# Step 7: perfume slider options as quick replies
elif step == 7 and a["perfume"] is None:
    choice = quick_replies(["Elegante", "Aceptable", "Mareante", "Tóxico"], "perf")
    if choice:
        add_user(choice)
        a["perfume"] = choice
        add_bestie("Puntualidad: ¿cómo llegó? ⏱️")
        st.session_state.step = 8
        st.rerun()

# Step 8: puntualidad
elif step == 8 and a["puntualidad"] is None:
    choice = quick_replies(["En punto 👑", "5 min", "15 min", "30 min (🚩)", "Cena sola"], "punt")
    if choice:
        add_user(choice)
        a["puntualidad"] = choice
        add_bestie("Outfit check: ¿qué tal el esfuerzo? 👗")
        st.session_state.step = 9
        st.rerun()

# Step 9: outfit
elif step == 9 and a["outfit_effort"] is None:
    choice = quick_replies(["Duchado", "Casual-Chic", "Iba impecable ✨", "Boda"], "out")
    if choice:
        add_user(choice)
        a["outfit_effort"] = choice
        add_bestie("Vale. ¿Cuántas veces ha mirado el móvil? (número) 📱")
        st.session_state.step = 10
        st.rerun()

# Step 10: móvil (free input)
elif step == 10 and a["movil"] is None:
    user_msg = st.chat_input("Escribe un número, bestie…")
    if user_msg:
        add_user(user_msg)
        try:
            a["movil"] = max(0, min(50, int(user_msg.strip())))
            add_bestie("Última y más importante: ¿cómo trata al personal? 😇😐😡")
            st.session_state.step = 11
            st.rerun()
        except:
            add_bestie("Eso no es un número, cariño. Me estás complicando la vida. Pon un número 😭")
            st.rerun()

# Step 11: camareros
elif step == 11 and a["camareros"] is None:
    choice = quick_replies(["Ejemplar", "Seco", "Maleducado"], "cam")
    if choice:
        add_user(choice)
        a["camareros"] = choice
        add_bestie("Dame 2 segundos que estoy calculando el nivel de peligro… 🧮💅")
        st.session_state.step = 12
        st.rerun()

# Step 12: show results + Gemini
elif step == 12 and not st.session_state.analysis_done:
    df, nivel_total = compute_score(a)
    st.session_state.analysis_done = True

    st.divider()
    st.subheader("📊 Perfil de Riesgo")

    chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
        x=alt.X('Categoría', sort=None),
        y=alt.Y('Peligro', scale=alt.Scale(domain=[0, 100])),
        color=alt.value("#C71585")
    ).properties(height=320)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("✨ Veredicto Final")
    if nivel_total >= 75:
        st.error(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
    elif nivel_total >= 30:
        st.warning(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
    else:
        st.success(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
        st.balloons()

    # Bestie final + Gemini
    st.divider()
    st.subheader("🔮 El Oráculo de tu Bestie (Gemini Edition)")

    prompt_ia = (
        "Eres la mejor amiga de la chica que está teniendo esta cita. "
        "Hablas como una girl actual española, divertida, un poco sarcástica pero protectora. "
        "Analiza si el chico es red flag o green flag y da consejo REAL.\n\n"
        f"Contexto:\n"
        f"- Índice de toxicidad: {nivel_total}%\n"
        f"- Trato a camareros: {a['camareros']}\n"
        f"- ¿Habló de crypto?: {a['crypto']}\n"
        f"- Ubicación: {a['location']}\n\n"
        "Responde en máximo 4 frases cortas como si estuvieras chateando. "
        "Sé graciosa y directa. Termina con un consejo práctico para ahora."
    )

    try:
        client = genai.Client(api_key=st.session_state.api_key)
        with st.spinner("✨ Bestie está escribiendo..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_ia,
                config={"temperature": 1.2},
            )
        st.chat_message("assistant", avatar="💅").write(response.text)
    except Exception as e:
        if "429" in str(e):
            st.error("💖 El oráculo está saturado de cotilleos. Espera un poco y reintenta.")
        else:
            st.error(f"🚨 Ups, algo falló: {e}")
