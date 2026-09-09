"""
app.py

Agente conversacional que responde preguntas sobre los resultados del proyecto de
analisis de costos (identificacion de materias primas, seleccion de variables,
proyeccion de costos) y puede buscar contexto de mercado actual en internet.

La API key de Gemini se lee desde "Secrets" de Streamlit Cloud (si esta
desplegada en linea) o desde la variable de entorno GEMINI_API_KEY (si corre
localmente); ver agent.py para el detalle de esa logica.
"""

import os
import streamlit as st

# Si la API key esta guardada en "Secrets" de Streamlit Cloud (para cuando se
# despliega en internet), la copiamos a la variable de entorno que agent.py
# espera. Si no existe (por ejemplo, corriendo en tu computadora con la
# variable de entorno ya configurada), simplemente se ignora este paso.
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

from agent import preguntar_al_agente

st.set_page_config(page_title="Agente de Analisis de Costos", page_icon="🤖")

st.title("🤖 Agente de Analisis de Costos Operativos")
st.markdown(
    "Preguntame sobre los resultados del proyecto (identificacion de materias primas, "
    "seleccion de variables, proyeccion de costos) o pideme contexto de mercado actual."
)

# El historial de la conversacion se guarda en la sesion de Streamlit,
# para que el agente recuerde lo que ya se hablo.
if "historial_visible" not in st.session_state:
    st.session_state.historial_visible = []  # lo que se muestra en pantalla
if "historial_api" not in st.session_state:
    st.session_state.historial_api = []  # lo que se le manda a Gemini (formato interno)

# Mostrar la conversacion ya existente
for mensaje in st.session_state.historial_visible:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

# Ejemplos de preguntas, para que el usuario sepa que puede preguntar
with st.expander("Ejemplos de preguntas"):
    st.markdown("""
    - ¿Qué materia prima identificaron para Price_X, Price_Y y Price_Z?
    - ¿Cuál es la proyección de costo para el Equipo 1 a 30 días?
    - ¿Por qué se descartó Price_X como variable explicativa?
    - ¿Qué pasaría con el costo del Equipo 1 si el precio del acero sube 10%?
    - ¿Qué pasaría con el costo del Equipo 2 si el precio del aluminio baja 15%?
    - ¿Qué está pasando actualmente con el precio del acero?
    """)

# Caja de texto para escribir la pregunta
pregunta = st.chat_input("Escribe tu pregunta aqui...")

if pregunta:
    # Mostrar la pregunta del usuario en pantalla
    st.session_state.historial_visible.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)

    # Llamar al agente
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            respuesta_texto, nuevo_historial_api = preguntar_al_agente(
                pregunta, st.session_state.historial_api
            )
            st.markdown(respuesta_texto)

    # Guardar la respuesta en el historial
    st.session_state.historial_visible.append({"role": "assistant", "content": respuesta_texto})
    st.session_state.historial_api = nuevo_historial_api
