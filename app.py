# app.py
import streamlit as st
from google import genai

# =========================
# Config + State
# =========================
st.set_page_config(page_title="Red Flag Detector", page_icon="🚩", layout="wide")

def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "landing"
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "date_data" not in st.session_state:
        st.session_state.date_data = {}
    if "score" not in st.session_state:
        st.session_state.score = None
    if "level" not in st.session_state:
        st.session_state.level = None

def go(page: str):
    st.session_state.page = page
    st.rerun()

init_state()

# =========================
# CSS (inspirado en tu base)
# =========================
st.markdown(
    """
<style>
/* Fondo girlie */
.stApp { background: linear-gradient(135deg, #FFF0F5 0%, #FFDEE9 100%); }

/* Contenedores */
div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
    background-color: rgba(255, 255, 255, 0.72);
    border-radius: 20px;
    padding: 22px;
    box-shadow: 10px 10px 25px rgba(255, 182, 193, 0.28);
}

/* Títulos */
.main-title {
    text-align: center;
    color: #C71585;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: 900;
    margin-bottom: 12px;
}

/* Botones */
.stButton > button {
    display: block;
    margin: 0 auto;
    border: none;
    background: linear-gradient(90deg, #FF1493 0%, #C71585 100%);
    color: white;
    padding: 14px 42px;
    font-size: 18px;
    font-weight: 800;
    border-radius: 999px;
    transition: all 0.2s ease;
    box-shadow: 0 6px 18px rgba(255, 20, 147, 0.35);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 26px rgba(255, 20, 147, 0.55);
    color: white !important;
}

/* “WhatsApp-ish” chat */
.chat-wrap{
    max-width: 760px;
    margin: 0 auto;
    padding: 6px 4px;
}
.chat-row{
    width: 100%;
    display: block;
    margin: 8px 0;
}
.bubble{
    display: inline-block;
    max-width: 85%;
    padding: 10px 12px;
    border-radius: 16px;
    line-height: 1.25;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 15px;
    position: relative;
}
.left { background: rgba(255,255,255,0.98); border: 1px solid rgba(0,0,0,0.06); }
.right { background: rgba(220, 248, 198, 0.95); border: 1px solid rgba(0,0,0,0.04); }

.row-left{ text-align: left; }
.row-right{ text-align: right; }

.time{
    font-size: 11px;
    opacity: 0.65;
    margin-left: 10px;
    white-space: nowrap;
    float: right;
}
.small-note{
    text-align:center;
    font-size: 13px;
    opacity: .75;
}
hr.soft {
    border: none;
    border-top: 1px solid rgba(199,21,133,0.18);
    margin: 16px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# Helpers: chat rendering
# =========================
def render_chat(messages):
    """
    messages: list[dict] con:
      - side: "left" | "right"
      - text: str
      - time: str | None
    """
    html = ["<div class='chat-wrap'>"]
    for m in messages:
        side = m.get("side", "left")
        text = (m.get("text", "") or "").replace("\n", "<br>")
        t = m.get("time", None)
        row_class = "row-right" if side == "right" else "row-left"
        bubble_class = "right" if side == "right" else "left"

        time_html = f"<span class='time'>{t}</span>" if t else ""
        html.append(
            f"""
<div class="chat-row {row_class}">
  <div class="bubble {bubble_class}">
    {text}{time_html}
  </div>
</div>
"""
        )
    html.append("</div>")
    st.markdown("\n".join(html), unsafe_allow_html=True)

def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))

# =========================
# Heurística de score
# =========================
def compute_score(data: dict) -> tuple[int, str, dict]:
    """
    Devuelve: (score 0-100, nivel, breakdown dict)
    Transparente y simple: suma puntos por red flags y resta por green flags.
    """
    points = 0
    breakdown = {}

    # --- Trato al personal (peso alto)
    staff = data.get("trato_personal", "Sin responder")
    staff_map = {"Maravilloso": 0, "Correcto": 5, "Seco": 15, "Maleducado": 25, "Sin responder": 10}
    p = staff_map.get(staff, 10)
    points += p
    breakdown["Trato al personal"] = p

    # --- Control / invasión de privacidad
    control = data.get("control_movil_redes", "Sin responder")
    p = 20 if control == "Sí" else (8 if control == "Sin responder" else 0)
    points += p
    breakdown["Control (móvil/redes)"] = p

    # --- Límites / consentimiento
    limites = data.get("respeto_limites", "Sin responder")
    limites_map = {
        "Sí, 10/10": 0,
        "Más o menos": 10,
        "No, insistió": 25,
        "Sin responder": 8,
    }
    p = limites_map.get(limites, 8)
    points += p
    breakdown["Respeto de límites"] = p

    # --- Ex’s
    exs = data.get("tema_exs", "Sin responder")
    ex_map = {
        "Cero drama": 0,
        "Lo mencionó normal": 5,
        "Rant / victimismo": 10,
        "Comparó contigo": 15,
        "Sin responder": 6,
    }
    p = ex_map.get(exs, 6)
    points += p
    breakdown["Tema ex’s"] = p

    # --- Celos
    celos = data.get("celos", "Sin responder")
    cel_map = {"No": 0, "Un poco": 8, "Sí": 15, "Sin responder": 6}
    p = cel_map.get(celos, 6)
    points += p
    breakdown["Celos"] = p

    # --- Seguridad: insistió en sitio aislado / su casa
    aislado = data.get("insistio_sitio_aislado", "Sin responder")
    p = 25 if aislado == "Sí" else (10 if aislado == "Sin responder" else 0)
    points += p
    breakdown["Insistió en sitio aislado"] = p

    # --- Seguridad: presionó alcohol u otras cosas
    presion = data.get("presiono_alcohol", "Sin responder")
    p = 20 if presion == "Sí" else (8 if presion == "Sin responder" else 0)
    points += p
    breakdown["Presión con alcohol"] = p

    # --- Love bombing / planes intensitos
    bombing = data.get("love_bombing", "Sin responder")
    p = 15 if bombing == "Sí" else (5 if bombing == "Sin responder" else 0)
    points += p
    breakdown["Love bombing"] = p

    # --- Incoherencias / mentiras
    incoh = data.get("incoherencias", "Sin responder")
    p = 15 if incoh == "Sí" else (6 if incoh == "Sin responder" else 0)
    points += p
    breakdown["Incoherencias"] = p

    # --- Comunicación (0-10): “me escuchó” y “me dejó hablar”
    # Usamos strings para permitir "Sin responder"
    def to_int_0_10(v, default_mid=5):
        if v is None:
            return default_mid
        if isinstance(v, int):
            return clamp(v, 0, 10)
        s = str(v).strip()
        if s.lower().startswith("sin"):
            return default_mid
        try:
            return clamp(int(s), 0, 10)
        except Exception:
            return default_mid

    escucho = to_int_0_10(data.get("me_escucho_0_10", "Sin responder"), 5)
    dejo_hablar = to_int_0_10(data.get("me_dejo_hablar_0_10", "Sin responder"), 5)
    preguntó = to_int_0_10(data.get("me_hizo_preguntas_0_10", "Sin responder"), 5)

    # Penaliza si están bajos (cuanto más bajo, más puntos)
    p_listen = int(round((10 - escucho) * 1.2))
    p_speak = int(round((10 - dejo_hablar) * 1.2))
    p_questions = int(round((10 - preguntó) * 1.0))

    points += p_listen + p_speak + p_questions
    breakdown["No escuchó / poca atención"] = p_listen
    breakdown["Interrumpía / no te dejó hablar"] = p_speak
    breakdown["Cero curiosidad por ti"] = p_questions

    # --- Valores (0-10)
    valores = to_int_0_10(data.get("compatibilidad_valores_0_10", "Sin responder"), 6)
    p = int(round((10 - valores) * 0.9))
    points += p
    breakdown["Valores poco alineados"] = p

    # --- Móvil en mesa (0-20+) (cap)
    miradas_movil = data.get("miradas_movil", 0)
    try:
        miradas_movil = int(miradas_movil)
    except Exception:
        miradas_movil = 0
    p = int(clamp(miradas_movil * 1.2, 0, 15))
    points += p
    breakdown["Móvil (demasiado presente)"] = p

    # --- Green flags (restan)
    greens = data.get("green_flags", [])
    green_bonus = 0
    if "Pidió consentimiento / fue respetuoso" in greens:
        green_bonus += 10
    if "Te hizo sentir segura (plan lógico, acompañar, etc.)" in greens:
        green_bonus += 8
    if "Comunicación clara y amable" in greens:
        green_bonus += 7
    points -= green_bonus
    breakdown["Green flags (resta)"] = -green_bonus

    score = clamp(points, 0, 100)

    # Niveles
    if score <= 20:
        level = "🟢 Verde"
    elif score <= 45:
        level = "🟡 Amarillo"
    elif score <= 70:
        level = "🟠 Naranja"
    else:
        level = "🔴 Rojo"

    return score, level, breakdown

def build_gemini_prompt(data: dict, score: int, level: str) -> str:
    # Nota: si algo es ambiguo del código base, nos quedamos con lo más simple:
    # patrón EXACTO: genai.Client(api_key=...), client.models.generate_content(model=..., contents=..., config=...)
    location = data.get("location", "Sin responder")
    alcohol = data.get("alcohol", False)
    trato = data.get("trato_personal", "Sin responder")
    exs = data.get("tema_exs", "Sin responder")
    celos = data.get("celos", "Sin responder")
    notas_red = (data.get("nota_rara", "") or "").strip()
    notas_green = (data.get("nota_buena", "") or "").strip()

    # Resumen corto para que Gemini no se ponga a escribir El Quijote
    summary_lines = [
        f"- Score: {score}/100 ({level})",
        f"- Ubicación: {location}",
        f"- ¿Alcohol?: {'Sí' if alcohol else 'No'}",
        f"- Trato al personal: {trato}",
        f"- Ex’s: {exs}",
        f"- Celos: {celos}",
    ]
    if notas_red:
        summary_lines.append(f"- Lo que chirrió: {notas_red[:180]}")
    if notas_green:
        summary_lines.append(f"- Lo bueno: {notas_green[:180]}")

    summary = "\n".join(summary_lines)

    return (
        "Eres la mejor amiga de la chica que está contando su cita por WhatsApp. "
        "Tono: divertido, directo, cariñoso y protector. Un toque sarcástico suave, cero insultos. "
        "Nada de diagnósticos clínicos, nada de terapia, nada de patologizar.\n\n"
        "Objetivo: dale un consejo realista y accionable según el score. "
        "Si hay señales de seguridad o control, prioriza seguridad y límites. "
        "Si pinta bien, hypea con cautela.\n\n"
        "Formato: máximo 4 frases cortas, estilo chat. Usa 1-3 emojis máximo (no más, que no es una feria).\n\n"
        "Contexto:\n"
        f"{summary}\n\n"
        "Termina con un consejo práctico para hacer ahora (durante o después de la cita)."
    )

# =========================
# UI: Páginas
# =========================
def page_landing():
    st.markdown("<h1 class='main-title'>🚩 Red Flag Detector (WhatsApp Edition) 💅</h1>", unsafe_allow_html=True)

    # Estado del chat en landing
    if "landing_chat" not in st.session_state:
        st.session_state.landing_chat = [
            {"side": "left", "text": "Has tenido una cita????", "time": "22:41"},
            {"side": "left", "text": "CUÉNTAMELO TODO YAAA", "time": "22:41"},
            {"side": "right", "text": "Bestie… estoy procesando todavía 😭", "time": "22:42"},
            {"side": "left", "text": "No me dejes en suspense que me da algo.", "time": "22:42"},
            {"side": "left", "text": "Pásame señales: vibes, modales, celos, ex’s, TODO.", "time": "22:43"},
            {"side": "right", "text": "Vale. Abro el detector. Si salta alarma, te saco de ahí.", "time": "22:43"},
            {"side": "left", "text": "Primero: necesito tu Google API Key para invocar a Gemini. 🧙‍♀️", "time": "22:44"},
            {
                "side": "left",
                "text": "Pégala aquí abajo como si me la mandaras por WhatsApp (tranqui, va en modo oculto).",
                "time": "22:44",
            },
        ]

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        render_chat(st.session_state.landing_chat)

        st.markdown("<hr class='soft'/>", unsafe_allow_html=True)
        st.markdown(
            "<div class='small-note'>Tip: si no tienes key todavía, te dejo el link. No invento URLs, por una vez.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("[Consigue tu API key aquí](https://aistudio.google.com/)")

        # --- Composer estilo WhatsApp (input + enviar) ---
        # Importante: input seguro type=password, pero UX chat
        with st.container():
            c_in, c_btn = st.columns([5, 1])
            with c_in:
                api_key_draft = st.text_input(
                    "Escribe tu API key como respuesta",
                    type="password",
                    placeholder="AIzaSy...",
                    key="api_key_draft",
                    label_visibility="collapsed",
                )
            with c_btn:
                send = st.button("Enviar", use_container_width=True)

        if send:
            if not (api_key_draft or "").strip():
                st.error("Me has mandado aire. Necesito la key, no vibes. 💅")
                return

            # Guardar key (sin imprimirla)
            st.session_state.api_key = api_key_draft.strip()

            # “Enviar” mensaje al chat pero enmascarado (NO mostramos la key real)
            masked = "•" * min(16, max(8, len(st.session_state.api_key)))
            st.session_state.landing_chat.append(
                {"side": "right", "text": f"Aquí va: {masked}", "time": "22:45"}
            )
            st.session_state.landing_chat.append(
                {"side": "left", "text": "Perfecto. Abriendo el cuestionario…", "time": "22:45"}
            )

            # Limpia el draft por estética
            st.session_state.api_key_draft = ""

            go("cuestionario")


def page_cuestionario():
    st.markdown("<h1 class='main-title'>📝 Cuestionario: el chismómetro con método</h1>", unsafe_allow_html=True)

    if not (st.session_state.api_key or "").strip():
        st.error("Te falta la API key. Vuelve al inicio y pégala en el input seguro.")
        if st.button("⬅️ Ir al inicio"):
            go("landing")
        return

    # Sidebar: contexto rápido (inspirado en tu base)
    with st.sidebar:
        st.markdown("## 📍 Contexto")
        location = st.selectbox(
            "¿Dónde fue la cita?",
            ["Restaurante chic", "Cafetería mona", "Paseo por el parque", "Cine", "Su casa (🚩)", "Otro"],
            index=0,
            key="sb_location",
        )
        alcohol = st.toggle("¿Hubo vinito / alcohol? 🍷", key="sb_alcohol")
        st.divider()
        if st.button("⬅️ Volver a Landing"):
            go("landing")

    # Preguntas (mínimo 10) con defaults “Sin responder” para progreso real
    q_total = 12  # contamos las “core” (las notas y greens van aparte)

    def answered(v):
        # Consideramos respondido si no es "Sin responder"
        if v is None:
            return False
        s = str(v).strip().lower()
        return not s.startswith("sin responder")

    # Defaults
    defaults = {
        "me_dejo_hablar_0_10": "Sin responder",
        "me_escucho_0_10": "Sin responder",
        "me_hizo_preguntas_0_10": "Sin responder",
        "trato_personal": "Sin responder",
        "compatibilidad_valores_0_10": "Sin responder",
        "control_movil_redes": "Sin responder",
        "respeto_limites": "Sin responder",
        "tema_exs": "Sin responder",
        "celos": "Sin responder",
        "insistio_sitio_aislado": "Sin responder",
        "presiono_alcohol": "Sin responder",
        "love_bombing": "Sin responder",
        "incoherencias": "Sin responder",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "miradas_movil" not in st.session_state:
        st.session_state.miradas_movil = 0
    if "green_flags" not in st.session_state:
        st.session_state.green_flags = []
    if "nota_rara" not in st.session_state:
        st.session_state.nota_rara = ""
    if "nota_buena" not in st.session_state:
        st.session_state.nota_buena = ""

    # Progreso (de 12 preguntas core, sin contar notas/greens)
    core_keys = [
        "me_dejo_hablar_0_10",
        "me_escucho_0_10",
        "me_hizo_preguntas_0_10",
        "trato_personal",
        "compatibilidad_valores_0_10",
        "control_movil_redes",
        "respeto_limites",
        "tema_exs",
        "celos",
        "insistio_sitio_aislado",
        "presiono_alcohol",
        "love_bombing",
        "incoherencias",
    ]
    # q_total pedido mínimo 10; aquí hay 13 core. Para el indicador lo dejamos en 13.
    answered_count = sum(1 for k in core_keys if answered(st.session_state.get(k)))
    prog = answered_count / max(1, len(core_keys))
    st.progress(prog)
    st.caption(f"Progreso: {answered_count}/{len(core_keys)} (sí, esto es lo que pasa cuando intentas poner orden en el caos romántico).")

    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        with st.container():
            st.markdown("### 🗣️ Comunicación")
            st.select_slider(
                "¿Te dejó hablar? (0–10)",
                options=["Sin responder"] + [str(i) for i in range(0, 11)],
                key="me_dejo_hablar_0_10",
            )
            st.select_slider(
                "¿Te escuchó de verdad? (0–10)",
                options=["Sin responder"] + [str(i) for i in range(0, 11)],
                key="me_escucho_0_10",
            )
            st.select_slider(
                "¿Te hizo preguntas sobre ti? (0–10)",
                options=["Sin responder"] + [str(i) for i in range(0, 11)],
                key="me_hizo_preguntas_0_10",
            )
            st.number_input(
                "Veces que miró el móvil (estimación honesta 😐)",
                min_value=0,
                max_value=50,
                value=int(st.session_state.miradas_movil),
                key="miradas_movil",
            )

    with c2:
        with st.container():
            st.markdown("### 🤝 Respeto & valores")
            st.selectbox(
                "Trato al personal (camareros, etc.)",
                ["Sin responder", "Maravilloso", "Correcto", "Seco", "Maleducado"],
                key="trato_personal",
            )
            st.select_slider(
                "Compatibilidad de valores (0–10)",
                options=["Sin responder"] + [str(i) for i in range(0, 11)],
                key="compatibilidad_valores_0_10",
            )
            st.selectbox(
                "Cuando marcaste un límite / dijiste ‘no’…",
                ["Sin responder", "Sí, 10/10", "Más o menos", "No, insistió"],
                key="respeto_limites",
            )
            st.selectbox(
                "Tema ex’s…",
                ["Sin responder", "Cero drama", "Lo mencionó normal", "Rant / victimismo", "Comparó contigo"],
                key="tema_exs",
            )

    with c3:
        with st.container():
            st.markdown("### 🚨 Control, celos y seguridad")
            st.selectbox(
                "¿Intentó controlar tu móvil/redes o preguntó cosas invasivas?",
                ["Sin responder", "No", "Sí"],
                key="control_movil_redes",
            )
            st.selectbox(
                "¿Celos raritos?",
                ["Sin responder", "No", "Un poco", "Sí"],
                key="celos",
            )
            st.selectbox(
                "¿Insistió en ir a su casa / sitio aislado (cuando no te apetecía)?",
                ["Sin responder", "No", "Sí"],
                key="insistio_sitio_aislado",
            )
            st.selectbox(
                "¿Te presionó con alcohol o algo que no querías?",
                ["Sin responder", "No", "Sí"],
                key="presiono_alcohol",
            )
            st.selectbox(
                "¿Love bombing? (boda, hijos, ‘eres mi destino’ en la 1ª cita)",
                ["Sin responder", "No", "Sí"],
                key="love_bombing",
            )
            st.selectbox(
                "¿Incoherencias/mentiras (rollo contradicciones sospechosas)?",
                ["Sin responder", "No", "Sí"],
                key="incoherencias",
            )

    st.markdown("<hr class='soft'/>", unsafe_allow_html=True)

    with st.container():
        st.markdown("### ✅ Green flags (para no vivir en guerra)")
        st.multiselect(
            "Marca si pasó (y te sumó puntos):",
            [
                "Pidió consentimiento / fue respetuoso",
                "Te hizo sentir segura (plan lógico, acompañar, etc.)",
                "Comunicación clara y amable",
            ],
            key="green_flags",
        )
        st.markdown("### 📝 Notas rápidas")
        st.text_area("Algo que te chirrió (opcional, pero jugoso)", key="nota_rara", height=90)
        st.text_area("Algo que te gustó (opcional, que también se celebra)", key="nota_buena", height=90)

    if st.button("🏁 Veredicto final"):
        # Validación: no pasar si hay “Sin responder” en core
        missing = [k for k in core_keys if not answered(st.session_state.get(k))]
        if missing:
            st.error("Te faltan respuestas (las que están en ‘Sin responder’). No me hagas adivinar, que no soy tu ex. 😌")
            return

        st.session_state.date_data = {
            "location": st.session_state.get("sb_location", "Otro"),
            "alcohol": bool(st.session_state.get("sb_alcohol", False)),
            "me_dejo_hablar_0_10": st.session_state.get("me_dejo_hablar_0_10"),
            "me_escucho_0_10": st.session_state.get("me_escucho_0_10"),
            "me_hizo_preguntas_0_10": st.session_state.get("me_hizo_preguntas_0_10"),
            "miradas_movil": st.session_state.get("miradas_movil", 0),
            "trato_personal": st.session_state.get("trato_personal"),
            "compatibilidad_valores_0_10": st.session_state.get("compatibilidad_valores_0_10"),
            "control_movil_redes": st.session_state.get("control_movil_redes"),
            "respeto_limites": st.session_state.get("respeto_limites"),
            "tema_exs": st.session_state.get("tema_exs"),
            "celos": st.session_state.get("celos"),
            "insistio_sitio_aislado": st.session_state.get("insistio_sitio_aislado"),
            "presiono_alcohol": st.session_state.get("presiono_alcohol"),
            "love_bombing": st.session_state.get("love_bombing"),
            "incoherencias": st.session_state.get("incoherencias"),
            "green_flags": st.session_state.get("green_flags", []),
            "nota_rara": st.session_state.get("nota_rara", ""),
            "nota_buena": st.session_state.get("nota_buena", ""),
        }

        score, level, breakdown = compute_score(st.session_state.date_data)
        st.session_state.score = score
        st.session_state.level = level
        st.session_state.breakdown = breakdown
        go("veredicto")

def page_veredicto():
    st.markdown("<h1 class='main-title'>🔮 Veredicto (con cariño y estadísticas)</h1>", unsafe_allow_html=True)

    if not st.session_state.date_data:
        st.error("No tengo tus respuestas. Vuelve al cuestionario y dale al botón de veredicto.")
        if st.button("⬅️ Ir al cuestionario"):
            go("cuestionario")
        return

    score = st.session_state.score
    level = st.session_state.level
    breakdown = st.session_state.get("breakdown", {})

    # Chat de resultado
    intro = [
        {"side": "left", "text": "Vengo con el veredicto. Respira.", "time": None},
        {"side": "left", "text": f"Red Flag Score: **{score}/100** · Nivel: **{level}**", "time": None},
    ]

    # Copy por nivel
    if score <= 20:
        vibe = "Esto pinta bastante sano. No perfecto, pero decente. Celebramos con cautela. ✨"
    elif score <= 45:
        vibe = "Hay cositas. No es sirena de emergencia, pero sí para ir con ojo y límites claros. 👀"
    elif score <= 70:
        vibe = "Ojo. Aquí hay señales que no son ‘detallitos’, son patrones potenciales. Prioriza límites y seguridad. 🚧"
    else:
        vibe = "No. Esto no es misterio, es alarma. Si algo te hizo sentir insegura, confía en esa señal y sal de ahí. 🚨"

    intro.append({"side": "left", "text": vibe, "time": None})
    render_chat(intro)

    st.markdown("<hr class='soft'/>", unsafe_allow_html=True)

    # Explicación breve de scoring (transparente)
    with st.container():
        st.markdown("### 🧮 Cómo se puntúa (versión humana)")
        st.markdown(
            """
- **Suma puntos** si hay señales de **control**, **celos**, **mal trato al personal**, **presión** (alcohol/sitios aislados), **límites no respetados**, **incoherencias**, **love bombing**.
- **Suma un poco** si la comunicación fue floja (no escuchó, interrumpía, cero curiosidad).
- **Resta puntos** si marcaste **green flags** (respeto, seguridad, comunicación amable).
- El resultado final se **recorta a 0–100** para que no explote el drama.
"""
        )

    # Llamada a Gemini (patrón EXACTO del código base)
    st.markdown("### 💬 Mensaje de tu bestie (Gemini)")
    prompt_ia = build_gemini_prompt(st.session_state.date_data, score, level)

    try:
        client = genai.Client(api_key=st.session_state.api_key)
        with st.spinner("✨ Consultando al oráculo..."):
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_ia,
                config={"temperature": 1.3},
            )

        # Mostrar como chat
        render_chat(
            [
                {"side": "right", "text": "Vale. Dímelo claro.", "time": None},
                {"side": "left", "text": (response.text or "").strip(), "time": None},
            ]
        )

    except Exception as e:
        if "429" in str(e):
            st.error("💖 El oráculo está saturado. Espera un minuto y reintenta.")
        else:
            st.error(f"🚨 Ups, algo falló con Gemini: {e}")

# =========================
# Router
# =========================
if st.session_state.page == "landing":
    page_landing()
elif st.session_state.page == "cuestionario":
    page_cuestionario()
elif st.session_state.page == "veredicto":
    page_veredicto()
else:
    # fallback
    st.session_state.page = "landing"
    st.rerun()
