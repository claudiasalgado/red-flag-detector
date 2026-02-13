import streamlit as st
import pandas as pd
import altair as alt
from google import genai
from google.genai import types

# 1. Configuración de página
st.set_page_config(page_title="Red flag detector", page_icon="🚩", layout="wide")

# Inicializar el estado de la navegación si no existe
if 'page' not in st.session_state:
    st.session_state.page = 'inicio'

# 2. CSS Avanzado UNIFICADO (Girlie & Clean)
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #FFF0F5 0%, #FFDEE9 100%); }
    
    /* Estilo de contenedores */
    div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 10px 10px 25px rgba(255, 182, 193, 0.3);
    }

    /* Centrado de títulos y botones */
    .main-title {
        text-align: center;
        color: #C71585;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        margin-bottom: 30px;
    }

    .stButton > button {
        display: block;
        margin: 0 auto;
        border: none;
        background: linear-gradient(90deg, #FF1493 0%, #C71585 100%);
        color: white;
        padding: 15px 45px;
        font-size: 20px;
        font-weight: bold;
        border-radius: 50px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 20, 147, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 20, 147, 0.6);
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE NAVEGACIÓN ---

# PÁGINA 1: INICIO Y API KEY
if st.session_state.page == 'inicio':
    st.markdown("<h1 class='main-title'>✨ Bienvenida al Red Flag Detector ✨</h1>", unsafe_allow_html=True)
    
    col_inicio1, col_inicio2, col_inicio3 = st.columns([1, 2, 1])
    
    with col_inicio2:
        st.image("https://media.giphy.com/media/v1.Y2lkPWVjZjA1ZTQ3MjI3NzZyc2Vpd2p4ejRjNzd3Y3liZ25vcGdpOTJlcmczbWVnazNlcSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/3lxoqLn8N5ETCWpU9u/giphy.gif", use_container_width=True)
        
        with st.container():
            st.markdown("### 🔑 Antes de empezar, Bestie...")
            api_key = st.text_input(
                "Introduce tu Google API Key para que el Oráculo funcione:",
                type="password",
                placeholder="AIzaSy..."
            )
            st.caption("Consigue tu key en [Google AI Studio](https://aistudio.google.com/)")
            
            if st.button("🚀 EMPEZAR ANÁLISIS"):
                if api_key:
                    st.session_state.api_key = api_key
                    st.session_state.page = 'cuestionario'
                    st.rerun()
                else:
                    st.error("¡Necesitas la API Key para que Gemini te aconseje! 💅")

# PÁGINA 2: CUESTIONARIO Y RESULTADOS
elif st.session_state.page == 'cuestionario':
    st.markdown("<h1 class='main-title'>🕵️‍♀️ Analizando al Susodicho...</h1>", unsafe_allow_html=True)

    # --- SIDEBAR (Mantenemos la info útil) ---
    with st.sidebar:
        st.markdown("## 📍 Detalles de la Cita")
        location = st.selectbox("¿Dónde os habéis visto?", ["Restaurante chic", "Cafetería mona", "Cita en el parque", "Cine", "Su casa (🚩)"])
        alcohol = st.toggle("¿Hay vinito de por medio? 🍷")
        st.divider()
        if st.button("⬅️ Volver al inicio"):
            st.session_state.page = 'inicio'
            st.rerun()

    # --- CUERPO PRINCIPAL ---
    main_col1, main_col2, main_col3 = st.columns([1, 1, 1])

    with main_col1:
        with st.container():
            st.markdown("### 🗣️ Comunicación")
            ex_locas = st.checkbox("Menciona a la ex en la 1ª hora")
            interrupciones = st.checkbox("Te corta mientras hablas")
            futuro = st.checkbox("Ya planea boda (Love Bombing)")
            selfies = st.checkbox("Se ha hecho un selfie en la mesa")
            crypto = st.checkbox("Habla de 'Invertir' (Crypto)")

    with main_col2:
        with st.container():
            st.markdown("### 🧥 Estilo & Vibe")
            perfume = st.select_slider("Nivel de perfume", options=["Elegante", "Aceptable", "Mareante", "Tóxico"], value="Aceptable")
            puntualidad = st.select_slider("⏱️ ¿Puntualidad?", options=["En punto 👑", "5 min", "15 min", "30 min (🚩)", "Cena sola"], value="En punto 👑")
            outfit_effort = st.select_slider("👗 Outfit", options=["Duchado", "Casual-Chic", "Iba impecable ✨", "Boda"], value="Casual-Chic")

    with main_col3:
        with st.container():
            st.markdown("### 🤵 Modales")
            movil = st.number_input("Veces que ha mirado el móvil", 0, 50, 0)
            camareros = st.radio("Trato al personal", ["Ejemplar", "Seco", "Maleducado"])

    st.markdown("<br>", unsafe_allow_html=True)
    juzgar = st.button("⚖️ EJECUTAR ANÁLISIS DE SEGURIDAD")

    # --- SECCIÓN DE RESULTADOS ---
    if juzgar:
        # Lógica de datos (Sin cambios en los cálculos)
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
        nivel_total = min(df["Peligro"].sum(), 100)

        st.divider()
        res_col1, res_col2 = st.columns([1.2, 1])

        with res_col1:
            st.subheader("📊 Perfil de Riesgo")
            chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=10, cornerRadiusTopRight=10).encode(
                x=alt.X('Categoría', sort=None),
                y=alt.Y('Peligro', scale=alt.Scale(domain=[0, 100])),
                color=alt.value("#C71585")
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)

        with res_col2:
            st.subheader("✨ Veredicto Final")
            if nivel_total >= 75:
                st.error(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
                st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaW43bXhveWp4dGIxYnE1eWp1YW8ya2lxaHA3cmpnendhOWo5N3QzMyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6r4R1HHNsfZGuOtO5V/giphy.gif")
            elif nivel_total >= 30:
                st.warning(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
                st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYmNkNjNrMmEyNWo1ZmdnZGo4OWwwbDk5N29iNjc4aDE2eXc0OThqdSZlcD12MV9naWZzX3NlYXJjaCZjdD1n/ANbD1CCdA3iI8/giphy.gif")
            else:
                st.success(f"ÍNDICE DE TOXICIDAD: {nivel_total}%")
                st.image("https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExeDVmaHBxN2V3cGZ4OHE0dDI3ZmcycTJxMmFiM3hoZ2g2YmI2cjJ2eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/eoeKEMNQBFLoP95RWH/giphy.gif")
                st.balloons()

        # IA GENERATIVA (GEMINI) - Usando la API Key guardada
        st.divider()
        st.subheader("🔮 El Oráculo de tu Bestie (Gemini Edition)")

        prompt_ia = (
            f"Eres la mejor amiga de la chica que está teniendo esta cita. "
            f"Hablas como una girl actual, divertida, un poco sarcástica pero protectora. "
            f"Tu misión es analizar si el chico es una red flag o no y darle consejos reales.\n\n"
            
            f"Contexto de la cita:\n"
            f"- Índice de toxicidad: {nivel_total}%\n"
            f"- Trato a camareros: {camareros}\n"
            f"- ¿Habló de crypto?: {crypto}\n"
            f"- Ubicación: {location}\n\n"
            
            f"Si el índice de toxicidad es alto o hay comportamientos de red flag, "
            f"sé clara y directa. Si todo pinta bien, hypea un poco pero con cautela. "
            f"Usa tono de amiga protectora, expresiones actuales y energía de 'yo te cuido'. "
            f"Responde en máximo 4 frases cortas como si estuvieras chateando. Sé graciosa y directa."
            f"Termina con un consejo práctico para lo que debería hacer durante o después de la cita."
        )

        try:
            client = genai.Client(api_key=st.session_state.api_key)
            with st.spinner("✨ Consultando al oráculo..."):
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_ia,
                    config={
                        "temperature": 2,
                    },
                )


            st.chat_message("assistant", avatar="💅").write(response.text)

        except Exception as e:
            if "429" in str(e):
                st.error("💖 ¡Oye, frena un poco, Bestie! El oráculo está saturado de tanto cotilleo. Espera un minuto y vuelve a intentarlo.")
            else:
                st.error(f"🚨 Ups, algo falló: {e}")