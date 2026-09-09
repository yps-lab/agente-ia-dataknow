"""
agent.py

Logica del agente. En simple: el modelo (Gemini) recibe una pregunta y decide por
si mismo si necesita usar alguna de las 3 herramientas disponibles antes de
responder. Esa decision autonoma (no un "if/else" fijo escrito por nosotros) es
lo que distingue a un agente de un sistema de IA convencional.

Flujo (el mismo patron, sin importar cuantas herramientas tenga el agente):
1. El usuario pregunta algo.
2. Se la mandamos a Gemini junto con la descripcion de las 3 herramientas.
3. Gemini responde "quiero usar la herramienta X con estos parametros"
   (todavia no da la respuesta final).
4. Ejecutamos esa funcion en nuestro codigo, y le devolvemos el resultado.
5. Gemini usa ese resultado (y puede pedir otra herramienta si lo necesita)
   hasta dar la respuesta final al usuario.

"""

import json
import time
from ddgs import DDGS
from google import genai
from google.genai import errors, types

cliente = genai.Client()  # lee la API key de la variable de entorno GEMINI_API_KEY

MODELO = "gemini-3.5-flash-lite"
RUTA_RESULTADOS = "resultados/resultados_proyecto.json"


def llamar_a_gemini_con_reintentos(contenidos, config, intentos_maximos=3):
    """
    Llama a Gemini con reintentos automaticos si el servidor esta temporalmente
    saturado (error 503). Espera un poco mas de tiempo en cada intento fallido
    (2, luego 4, luego 8 segundos) antes de rendirse.
    """
    for intento in range(intentos_maximos):
        try:
            return cliente.models.generate_content(
                model=MODELO, contents=contenidos, config=config
            )
        except errors.ServerError:
            if intento == intentos_maximos - 1:
                raise  # ya se agotaron los intentos, dejamos que el error se muestre
            espera = 2 ** (intento + 1)  # 2, 4, 8 segundos
            time.sleep(espera)


# ---------------------------------------------------------------------------
# Herramienta 1: consultar los resultados del proyecto (JSON local)
# ---------------------------------------------------------------------------
def obtener_pronostico_local(seccion: str) -> str:
    """
    Lee el archivo local de resultados (ya calculados previamente) y devuelve la seccion pedida: identificacion de materias primas,
    seleccion de variables, verificacion de la relacion materia prima-equipo,
    proyeccion de costos, hallazgos clave, o limitaciones.
    """
    with open(RUTA_RESULTADOS, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if seccion not in datos:
        return f"No existe la seccion '{seccion}'. Secciones disponibles: {list(datos.keys())}"

    return json.dumps(datos[seccion], ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Herramienta 2: buscar noticias reales de mercado (gratis, sin API key)
# ---------------------------------------------------------------------------
def buscar_noticias_mercado(consulta: str) -> str:
    """
    Busca noticias reales y actuales en internet usando DuckDuckGo (gratis,
    sin necesidad de una API key adicional). Devuelve los primeros resultados
    como texto plano para que el modelo los resuma.
    """
    with DDGS() as buscador:
        resultados = list(buscador.text(consulta, max_results=5))

    if not resultados:
        return "No se encontraron noticias para esa consulta."

    texto = "\n\n".join(
        f"Titulo: {r['title']}\nResumen: {r['body']}\nFuente: {r['href']}"
        for r in resultados
    )
    return texto


# ---------------------------------------------------------------------------
# Herramienta 3 (diferenciadora): simulador de sensibilidad financiera
# ---------------------------------------------------------------------------
def simular_sensibilidad(equipo: str, cambio_porcentual_materia_prima: float) -> str:
    """
    Responde "que pasaria si" el precio de la materia prima dominante subiera o
    bajara un cierto porcentaje, usando la ecuacion de regresion ya confirmada
    en el notebook 3 (Equipo = intercepto + coeficiente * materia_prima).
    No es una tecnica nueva: es la misma formula ya verificada, aplicada a un
    escenario hipotetico en vez de al precio actual.
    """
    with open(RUTA_RESULTADOS, "r", encoding="utf-8") as f:
        datos = json.load(f)

    relaciones = datos["verificacion_relacion_niveles"]
    clave = f"{equipo}_vs_Price_Y" if equipo == "Price_Equipo1" else f"{equipo}_vs_Price_Z"

    if clave not in relaciones:
        return f"No hay una relacion confirmada para '{equipo}'. Usa 'Price_Equipo1' o 'Price_Equipo2'."

    relacion = relaciones[clave]
    a = relacion["intercepto_a"]
    b = relacion["coeficiente_b"]
    precio_materia_actual = relacion["precio_actual_materia_prima"]

    precio_materia_simulado = precio_materia_actual * (1 + cambio_porcentual_materia_prima / 100)
    precio_equipo_actual = a + b * precio_materia_actual
    precio_equipo_simulado = a + b * precio_materia_simulado

    cambio_pct_equipo = (precio_equipo_simulado / precio_equipo_actual - 1) * 100

    return json.dumps({
        "equipo": equipo,
        "escenario": f"{cambio_porcentual_materia_prima:+.1f}% en la materia prima dominante",
        "precio_equipo_actual_estimado": round(precio_equipo_actual, 2),
        "precio_equipo_simulado": round(precio_equipo_simulado, 2),
        "cambio_resultante_en_equipo_pct": round(cambio_pct_equipo, 2),
    }, ensure_ascii=False, indent=2)


FUNCIONES_DISPONIBLES = {
    "obtener_pronostico_local": obtener_pronostico_local,
    "buscar_noticias_mercado": buscar_noticias_mercado,
    "simular_sensibilidad": simular_sensibilidad,
}

# ---------------------------------------------------------------------------
# Descripcion de las herramientas para Gemini
# ---------------------------------------------------------------------------
HERRAMIENTAS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="obtener_pronostico_local",
                description=(
                    "Consulta los resultados del proyecto: identificacion de "
                    "materias primas, seleccion de variables, verificacion de la "
                    "relacion materia prima-equipo, proyeccion de costos con "
                    "intervalos de confianza, hallazgos clave o limitaciones."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "seccion": types.Schema(
                            type="STRING",
                            description=(
                                "identificacion_materias_primas, "
                                "seleccion_de_variables, verificacion_relacion_niveles, "
                                "proyeccion_de_costos, hallazgos_clave, o limitaciones."
                            ),
                        )
                    },
                    required=["seccion"],
                ),
            ),
            types.FunctionDeclaration(
                name="buscar_noticias_mercado",
                description=(
                    "Busca noticias reales y actuales sobre un tema de mercado "
                    "(precios de commodities, contexto economico, sector "
                    "industrial). Usar cuando la pregunta pida informacion "
                    "externa o actual que no esta en los resultados del proyecto."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "consulta": types.Schema(
                            type="STRING",
                            description="Los terminos de busqueda.",
                        )
                    },
                    required=["consulta"],
                ),
            ),
            types.FunctionDeclaration(
                name="simular_sensibilidad",
                description=(
                    "Simula que pasaria con el precio de un equipo si el precio "
                    "de su materia prima dominante subiera o bajara un porcentaje "
                    "dado. Usar cuando el usuario pregunte un escenario "
                    "hipotetico del tipo 'que pasa si el precio de X sube o baja'."
                ),
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "equipo": types.Schema(
                            type="STRING",
                            description="'Price_Equipo1' o 'Price_Equipo2'.",
                        ),
                        "cambio_porcentual_materia_prima": types.Schema(
                            type="NUMBER",
                            description="Cambio porcentual a simular, ej. 10 para +10%, -15 para -15%.",
                        ),
                    },
                    required=["equipo", "cambio_porcentual_materia_prima"],
                ),
            ),
        ]
    )
]

PROMPT_SISTEMA = """Eres un asistente que explica los resultados de un proyecto de
analisis de costos operativos para una empresa de construccion. El proyecto identifico
que materias primas (petroleo, acero, aluminio) explican el costo de 2 tipos de equipo,
y proyecto su costo futuro con intervalos de confianza.

Responde de forma clara y concisa, en español. Usa obtener_pronostico_local para
preguntas sobre el analisis realizado, buscar_noticias_mercado para contexto de
mercado actual, y simular_sensibilidad para escenarios hipoteticos de cambio de
precio. Si combinas varias fuentes en una respuesta, dilo explicitamente.
"""


def preguntar_al_agente(pregunta_usuario: str, historial: list = None) -> tuple[str, list]:
    """
    Recibe la pregunta del usuario y devuelve la respuesta del agente, ademas
    del historial actualizado (para que la conversacion tenga memoria de lo
    que ya se hablo).
    """
    if historial is None:
        historial = []

    contenidos = historial + [
        types.Content(role="user", parts=[types.Part(text=pregunta_usuario)])
    ]

    config = types.GenerateContentConfig(
        system_instruction=PROMPT_SISTEMA,
        tools=HERRAMIENTAS,
    )

    respuesta = llamar_a_gemini_con_reintentos(contenidos, config)

    while respuesta.function_calls:
        contenidos.append(respuesta.candidates[0].content)

        partes_resultado = []
        for llamada in respuesta.function_calls:
            nombre_funcion = llamada.name
            argumentos = dict(llamada.args)
            funcion = FUNCIONES_DISPONIBLES[nombre_funcion]
            resultado = funcion(**argumentos)

            partes_resultado.append(
                types.Part.from_function_response(
                    name=nombre_funcion,
                    response={"resultado": resultado},
                )
            )

        contenidos.append(types.Content(role="user", parts=partes_resultado))

        respuesta = llamar_a_gemini_con_reintentos(contenidos, config)

    contenidos.append(respuesta.candidates[0].content)

    return respuesta.text, contenidos
