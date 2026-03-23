# ================================
# 📦 IMPORTACIONES
# ================================
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import os

# 🤖 OpenAI
from openai import OpenAI

# Cliente IA (usa variable de entorno)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

px.defaults.template = "plotly_dark"

# ================================
# 📥 CARGA DE DATOS
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "clinical_analytics.csv")

df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

df['Appt Start Time'] = pd.to_datetime(df['Appt Start Time'], errors='coerce')
df = df.dropna(subset=['Appt Start Time'])

# ================================
# 🤖 FUNCIÓN IA (OPENAI)
# ================================
def generar_insights(data):

    if data.empty:
        return "No hay datos disponibles."

    resumen = {
        "total_pacientes": int(len(data)),
        "espera_promedio": float(data['Wait Time Min'].mean()),
        "satisfaccion_promedio": float(data['Care Score'].mean()),
        "top_clinica": str(data['Clinic Name'].value_counts().idxmax()),
        "top_departamento": str(data['Department'].value_counts().idxmax())
    }

    prompt = f"""
    Eres un analista de datos clínicos experto.

    Analiza estos datos:
    {resumen}

    Dame:
    - Insights clave
    - Problemas detectados
    - Recomendaciones claras

    Responde en español, profesional y breve.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres experto en análisis de datos de salud."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error IA: {str(e)}"


# ================================
# 🚀 APP
# ================================
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server

# ================================
# 🎨 ESTILOS
# ================================
CARD_STYLE = {
    "borderRadius": "15px",
    "boxShadow": "0px 4px 15px rgba(0,0,0,0.5)",
    "padding": "15px"
}

KPI_STYLE = {
    "textAlign": "center",
    "padding": "20px"
}

# ================================
# 🎨 LAYOUT
# ================================
app.layout = dbc.Container([

    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("🏥 Dashboard Clínico Inteligente (IA)", className="fw-bold fs-4"),
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    ),

    # FILTROS
    dbc.Card([
        dbc.CardBody([
            dbc.Row([

                dbc.Col([
                    html.Label("📅 Fecha"),
                    dcc.DatePickerRange(
                        id='filtro_fecha',
                        start_date=df['Appt Start Time'].min(),
                        end_date=df['Appt Start Time'].max()
                    )
                ], md=4),

                dbc.Col([
                    html.Label("🏥 Clínica"),
                    dcc.Dropdown(
                        id='filtro_clinica',
                        options=[{'label': c, 'value': c} for c in df['Clinic Name'].dropna().unique()],
                        multi=True
                    )
                ], md=4),

                dbc.Col([
                    html.Label("🚑 Fuente"),
                    dcc.Dropdown(
                        id='filtro_fuente',
                        options=[{'label': s, 'value': s} for s in df['Admit Source'].dropna().unique()],
                        multi=True
                    )
                ], md=4),

            ])
        ])
    ], style=CARD_STYLE, className="mb-4"),

    # KPIs
    dbc.Row([
        dbc.Col(html.Div(id="kpi_pacientes"), md=4),
        dbc.Col(html.Div(id="kpi_espera"), md=4),
        dbc.Col(html.Div(id="kpi_satisfaccion"), md=4),
    ], className="mb-4"),

    # GRÁFICOS
    dbc.Row([

        dbc.Col(
            dbc.Card([dcc.Graph(id="grafico_volumen")], style=CARD_STYLE),
            md=4
        ),

        dbc.Col(
            dbc.Card([dcc.Graph(id="grafico_espera")], style=CARD_STYLE),
            md=4
        ),

        dbc.Col(
            dbc.Card([dcc.Graph(id="grafico_satisfaccion")], style=CARD_STYLE),
            md=4
        ),

    ]),

    # 🤖 PANEL IA
    dbc.Card([
        dbc.CardBody([
            html.H4("🤖 Insights Automáticos con IA"),
            html.Div(id="insights_ia", style={"fontSize": "18px"})
        ])
    ], className="mt-4", style=CARD_STYLE)

], fluid=True)

# ================================
# 🔄 CALLBACK
# ================================
@app.callback(
    [
        Output("grafico_volumen", "figure"),
        Output("grafico_espera", "figure"),
        Output("grafico_satisfaccion", "figure"),
        Output("kpi_pacientes", "children"),
        Output("kpi_espera", "children"),
        Output("kpi_satisfaccion", "children"),
        Output("insights_ia", "children"),
    ],
    [
        Input("filtro_fecha", "start_date"),
        Input("filtro_fecha", "end_date"),
        Input("filtro_clinica", "value"),
        Input("filtro_fuente", "value"),
    ]
)
def actualizar_dashboard(fecha_inicio, fecha_fin, clinicas, fuentes):

    datos = df.copy()

    # FILTROS
    if fecha_inicio and fecha_fin:
        datos = datos[
            (datos['Appt Start Time'] >= fecha_inicio) &
            (datos['Appt Start Time'] <= fecha_fin)
        ]

    if clinicas:
        datos = datos[datos['Clinic Name'].isin(clinicas)]

    if fuentes:
        datos = datos[datos['Admit Source'].isin(fuentes)]

    # 📊 VOLUMEN
    volumen = datos.groupby("Clinic Name").size().reset_index(name="Pacientes")

    fig_volumen = px.bar(
        volumen,
        x="Clinic Name",
        y="Pacientes",
        color="Pacientes",
        title="Volumen de Pacientes",
        text_auto=True
    )

    # ⏳ ESPERA
    fig_espera = px.box(
        datos,
        x="Department",
        y="Wait Time Min",
        color="Department",
        title="Tiempo de Espera"
    )

    # ⭐ SATISFACCIÓN
    fig_satisfaccion = px.histogram(
        datos,
        x="Care Score",
        color="Department",
        title="Satisfacción",
        nbins=20
    )

    # KPIs
    total = len(datos)
    avg_wait = round(datos['Wait Time Min'].mean(), 2)
    avg_score = round(datos['Care Score'].mean(), 2)

    kpi_pacientes = dbc.Card(dbc.CardBody([
        html.H6("Pacientes"),
        html.H2(total)
    ]), style=KPI_STYLE)

    kpi_espera = dbc.Card(dbc.CardBody([
        html.H6("Espera Promedio"),
        html.H2(avg_wait)
    ]), style=KPI_STYLE)

    kpi_satisfaccion = dbc.Card(dbc.CardBody([
        html.H6("Satisfacción"),
        html.H2(avg_score)
    ]), style=KPI_STYLE)

    # 🤖 IA REAL
    insights = generar_insights(datos)

    return (
        fig_volumen,
        fig_espera,
        fig_satisfaccion,
        kpi_pacientes,
        kpi_espera,
        kpi_satisfaccion,
        insights
    )


# ================================
# ▶️ RUN
# ================================
if __name__ == "__main__":
    app.run(debug=True)