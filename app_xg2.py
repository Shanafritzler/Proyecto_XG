import streamlit as st
from mplsoccer import Pitch
import pandas as pd
from streamlit_image_coordinates import streamlit_image_coordinates
from funciones import (calcular_angulo, calcular_distancia, dentro_area)

import joblib

@st.cache_resource
def cargar_modelo():
    return joblib.load("modelo_xg.pkl")

modelo = cargar_modelo()

st.title("SHOT LOGGER")

# ---------------- ESTADOS ----------------

if "shots" not in st.session_state:
    st.session_state["shots"] = []

if "last_click" not in st.session_state:
    st.session_state["last_click"] = None

#metadatos
st.subheader("Información del partido")

jugador = st.text_input("Jugador")

equipo = st.text_input("Equipo")

rival = st.text_input("Rival")

# ---------------- TIPOS DE TIRO ----------------

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

# ---------------- CREAR CANCHA ----------------

pitch = Pitch(
    pitch_type="statsbomb",
    half=False,
    pitch_color="white",
    line_color="black",
 
)
fig, ax = pitch.draw(figsize=(7, 5))

# Eliminar márgenes de matplotlib
#fig.subplots_adjust(
  #  left=0,
   # right=1,
    #top=1,
    #bottom=0
#)

# Obtener dimensiones reales de la cancha
xmin, xmax = ax.get_xlim()
ymax, ymin = ax.get_ylim()


# ---------------- DIBUJAR TIROS EXISTENTES ----------------

for shot in st.session_state["shots"]:

    estilo = play_types[shot["tipo"]]

    ax.scatter(
        shot["x"],
        shot["y"],
        s=120,
        c=estilo["color"],
        marker=estilo["marker"]
    )

# Ocultar ejes
ax.set_axis_off()

# Guardar imagen temporal
fig.savefig(
    "cancha.png",
    bbox_inches="tight",
    pad_inches=0
)

# ---------------- IMAGEN CLICKEABLE ----------------

value = streamlit_image_coordinates(
    "cancha.png",
    key="cancha"
)

# ---------------- REGISTRAR NUEVO TIRO ----------------

if value and value != st.session_state["last_click"]:

    img_width = value["width"]
    img_height = value["height"]

    #Convertir el click a coordenadas reales
    x_pitch = xmin + (value["x"] / img_width) * (xmax - xmin)

    y_pitch = ymin + (value["y"] / img_height) * (ymax - ymin)
      # ---------------- CALCULAR VARIABLES ----------------

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

    # Variables dummy
    free_kick = 0
    penalty = 0


    if play_type == "Tiro libre":
        free_kick = 1

    elif play_type == "Penal":
        penalty = 1

    # ---------------- CREAR FEATURES ----------------

    features = pd.DataFrame(
        {
            "angulo":[angulo],
            "distancia":[distancia],
            "dentro_area":[dentro_area_valor],
            "sub_type_name_Free Kick":[free_kick],
            "sub_type_name_Penalty":[penalty]
        }
    )

    # ---------------- PREDECIR xG ----------------

    xg = modelo.predict_proba(
        features
    )[0][1]

    # ---------------- GUARDAR ----------------

    st.session_state["shots"].append(
        {
                 
                "jugador": jugador,
                "equipo": equipo,
                "rival": rival,
                "x": round(x_pitch,2),
                "y": round(y_pitch,2),
                "tipo": play_type,
                "angulo": round(angulo,2),
                "distancia": round(distancia,2),
                "dentro_area": dentro_area_valor,
                "xg": round(xg,3)
}
        
    )

    st.session_state["last_click"] = value

    st.rerun()


# ---------------- TABLA ----------------

if st.session_state["shots"]:

    df = pd.DataFrame(
        st.session_state["shots"]
    )

    st.dataframe(df)

# ---------------- EXPORTAR CSV ----------------

    csv = df.to_csv(
        index=False
        ).encode("utf-8")

    st.download_button(
        label=" Descargar CSV",
        data=csv,
        file_name="shots.csv",
        mime="text/csv"
    )