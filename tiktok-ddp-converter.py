# Import necessary libraries
import dash
from dash import dcc, html, Input, Output, dash_table, callback, State, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import json
import base64
import plotly.express as px  # Import Plotly Express for the chart
import os  # Ensure os is imported for Heroku deployment

# Initialize the Dash app (using Bootstrap for styling)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define the layout of the app
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Upload and Convert TikTok Data Donation"), width={"size": 6, "offset": 3})),
    
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-data",
                children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
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
            html.P("This application is part of a data donations project at the Vrije Universiteit Brussel..."),
            # More explanatory text...
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col(dash_table.DataTable(id='table'), width={"size": 6, "offset": 3})
    ]),
    dbc.Row([  # Add a new row for the bar chart
        dbc.Col(dcc.Graph(id='video-history-chart'), width={"size": 8, "offset": 2})
    ])
], fluid=True)

# Global variable to store video browsing history DataFrame
video_browsing_history_df = pd.DataFrame()

# Callback to process the uploaded file, display its content, prepare for CSV download, and update the bar chart
@app.callback(
    [Output('table', 'data'),
     Output('table', 'columns'),
     Output('video-history-chart', 'figure')],  # Add output for the chart
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_output(contents, filename):
    global video_browsing_history_df
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        # Decode the JSON content and specifically extract the "Video Browsing History"
        data = json.loads(decoded)
        video_history = data.get('Activity', {}).get('Video Browsing History', {}).get('VideoList', [])
        if video_history:
            # Convert the video browsing history into a pandas DataFrame
            video_browsing_history_df = pd.DataFrame(video_history)
            # Ensure the 'Date' column is in datetime format
            video_browsing_history_df['Date'] = pd.to_datetime(video_browsing_history_df['Date'])
            # Extract year and month from the 'Date', and count videos per month
            video_browsing_history_df['year_month'] = video_browsing_history_df['Date'].dt.to_period('M')
            links_per_month = video_browsing_history_df.groupby('year_month').size().reset_index(name='counts')
            # Create the bar chart with Plotly Express
            fig = px.bar(links_per_month, x='year_month', y='counts', labels={'year_month': 'Month', 'counts': 'Number of Videos'}, title="Video Links per Month")
            # Prepare the data for the DataTable and the chart
            return video_browsing_history_df.to_dict('records'), [{"name": i, "id": i} for i in video_browsing_history_df.columns], fig
        else:
            # Return empty states if no video history is found
            return [{}], [], {}
    else:
        # Return empty states if no contents are uploaded
        return [{}], [], {}

# Callback to handle the download action remains unchanged
@app.callback(
    Output("download-link", "data"),
    [Input("downloadData", "n_clicks")],
    prevent_initial_call=True
)
def generate_csv(n_clicks):
    if not video_browsing_history_df.empty:
        return dcc.send_data_frame(video_browsing_history_df.to_csv, "video_browsing_history.csv", index=False)
    return None

# Entry point for running the app on Heroku
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=int(os.environ.get('PORT', 8051)))
