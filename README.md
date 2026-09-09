# Agente de IA - Analisis de Costos Operativos (DataKnow)

Agente conversacional que expone los resultados de un proyecto de analisis de
costos para una empresa de construccion (identificacion de materias primas,
seleccion de variables, y proyeccion de costos con intervalos de confianza).

## Por que es un agente y no solo un chatbot

El modelo (Gemini) decide por si mismo, segun la pregunta del usuario, si
necesita usar alguna de las 3 herramientas disponibles, en vez de seguir un
guion fijo. Esa autonomia en la decision es la diferencia central entre un
agente de IA y un sistema de IA convencional.

## Las 3 herramientas

| Herramienta | Que hace |
|---|---|
| `obtener_pronostico_local` | Consulta los hallazgos del proyecto (identificacion de materias primas, proyeccion de costos, etc.) guardados en `resultados/resultados_proyecto.json` |
| `buscar_noticias_mercado` | Busca noticias reales y actuales de mercado (gratis, via DuckDuckGo) |
| `simular_sensibilidad` | Calcula que pasaria con el costo de un equipo si su materia prima dominante subiera o bajara un porcentaje dado, usando la relacion estadistica ya verificada entre ambas variables |

## Estructura

```
.
├── agent.py                 # Logica del agente: herramientas y bucle de decision
├── app.py                    # Interfaz de chat (Streamlit)
├── requirements.txt           # Dependencias
├── resultados/
│   └── resultados_proyecto.json   # Hallazgos del analisis de costos
└── .gitignore
```

## Ejemplos de preguntas

- ¿Que materia prima identificaron para Price_X, Price_Y y Price_Z?
- ¿Cual es la proyeccion de costo para el Equipo 1 a 30 dias?
- ¿Que pasaria con el costo del Equipo 1 si el precio del acero sube 10%?
- ¿Que esta pasando actualmente con el precio del acero?
