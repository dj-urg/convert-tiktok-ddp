# Import necessary libraries
import dash
from dash import Dash, dcc, html, Input, Output, callback, dash_table, State, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import json
import base64  # Ensure base64 is imported for decoding

# Initialize the Dash app (using Bootstrap for styling)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Upload and Convert TikTok Data Donation"), width={"size": 6, "offset": 3})),
    
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                },
                # Allow a single file to be uploaded
                multiple=False,
                accept=".json"
            ),
            html.Button("Download CSV", id="downloadData"),
            dcc.Download(id="download-link"),
            html.Hr(),
            html.P("This application is part of a data donations project at the Vrije Universiteit Brussel. The app processes your personal data file received from TikTok from JSON into a CSV that only contains your 'Video Browsing History'. This includes a URL link to the TikTok video that has been watched and a date on which the video was watched."),
            html.P("Our application processes your uploaded data in real-time, ensuring that no personal information is stored or kept on any server. Once your session ends, any temporarily held data is immediately discarded. We prioritize your privacy, handling your data exclusively for the conversion process and ensuring it remains under your control at all times."),
            html.P("If you have any questions about this process, please contact daniel.jurg@vub.be"),
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col(dash_table.DataTable(id='table'), width={"size": 6, "offset": 3})
    ])
], fluid=True)

# Global variable to store video browsing history DataFrame
video_browsing_history_df = pd.DataFrame()

# Callback to process the uploaded file, display its content, and prepare for CSV download
@callback(
    Output('table', 'data'),
    Output('table', 'columns'),
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    global video_browsing_history_df
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        # Decode the JSON content and extract the video browsing history
        data = json.loads(decoded)
        video_history = data.get('Activity', {}).get('Video Browsing History', {}).get('VideoList', [])
        if video_history:
            # Convert the video browsing history into a pandas DataFrame
            video_browsing_history_df = pd.DataFrame(video_history)
            # Prepare the data for the DataTable
            return video_browsing_history_df.to_dict('records'), [{"name": i, "id": i} for i in video_browsing_history_df.columns]
        else:
            return [{}], []
    else:
        return [{}], []

# Callback to handle the download action
@callback(
    Output("download-link", "data"),
    [Input("downloadData", "n_clicks")],
    prevent_initial_call=True  # Prevents the callback from running on app load
)
def generate_csv(n_clicks):
    if not video_browsing_history_df.empty:
        return dcc.send_data_frame(video_browsing_history_df.to_csv, "video_browsing_history.csv", index=False)
    return None

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)
