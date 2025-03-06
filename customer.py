import dash
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import base64
import io
import re

# ============================
# 1️⃣ Inisialisasi Aplikasi Dash (Dengan Bootstrap)
# ============================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SANDSTONE], suppress_callback_exceptions=True)
server = app.server  # Untuk deployment

# ============================
# 2️⃣ Layout Dashboard dengan Bootstrap
# ============================
app.layout = dbc.Container([
    dcc.Store(id="stored-data"),  # 🔹 Menyimpan data CSV yang diunggah

    dbc.Row([
        dbc.Col(html.H1("📊 Customer Segmentation Dashboard", className="text-center mt-4"))
    ]),

    dbc.Row([
        dbc.Col(
            dcc.Upload(
                id='upload-data',
                children=dbc.Button("📂 Upload File CSV", color="primary", className="mt-3"),
                multiple=False
            ), width=6, className="d-flex justify-content-center"
        )
    ]),

    dbc.Row([
        dbc.Col(html.Div(id="upload-status", className="mt-2 text-center"), width=12)
    ]),

    dbc.Tabs(id="tabs", active_tab="dashboard", children=[
        dbc.Tab(label="📊 Dashboard", tab_id="dashboard"),
        dbc.Tab(label="📋 Tabel Segmentation", tab_id="table"),
        dbc.Tab(label="📥 Unduh Data", tab_id="download"),
    ], className="mt-3"),

    html.Div(id="tab-content", className="p-3"),

    dcc.Download(id="download-excel"),
], fluid=True)

# ============================
# 3️⃣ Fungsi Baca CSV & Segmentasi Pelanggan
# ============================
def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # Bersihkan & proses data
    df.columns = df.columns.str.strip()
    df = df.drop_duplicates(subset=['Username'], keep='first')
    df = df[(df['Deposit Amount'] > 0) | (df['Withdraw Amount'] > 0)]
    df['Net Amount'] = df['Deposit Amount'] - df['Withdraw Amount']
    df['Profit'] = df['Net Amount']

    # Menentukan Grade berdasarkan Deposit Amount
    def categorize(amount):
        if amount > 5000:
            return 'AAA'
        elif amount > 3000:
            return 'A'
        elif amount > 2000:
            return 'B'
        elif amount > 1000:
            return 'C'
        else:
            return 'D'
    
    df['Grade'] = df['Deposit Amount'].apply(categorize)

    # Menentukan Net Category
    def categorize_net(net_amount):
        if net_amount > 5000:
            return 'High Surplus'
        elif net_amount > 0:
            return 'Surplus'
        elif net_amount == 0:
            return 'Balanced'
        else:
            return 'Deficit'

    df['Net Category'] = df['Net Amount'].apply(categorize_net)

    return df.to_dict('records')  # Simpan sebagai dictionary untuk `dcc.Store`

# ============================
# 4️⃣ Callback Upload File & Dashboard Update
# ============================
@app.callback(
    [Output("upload-status", "children"), Output("stored-data", "data"), Output("tab-content", "children")],
    [Input("upload-data", "contents"), Input("tabs", "active_tab")],
    prevent_initial_call=True
)
def update_output(contents, selected_tab):
    if contents:
        df_data = parse_contents(contents)
    else:
        df_data = None

    if selected_tab == "dashboard":
        if not df_data:
            return "⚠️ Silakan unggah file CSV.", None, html.Div()

        df = pd.DataFrame(df_data)

        return "✅ File berhasil diunggah!", df_data, dbc.Container([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("💰 Total Deposit"),
                    dbc.CardBody(html.H4(f"RM{df['Deposit Amount'].sum():,.2f}"))
                ], color="info", inverse=True), width=4),

                dbc.Col(dbc.Card([
                    dbc.CardHeader("📉 Total Withdraw"),
                    dbc.CardBody(html.H4(f"RM{df['Withdraw Amount'].sum():,.2f}"))
                ], color="danger", inverse=True), width=4),

                dbc.Col(dbc.Card([
                    dbc.CardHeader("💵 Total Profit"),
                    dbc.CardBody(html.H4(f"RM{df['Profit'].sum():,.2f}"))
                ], color="success", inverse=True), width=4)
            ], className="mt-3"),

            dbc.Row([
                dcc.Graph(figure=px.bar(df.groupby('Grade')['Profit'].sum().reset_index(), x="Grade", y="Profit", title="Total Profit per Grade")),
                dcc.Graph(figure=px.bar(df.groupby('Grade')[['Deposit Amount', 'Withdraw Amount']].sum().reset_index(), x="Grade", y=['Deposit Amount', 'Withdraw Amount'], title="Deposit vs Withdraw per Grade", barmode='group'))
            ], className="mt-3")
        ])

    elif selected_tab == "table":
        return "✅ File berhasil diunggah!", df_data, dbc.Container([
            dcc.Dropdown(
                id="grade-filter",
                options=[{"label": g, "value": g} for g in sorted(pd.DataFrame(df_data)["Grade"].unique())],
                value="AAA",
                clearable=False
            ),
            html.Div(id="table-container")
        ])

    elif selected_tab == "download":
        return "✅ File berhasil diunggah!", df_data, html.Div([
            dbc.Button("📥 Download CSV", id="btn_csv", color="success"),
            dcc.Download(id="download-dataframe-csv")
        ])

# ============================
# 5️⃣ Callback untuk Menampilkan Tabel
# ============================
@app.callback(
    Output("table-container", "children"),
    [Input("grade-filter", "value")],
    [State("stored-data", "data")],
    prevent_initial_call=True
)
def update_table(selected_grade, data):
    df = pd.DataFrame(data)
    df_filtered = df[df["Grade"] == selected_grade]

    return dash_table.DataTable(columns=[{"name": i, "id": i} for i in df_filtered.columns], data=df_filtered.to_dict('records'))

# ============================
# 6️⃣ Jalankan Aplikasi Dash
# ============================
if __name__ == '__main__':
    app.run_server(debug=True)
