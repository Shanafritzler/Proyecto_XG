import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from mplsoccer import Pitch
from streamlit_image_coordinates import streamlit_image_coordinates
from funciones import (
    calcular_angulo,
    calcular_distancia,
    dentro_area
)
import joblib
from streamlit_option_menu import option_menu

# =====================
# CONFIG
# =====================

st.set_page_config(
    page_title="xGLab",
    layout="wide"
)

# =====================
# MODELO xG
# =====================

@st.cache_resource
def cargar_modelo():
    return joblib.load("modelo_xg.pkl")

modelo = cargar_modelo()

# =====================
# SESSION STATE
# =====================

#estilo de la app
st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg,
        #141414,
        #1E2430,
        #2B3445
    );
}

[data-testid="stAppViewContainer"] {
    background: inherit;
}

</style>
""", unsafe_allow_html=True)

#estilo de los botones
st.markdown("""
<style>

/* Botones de la navbar */

.stButton > button{

    background-color: transparent;

    border: none;

    color: white;

    font-size:16px;

    font-weight:600;

    padding:0;

}

/* Hover */

.stButton > button:hover{

    color:#4CC9F0;

    background-color: transparent;

    border:none;

}

/* Botón activo */

.stButton > button:focus{

    box-shadow:none;

}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

.block-container{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)
espacio1, col_logo, espacio2, c1, c2, c3 = st.columns([2,2,1,1.5,1.5,1]) #agrego un espacio a la izquierda y a la derecha del logo para centrarlo
#columna para el logo
with col_logo:
 st.markdown(
    """
    <h1 style="
        font-size:25px;
        margin:0;
        padding:0;
    ">
    ⚽ xGLab
    </h1>
    """,
    unsafe_allow_html=True
)

#columnas para los botones de la navbar
with c1:
     if st.button("Registrar tiros"):
        st.session_state["pagina"] = "Registrar"

with c2:
     if st.button("Análisis de tiros"):
        st.session_state["pagina"] = "Analisis"

with c3:
    if st.button("Acerca de"):
        st.session_state["pagina"] = "Acerca"

if "shots" not in st.session_state:
    st.session_state["shots"] = []

if "last_click" not in st.session_state:
    st.session_state["last_click"] = None


#definimos por defecto la página a mostrar al iniciar la app
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Registrar"

pagina = st.session_state["pagina"]

# ==================================================
# LOGGER
# ==================================================

if pagina == "Registrar":
    st.markdown(
    """
    <div style="
    text-align:center;
    margin-top:50px;
    margin-bottom:70px;
    ">

    <h2>Calculadora y análisis de tiros</h2>

    </div>
    """,
    unsafe_allow_html=True)


    espacio_izq, col_form, col_pitch, espacio_der = st.columns(
    [0.6, 1, 2, 0.4])

    with col_form:

        st.subheader("Información del partido")

        jugador = st.text_input(
        "Jugador"
        )

        equipo = st.text_input(
            "Equipo"
        )

        rival = st.text_input(
          "Rival"
        )   

        play_types = {
        "Jugada": {"color": "red", "marker": "o"},
        "Tiro libre": {"color": "blue", "marker": "o"},
        "Corner": {"color": "orange", "marker": "o"},
        "Penal": {"color": "green", "marker": "o"}
        }

        play_type = st.selectbox(
          "Tipo de tiro",
         list(play_types.keys())
        )

    
    pitch = Pitch(
        pitch_type="statsbomb",
        half=False,
        pitch_color="#2E8B57",
        line_color="white",
        pad_left=0,
        pad_right=0,
        pad_top=0,
        pad_bottom=0
    )

    fig, ax = pitch.draw(figsize=(8, 6))

    fig.patch.set_facecolor("#2E8B57")
    ax.set_facecolor("#2E8B57")

    fig.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0
    )

    xmin, xmax = ax.get_xlim()
    ymax, ymin = ax.get_ylim()

    # Dibujar tiros ya cargados

    for shot in st.session_state["shots"]:

        estilo = play_types[shot["tipo"]]

        ax.scatter(
            shot["x"],
            shot["y"],
            s=120,
            c=estilo["color"],
            marker=estilo["marker"]
        )

    ax.set_axis_off()

    fig.savefig(
        "cancha.png",
        bbox_inches="tight",
        pad_inches=0
    )

    with col_pitch:
        value = streamlit_image_coordinates(
        "cancha.png",
        key="cancha"
    )

    if value and value != st.session_state["last_click"]:

        img_width = value["width"]
        img_height = value["height"]

        x_pitch = xmin + (
            value["x"] / img_width
        ) * (xmax - xmin)

        y_pitch = ymin + (
            value["y"] / img_height
        ) * (ymax - ymin)

        angulo = calcular_angulo(
            x_pitch,
            y_pitch
        )

        distancia = calcular_distancia(
            x_pitch,
            y_pitch
        )

        dentro_area_valor = dentro_area(
            x_pitch,
            y_pitch
        )

        free_kick = 0
        penalty = 0

        if play_type == "Tiro libre":
            free_kick = 1

        elif play_type == "Penal":
            penalty = 1

        features = pd.DataFrame(
            {
                "angulo": [angulo],
                "distancia": [distancia],
                "dentro_area": [dentro_area_valor],
                "sub_type_name_Free Kick": [free_kick],
                "sub_type_name_Penalty": [penalty]
            }
        )

        xg = modelo.predict_proba(
            features
        )[0][1]

        st.session_state["shots"].append(
            {
                "jugador": jugador,
                "equipo": equipo,
                "rival": rival,
                "x": round(x_pitch, 2),
                "y": round(y_pitch, 2),
                "tipo": play_type,
                "angulo": round(angulo, 2),
                "distancia": round(distancia, 2),
                "dentro_area": dentro_area_valor,
                "xg": round(xg, 3)
            }
        )

        st.session_state["last_click"] = value

        st.rerun()

    # Tabla

    if st.session_state["shots"]:

        df = pd.DataFrame(
            st.session_state["shots"]
        )

        st.subheader("Tiros registrados")

        st.dataframe(
            df,
            use_container_width=True
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "📥 Descargar CSV",
            csv,
            "shots.csv",
            "text/csv"
        )

        if st.button("🗑️ Limpiar tiros"):

            st.session_state["shots"] = []
            st.session_state["last_click"] = None
            st.rerun()

# ==================================================
# DASHBOARD
# ==================================================

if pagina == "Analisis":

    st.title("Analisis de tiros")

    if len(st.session_state["shots"]) == 0:

        st.warning(
            "No hay tiros cargados. Registrá tiros primero."
        )

        st.stop()

    df = pd.DataFrame(
        st.session_state["shots"]
    )

    # =====================
    # FILTROS
    # =====================

    st.sidebar.header("Filtros")

    jugadores = st.sidebar.multiselect(
        "Jugador",
        options=sorted(df["jugador"].fillna("").unique()),
        default=sorted(df["jugador"].fillna("").unique())
    )

    equipos = st.sidebar.multiselect(
        "Equipo",
        options=sorted(df["equipo"].fillna("").unique()),
        default=sorted(df["equipo"].fillna("").unique())
    )

    rivales = st.sidebar.multiselect(
        "Rival",
        options=sorted(df["rival"].fillna("").unique()),
        default=sorted(df["rival"].fillna("").unique())
    )

    tipos = st.sidebar.multiselect(
        "Tipo de remate",
        options=sorted(df["tipo"].unique()),
        default=sorted(df["tipo"].unique())
    )

    dentro_area_filtro = st.sidebar.multiselect(
        "Dentro del área",
        options=sorted(df["dentro_area"].unique()),
        default=sorted(df["dentro_area"].unique())
    )

    xg_min, xg_max = st.sidebar.slider(
        "Rango de xG",
        min_value=float(df["xg"].min()),
        max_value=float(df["xg"].max()),
        value=(
            float(df["xg"].min()),
            float(df["xg"].max())
        )
    )

    distancia_min, distancia_max = st.sidebar.slider(
        "Rango de distancia",
        min_value=float(df["distancia"].min()),
        max_value=float(df["distancia"].max()),
        value=(
            float(df["distancia"].min()),
            float(df["distancia"].max())
        )
    )

    df_filtrado = df[
        (df["jugador"].isin(jugadores))
        &
        (df["equipo"].isin(equipos))
        &
        (df["rival"].isin(rivales))
        &
        (df["tipo"].isin(tipos))
        &
        (df["dentro_area"].isin(dentro_area_filtro))
        &
        (df["xg"].between(xg_min, xg_max))
        &
        (df["distancia"].between(
            distancia_min,
            distancia_max
        ))
    ]

    # =====================
    # KPIs
    # =====================

    total_shots = len(df_filtrado)

    total_xg = df_filtrado["xg"].sum()

    avg_xg = (
        df_filtrado["xg"].mean()
        if total_shots > 0
        else 0
    )

    inside_pct = (
        df_filtrado["dentro_area"].mean() * 100
        if total_shots > 0
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tiros",
        total_shots
    )

    c2.metric(
        "xG Total",
        round(total_xg, 2)
    )

    c3.metric(
        "xG/Tiro",
        round(avg_xg, 3)
    )

    c4.metric(
        "% Dentro Área",
        round(inside_pct, 1)
    )

    # =====================
    # SHOT MAP
    # =====================

    st.subheader("Shot Map")

    fig = go.Figure()

    # Bordes cancha

    fig.add_shape(
    type="rect",
    x0=0,
    y0=0,
    x1=120,
    y1=80,
    line=dict(width=2)
    )

    # Línea central

    fig.add_shape(
    type="line",
    x0=60,
    y0=0,
    x1=60,
    y1=80
    )

    # Círculo central

    fig.add_shape(
    type="circle",
    x0=50,
    y0=30,
    x1=70,
    y1=50
    )

    # Área izquierda

    fig.add_shape(
    type="rect",
    x0=0,
    y0=18,
    x1=18,
    y1=62
    )

    # Área derecha

    fig.add_shape(
    type="rect",
    x0=102,
    y0=18,
    x1=120,
    y1=62
    )

    # Área chica izquierda

    fig.add_shape(
    type="rect",
    x0=0,
    y0=30,
    x1=6,
    y1=50
    )

    # Área chica derecha

    fig.add_shape(
    type="rect",
    x0=114,
    y0=30,
    x1=120,
    y1=50
    )

    # Arco izquierdo

    fig.add_shape(
    type="rect",
    x0=-2,
    y0=36,
    x1=0,
    y1=44
    )

    # Arco derecho

    fig.add_shape(
    type="rect",
    x0=120,
    y0=36,
    x1=122,
    y1=44
    )

    # Punto penal izquierdo

    fig.add_shape(
    type="circle",
    x0=11-0.4,
    y0=40-0.4,
    x1=11+0.4,
    y1=40+0.4
    )

    # Punto penal derecho

    fig.add_shape(
    type="circle",
    x0=109-0.4,
    y0=40-0.4,
    x1=109+0.4,
    y1=40+0.4
    )

    # Punto central

    fig.add_shape(
    type="circle",
    x0=60-0.4,
    y0=40-0.4,
    x1=60+0.4,
    y1=40+0.4
    )

    fig.add_trace(
        go.Scatter(
            x=df_filtrado["x"],
            y=df_filtrado["y"],
            mode="markers",
            marker=dict(
                size=df_filtrado["xg"] * 80 + 8,
                color="white",
                line=dict(
                    color="black",
                    width=1
                )  
            ),
            customdata=df_filtrado[
                [
                    "jugador",
                    "equipo",
                    "rival",
                    "tipo",
                    "distancia",
                    "angulo",
                    "xg"
                ]
            ],
            hovertemplate=
            "<b>%{customdata[0]}</b><br>"
            + "Rival: %{customdata[2]}<br>"
            + "Tipo: %{customdata[3]}<br>"
            + "Distancia: %{customdata[4]:.1f}<br>"
            + "xG: %{customdata[6]:.3f}"
            + "<extra></extra>"
        )
    )
    fig.update_layout(
        height=700,
        showlegend=False,
        plot_bgcolor="#2E8B57",
        paper_bgcolor="#2E8B57",
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        )
    )

    fig.update_xaxes(
    range=[0, 120],
    visible=False,
    fixedrange=True
    )

    fig.update_yaxes(
    range=[0, 80],
    visible=False,
    scaleanchor="x",
    scaleratio=1,
    fixedrange=True
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )



    # =====================
    # Análisis
    # =====================

    ocasion_mas_clara = (
        df_filtrado["xg"].max()
        if total_shots > 0
        else 0
    )

    distancia_media = (
        df_filtrado["distancia"].mean()
        if total_shots > 0
        else 0
    )

    st.subheader("Análisis")

    texto = []

    texto.append(
        f"El equipo registró {total_shots} remates con un xG acumulado de {total_xg:.2f}."
    )

    texto.append(
        f"La calidad media de los disparos fue de {avg_xg:.3f} xG por remate."
    )

    texto.append(
        f"El {inside_pct:.1f}% de los intentos se realizaron dentro del área."
    )

    texto.append(
        f"La distancia promedio de remate fue de {distancia_media:.1f} metros."
    )

    texto.append(
        f"La ocasión más clara generada alcanzó un valor de {ocasion_mas_clara:.2f} xG."
    )

    for t in texto:
        st.write("•", t)

    st.markdown("### Conclusión")

    if total_xg >= 2:
        nivel = "alta"
    elif total_xg >= 1:
        nivel = "moderada"
    else:
        nivel = "reducida"

    st.info(
        f"El equipo generó una producción ofensiva {nivel}, acumulando "
        f"{total_xg:.2f} xG en {total_shots} remates. "
        f"El {inside_pct:.1f}% de los disparos se produjo dentro del área y "
        f"la ocasión de mayor peligro alcanzó {ocasion_mas_clara:.2f} xG."
    )

if pagina == "Acerca":

    # =====================================
    # TITULO
    # =====================================

    st.markdown("""
    <div style="
        text-align:center;
        margin-top:30px;
        margin-bottom:50px;
    ">
        <h1>Acerca de xGLab</h1>


    </div>
    """, unsafe_allow_html=True)

    # =====================================
    # DOS COLUMNAS PRINCIPALES
    # =====================================

    col_mision, col_features = st.columns([1,1])

    # =====================================
    # MISION
    # =====================================

    with col_mision:

        st.markdown("## Nuestra Misión")

        st.markdown("""
        En xGLab nuestra misión es democratizar el análisis
        de datos en el fútbol.

        Queremos que entrenadores, analistas, jugadores y
        aficionados tengan acceso a herramientas intuitivas
        que les permitan comprender mejor el juego y tomar
        decisiones basadas en datos.

        Creemos que los datos pueden transformar la manera
        en que entendemos el fútbol y xGLab nace para ser
        tu aliado en ese camino.
        """)

        st.markdown("<br>", unsafe_allow_html=True)

        # Card xG

        st.markdown("""
        <div style="
            padding:25px;
            border-radius:15px;
            border:1px solid rgba(255,255,255,0.1);
            background-color: rgba(255,255,255,0.03);
        ">

        <h3>¿Qué es xG?</h3>

        <p>
        El Expected Goals (xG) mide la calidad de un tiro
        considerando factores como la distancia, el ángulo,
        la ubicación y el contexto de la jugada.
        </p>

        <p>
        No es una predicción exacta, sino una métrica que
        ayuda a entender qué oportunidades tenían más
        probabilidades de convertirse en gol.
        </p>

        </div>
        """, unsafe_allow_html=True)

    # =====================================
    # FEATURES
    # =====================================

    with col_features:

        st.markdown("## Características")

        features = [
            (
                "1",
                "Registro de tiros",
                "Marca tiros sobre el mapa de la cancha de forma sencilla."
            ),
            (
                "2",
                "Cálculo de xG",
                "Obtén la probabilidad de gol utilizando un modelo entrenado."
            ),
            (
                "3",
                "KPIs y análisis",
                "Visualiza métricas para evaluar rendimiento individual y colectivo."
            ),
            (
                "4",
                "Exportación",
                "Descarga los datos registrados en formato CSV."
            )
        ]

        for numero, titulo, descripcion in features:

            st.markdown(f"""
            <div style="
                padding:20px;
                margin-bottom:15px;
                border-radius:15px;
                border:1px solid rgba(255,255,255,0.08);
                background-color: rgba(255,255,255,0.03);
            ">

            <h4>
            {numero}. {titulo}
            </h4>

            <p style="color:#B8B8B8;">
            {descripcion}
            </p>

            </div>
            """, unsafe_allow_html=True)
            
st.markdown("---")

st.markdown("""
<div style="
    text-align:center;
    padding:20px;
    margin-top:25px;
    color:#B0B0B0;
    font-size:14px;
">
    <p><strong>xGLab</strong></p>
    <p> Mail: contacto@xglab.com</p>
    <p> Tel: +54 11 1234-5678</p>
</div>
""", unsafe_allow_html=True)
        