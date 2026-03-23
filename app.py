# ================================
# 📦 IMPORTACIONES
# ================================
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import os

px.defaults.template = "simple_white"

# ================================
# 📥 CARGA DE DATOS (FIX RENDER)
# ================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "clinical_analytics.csv")

df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# ✅ FIX DEFINITIVO (SIN infer_datetime_format)
df["Appt Start Time"] = pd.to_datetime(
    df["Appt Start Time"],
    errors="coerce"
)

df = df.dropna(subset=["Appt Start Time"])

# ================================
# 🚀 APP + SERVER
# ================================
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server  # 🔥 CLAVE

# ================================
# 🎨 ESTILOS
# ================================
CARD_STYLE = {
    "borderRadius": "15px",
    "boxShadow": "0px 4px 10px rgba(0,0,0,0.4)",
    "padding": "10px",
}

# ================================
# 🎨 LAYOUT
# ================================
app.layout = dbc.Container([
    
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("🏥 Dashboard Clínico", className="fw-bold fs-4"),
        ]),
        color="dark",
        dark=True,
        className="mb-4",
    ),

    dbc.Card([
        dbc.CardBody([
            dbc.Row([

                dbc.Col([
                    html.Label("📅 Rango de fechas"),
                    dcc.DatePickerRange(
                        id="filtro_fecha",
                        start_date=df["Appt Start Time"].min(),
                        end_date=df["Appt Start Time"].max(),
                    ),
                ], md=4),

                dbc.Col([
                    html.Label("🏥 Clínica"),
                    dcc.Dropdown(
                        id="filtro_clinica",
                        options=[{"label": c, "value": c} for c in df["Clinic Name"].dropna().unique()],
                        multi=True,
                    ),
                ], md=4),

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
    ], style=CARD_STYLE, className="mb-4"),

    dbc.Row([
        dbc.Col(html.Div(id="kpi_pacientes"), md=4),
        dbc.Col(html.Div(id="kpi_espera"), md=4),
        dbc.Col(html.Div(id="kpi_satisfaccion"), md=4),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dcc.Graph(id="grafico_volumen"), style=CARD_STYLE), md=4),
        dbc.Col(dbc.Card(dcc.Graph(id="grafico_espera"), style=CARD_STYLE), md=4),
        dbc.Col(dbc.Card(dcc.Graph(id="grafico_satisfaccion"), style=CARD_STYLE), md=4),
    ])
    
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
    ],
    [
        Input("filtro_fecha", "start_date"),
        Input("filtro_fecha", "end_date"),
        Input("filtro_clinica", "value"),
        Input("filtro_fuente", "value"),
    ],
)
def actualizar_dashboard(fecha_inicio, fecha_fin, clinicas, fuentes):

    datos = df.copy()

    if fecha_inicio and fecha_fin:
        datos = datos[
            (datos["Appt Start Time"] >= fecha_inicio) &
            (datos["Appt Start Time"] <= fecha_fin)
        ]

    if clinicas:
        datos = datos[datos["Clinic Name"].isin(clinicas)]

    if fuentes:
        datos = datos[datos["Admit Source"].isin(fuentes)]

    # 📊 VOLUMEN
    volumen = datos.groupby("Clinic Name").size().reset_index(name="Pacientes")

    fig_volumen = px.bar(volumen, x="Clinic Name", y="Pacientes")

    # ⏳ ESPERA
    fig_espera = px.box(datos, x="Department", y="Wait Time Min")

    # ⭐ SATISFACCIÓN
    fig_satisfaccion = px.histogram(datos, x="Care Score")

    # KPIs
    total = len(datos)
    avg_wait = round(datos["Wait Time Min"].mean(), 2)
    avg_score = round(datos["Care Score"].mean(), 2)

    return (
        fig_volumen,
        fig_espera,
        fig_satisfaccion,
        dbc.Card(dbc.CardBody([html.H6("Pacientes"), html.H2(total)])),
        dbc.Card(dbc.CardBody([html.H6("Espera"), html.H2(avg_wait)])),
        dbc.Card(dbc.CardBody([html.H6("Satisfacción"), html.H2(avg_score)])),
    )

# ================================
# ▶️ RUN
# ================================
if __name__ == "__main__":
    app.run()
