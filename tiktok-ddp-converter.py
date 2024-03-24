# Import necessary libraries
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, dash_table, callback, State
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
    dbc.Row(dbc.Col(html.H1("Upload, Convert and Download TikTok Data Download Package", className="text-center"), width=12)),
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.P('Drag and Drop or', className="text-center"),
                    html.P(html.A('Select Files', className="btn btn-primary btn-lg btn-block"))
                ]),
                style={'textAlign': 'center', 'margin': '10px', 'display': 'flex', 'justifyContent': 'center', 'flexDirection': 'column'}
            ),
            html.Hr(),
            html.P("This application is part of a data donations project at the Vrije Universiteit Brussel. The app processes your personal data file received from TikTok from JSON into a CSV that only contains your 'Video Browsing History'. This includes a URL link to the TikTok video that has been watched and a date on which the video was watched.", className="text-center"),
            html.P("Our application processes your uploaded data in real-time, ensuring that no personal information is stored or kept on any server. Once your session ends, any temporarily held data is immediately discarded. We prioritize your privacy, handling your data exclusively for the conversion process and ensuring it remains under your control at all times.", className="text-center"),
            html.P("If you have any questions about this process, please contact daniel.jurg@vub.be", className="text-center"),
            dcc.Checklist(
                id='data-selection-checklist',
                options=[
                    {'label': 'Browsing', 'value': 'video_history'},
                    {'label': 'Favorite', 'value': 'favorite_video'},
                    {'label': 'Liked', 'value': 'item_favorite'},
                ],
                value=['video_history', 'favorite_video', 'item_favorite'],  # Default all selected
                labelStyle={'display': 'block', 'margin-left': '50px'}  # Display checkboxes vertically
            ),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='average-watch-time', className="text-center mt-3 mb-3", style={'color': '#007BFF', 'fontSize': '20px', 'fontWeight': 'bold'}), width=12)
    ]),
    dbc.Row([  # Row for the bar chart
        dbc.Col(dcc.Graph(id='video-history-chart'), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Button("Download CSV", id="downloadData", className="btn btn-success btn-lg btn-block"), 
                width={"size": 6, "offset": 3},  # Set the size and offset to center the button
                className="d-flex justify-content-center")  # Use d-flex and justify-content-center to center the column content
    ]),
    dbc.Row([  # dcc.Download component doesn't need a visible row; it works in the background
        dbc.Col(dcc.Download(id="download-link"))
    ]),
    dbc.Row([
        dbc.Col(html.Div(), className="mb-3")  # You can adjust the margin-bottom as needed
    ], className="mt-3"),  # Add margin-top to this row if you want even more space
    dbc.Row([
        dbc.Col(dash_table.DataTable(id='table'), width=12)
    ])
], fluid=True, className="text-center")

# Global variable to store video browsing history DataFrame
video_browsing_history_df = pd.DataFrame()

# Assuming 'video_browsing_history_df' and other setup code is already provided
def parse_date(date_str):
    """Parse the datetime string to a datetime object."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        return None

# Callback to process the uploaded file, display its content, prepare for CSV download, and update the bar chart
@app.callback(
    [Output('table', 'data'),
     Output('table', 'columns'),
     Output('video-history-chart', 'figure'),
     Output('average-watch-time', 'children')],
    [Input('upload-data', 'contents'),
     Input('data-selection-checklist', 'value')],  # Include selections from the checklist
    [State('upload-data', 'filename')]
)

def update_output(contents, selected_sections, filename):
    if contents is not None:
        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            data = json.loads(decoded)
            
            all_videos = []
            if 'video_history' in selected_sections:
                video_history = data.get('Activity', {}).get('Video Browsing History', {}).get('VideoList', [])
                for video in video_history:
                    video['Source'] = 'Browsing'
                all_videos.extend(video_history)
            
            if 'favorite_video' in selected_sections:
                favorite_video_history = data.get('Activity', {}).get('Favorite Videos', {}).get('FavoriteVideoList', [])
                if not favorite_video_history:  # Fallback to 'Favorite' if 'Favorite Videos' does not exist
                    favorite_video_history = data.get('Activity', {}).get('Favorite', {}).get('FavoriteVideoList', [])
                for video in favorite_video_history:
                    video['Source'] = 'Favorite'
                all_videos.extend(favorite_video_history)
            
             if 'item_favorite' in selected_sections:
                 item_favorite_list = data.get('Activity', {}).get('Like List', {}).get('ItemFavoriteList', [])
                 if not item_favorite_list:  # If not found, try the old key structure
                     item_favorite_list = data.get('Activity', {}).get('Liked', {}).get('ItemFavoriteList', [])
                for video in item_favorite_list:
                    video['Source'] = 'Liked'
                all_videos.extend(item_favorite_list)
            
            if all_videos:
                global video_browsing_history_df
                video_browsing_history_df = pd.DataFrame(all_videos)
                video_browsing_history_df['Date'] = pd.to_datetime(video_browsing_history_df['Date'])
                video_browsing_history_df.sort_values('Date', inplace=True)
                video_browsing_history_df['Time_Diff'] = video_browsing_history_df['Date'].diff().dt.total_seconds()
                filtered_time_diff = video_browsing_history_df['Time_Diff'][video_browsing_history_df['Time_Diff'] <= 600]
                average_watch_time = filtered_time_diff[1:].mean()
                average_time_text = f"Average time spent per video (excluding breaks > 10 mins): {average_watch_time:.2f} seconds"
                links_per_month = video_browsing_history_df.groupby(video_browsing_history_df['Date'].dt.to_period('M')).size().reset_index(name='counts')
                links_per_month['year_month'] = links_per_month['Date'].astype(str)
                fig = px.bar(links_per_month, x='year_month', y='counts', labels={'year_month': 'Month', 'counts': 'Number of Videos'}, title="Watched Videos per Month")
                fig.update_layout({
                    'plot_bgcolor': 'white',
                    'paper_bgcolor': 'white',
                    'font': {
                        'color': '#2c3e50',
                        'family': "Arial, Helvetica, sans-serif",
                    },
                    'title': {
                        'x': 0.5,
                        'xanchor': 'center'
                    }
                })
                fig.update_xaxes(showline=True, linewidth=2, linecolor='gray', gridcolor='lightgray')
                fig.update_yaxes(showline=True, linewidth=2, linecolor='gray', gridcolor='lightgray')
                records = video_browsing_history_df.to_dict('records')
                columns = [{"name": i, "id": i} for i in video_browsing_history_df.columns]
                return records, columns, fig, average_time_text
            else:
                return [{}], [], {}, "No Browsing found."
            
        except Exception as e:
            return [{}], [], {}, f"Error processing the file: {e}"
    
    return [{}], [], {}, "No file uploaded."

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
