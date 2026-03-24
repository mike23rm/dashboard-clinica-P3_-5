# ================================
# 📦 IMPORTACIONES
# ================================
# Librería para manejo de datos (DataFrames)
import pandas as pd

# Librería para gráficos interactivos
import plotly.express as px

# Componentes principales de Dash (framework web)
from dash import Dash, html, dcc, Input, Output

# Componentes con estilos Bootstrap
import dash_bootstrap_components as dbc

# Librería para manejar rutas de archivos
import os


# ================================
# 🎨 CONFIG GLOBAL
# ================================
# Tema global de gráficos (oscuro)
px.defaults.template = "plotly_dark"

# Diccionario de colores personalizados para todo el dashboard
COLORS = {
    "primary": "#4F46E5",    # Azul principal
    "secondary": "#06B6D4",  # Celeste
    "success": "#10B981",    # Verde
    "warning": "#F59E0B",    # Amarillo
    "danger": "#EF4444",     # Rojo
    "bg": "#0F172A",         # Fondo general
    "card": "#1E293B",       # Fondo de tarjetas
    "text": "#E2E8F0"        # Texto
}


# ================================
# 📥 CARGA DE DATOS
# ================================
# Obtiene la ruta del archivo actual (para evitar errores en Render o servidores)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construye la ruta completa del CSV
file_path = os.path.join(BASE_DIR, "clinical_analytics.csv")

# Lee el archivo CSV
df = pd.read_csv(file_path)

# Limpia espacios en nombres de columnas
df.columns = df.columns.str.strip()

# Convierte la columna de fecha a formato datetime
df["Appt Start Time"] = pd.to_datetime(df["Appt Start Time"], errors="coerce")

# Elimina filas con fechas inválidas o vacías
df = df.dropna(subset=["Appt Start Time"])


# ================================
# 🚀 APP
# ================================
# Inicializa la aplicación Dash con tema Bootstrap oscuro
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Necesario para despliegue en Render/Heroku
server = app.server


# ================================
# 🎨 COMPONENTES REUTILIZABLES
# ================================
# Tarjeta KPI reutilizable (métricas principales)
def kpi_card(title, value, color):
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="text-muted"),  # Título pequeño
            html.H2(value, style={"color": color, "fontWeight": "bold"})  # Valor principal
        ]),
        style={
            "borderRadius": "15px",
            "background": COLORS["card"],
            "boxShadow": "0px 4px 15px rgba(0,0,0,0.4)"
        }
    )

# Tarjeta contenedora para gráficos
def graph_card(graph):
    return dbc.Card(
        dbc.CardBody(graph),
        style={
            "borderRadius": "15px",
            "background": COLORS["card"],
            "boxShadow": "0px 4px 15px rgba(0,0,0,0.4)"
        }
    )


# ================================
# 🎨 LAYOUT (DISEÑO)
# ================================
app.layout = dbc.Container([

    # 🔷 HEADER (barra superior)
    dbc.Navbar(
        dbc.Container([
            html.Div([
                html.H3("🏥 Dashboard Clínico", className="fw-bold mb-0"),
                html.Small("Analítica avanzada de pacientes", className="text-muted")
            ])
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    ),

    # 🔎 FILTROS
    dbc.Card([
        dbc.CardBody([
            dbc.Row([

                # Filtro por rango de fechas
                dbc.Col([
                    html.Label("📅 Fechas"),
                    dcc.DatePickerRange(
                        id="filtro_fecha",
                        start_date=df["Appt Start Time"].min(),
                        end_date=df["Appt Start Time"].max(),
                    ),
                ], md=4),

                # Filtro por clínica
                dbc.Col([
                    html.Label("🏥 Clínica"),
                    dcc.Dropdown(
                        id="filtro_clinica",
                        options=[{"label": c, "value": c} for c in df["Clinic Name"].dropna().unique()],
                        multi=True,
                    ),
                ], md=4),

                # Filtro por fuente de ingreso
                dbc.Col([
                    html.Label("🚑 Fuente"),
                    dcc.Dropdown(
                        id="filtro_fuente",
                        options=[{"label": s, "value": s} for s in df["Admit Source"].dropna().unique()],
                        multi=True,
                    ),
                ], md=4),

            ])
        ])
    ], className="mb-4", style={"background": COLORS["card"], "borderRadius": "15px"}),

    # 📊 KPIs (indicadores)
    dbc.Row([
        dbc.Col(html.Div(id="kpi_pacientes"), md=4),
        dbc.Col(html.Div(id="kpi_espera"), md=4),
        dbc.Col(html.Div(id="kpi_satisfaccion"), md=4),
    ], className="mb-4"),

    # 📈 GRÁFICOS PRINCIPALES
    dbc.Row([
        dbc.Col(graph_card(dcc.Graph(id="grafico_volumen")), md=6),
        dbc.Col(graph_card(dcc.Graph(id="grafico_tiempo")), md=6),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(graph_card(dcc.Graph(id="grafico_espera")), md=6),
        dbc.Col(graph_card(dcc.Graph(id="grafico_satisfaccion")), md=6),
    ])

], fluid=True)


# ================================
# 🔄 CALLBACK (LÓGICA DINÁMICA)
# ================================
@app.callback(
    [
        Output("grafico_volumen", "figure"),
        Output("grafico_espera", "figure"),
        Output("grafico_satisfaccion", "figure"),
        Output("grafico_tiempo", "figure"),
        Output("kpi_pacientes", "children"),
        Output("kpi_espera", "children"),
        Output("kpi_satisfaccion", "children"),
    ],
    [
        Input("filtro_fecha", "start_date"),
        Input("filtro_fecha", "end_date"),
        Input("filtro_clinica", "value"),
        Input("filtro_fuente", "value"),
    ],
)
def actualizar_dashboard(inicio, fin, clinicas, fuentes):

    # Copia del dataset original
    datos = df.copy()

    # Filtrado por fechas
    if inicio and fin:
        datos = datos[
            (datos["Appt Start Time"] >= inicio) &
            (datos["Appt Start Time"] <= fin)
        ]

    # Filtrado por clínica
    if clinicas:
        datos = datos[datos["Clinic Name"].isin(clinicas)]

    # Filtrado por fuente
    if fuentes:
        datos = datos[datos["Admit Source"].isin(fuentes)]

    # ================================
    # 📊 GRÁFICOS
    # ================================

    # Volumen de pacientes por clínica
    volumen = datos.groupby("Clinic Name").size().reset_index(name="Pacientes")
    volumen = volumen.sort_values("Pacientes", ascending=False)

    fig_volumen = px.bar(
        volumen,
        x="Clinic Name",
        y="Pacientes",
        color="Pacientes",
        color_continuous_scale="Blues",
        title="Pacientes por Clínica"
    )

    # Tendencia de pacientes en el tiempo
    tendencia = datos.groupby(datos["Appt Start Time"].dt.date).size().reset_index(name="Pacientes")

    fig_tiempo = px.line(
        tendencia,
        x="Appt Start Time",
        y="Pacientes",
        markers=True,
        title="Tendencia de Pacientes"
    )

    # Distribución del tiempo de espera
    fig_espera = px.box(
        datos,
        x="Department",
        y="Wait Time Min",
        color="Department",
        title="Distribución de Tiempo de Espera"
    )

    # Distribución de satisfacción del paciente
    fig_satisfaccion = px.histogram(
        datos,
        x="Care Score",
        nbins=20,
        color_discrete_sequence=[COLORS["secondary"]],
        title="Distribución de Satisfacción"
    )

    # ================================
    # 📊 KPIs
    # ================================
    total = len(datos)  # Total pacientes
    avg_wait = round(datos["Wait Time Min"].mean(), 2)  # Promedio espera
    avg_score = round(datos["Care Score"].mean(), 2)    # Promedio satisfacción

    # Retorna todos los outputs
    return (
        fig_volumen,
        fig_espera,
        fig_satisfaccion,
        fig_tiempo,
        kpi_card("Pacientes", total, COLORS["primary"]),
        kpi_card("Espera Promedio", avg_wait, COLORS["warning"]),
        kpi_card("Satisfacción", avg_score, COLORS["success"]),
    )


# ================================
# ▶️ EJECUCIÓN
# ================================
# Ejecuta la app en modo local
if __name__ == "__main__":
    app.run()