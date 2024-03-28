# Import necessary libraries
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, dash_table, callback_context, State
import dash_bootstrap_components as dbc
import pandas as pd
import json
import base64
import plotly.express as px
import os

# Reference the external CSS file using a URL
external_stylesheets = [dbc.themes.BOOTSTRAP, 'https://github.com/dj-urg/convert-tiktok-ddp/blob/main/style.css']

# Initialize Dash app with external CSS
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define the layout of the app
app.layout = dbc.Container([
    # Header with the app title
    dbc.Row(
        dbc.Col(
            html.H1("TikTok Data Download Package Processor", className="text-center my-5"),
            width=12
        )
    ),
    # Upload section for selecting files
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select File', className="link-class")
                        ]),
                        style={
                            'width': '100%', 'height': '60px', 'lineHeight': '60px',
                            'borderWidth': '1px', 'borderStyle': 'dashed',
                            'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px'
                        },
                        multiple=True
                    ),
                    # Informational text for the user
                    html.P([
                        "Easily transform your TikTok JSON into a CSV format, capturing details from your ",
                        html.Span("Video Browsing History", className="font-weight-bold"),
                        ", ",
                        html.Span("Favorite Videos", className="font-weight-bold"),
                        ", and ",
                        html.Span("Like List", className="font-weight-bold"),
                        ". Your data is processed in real-time, ensuring that personal information is ",
                        html.Span("never kept or retained", className="font-italic text-danger"),
                        " on any server."
                    ], className="text-center mt-4"),
                    # Section for selecting data to process
                    html.P("Please select the information to be processed below:", className="text-center mt-4"),
                    dcc.Checklist(
                        id='data-selection-checklist',
                        options=[
                            {'label': ' Browsing', 'value': 'video_history'},
                            {'label': ' Favorite', 'value': 'favorite_video'},
                            {'label': ' Liked', 'value': 'item_favorite'},
                        ],
                        value=['video_history', 'favorite_video', 'item_favorite'],
                        inline=True,
                        style={'textAlign': 'center'},
                        labelStyle={'margin-right': '20px'}
                    ),
                ]),
                className="mt-4"  # Margin top for spacing
            ),
            width={'size': 8, 'offset': 0},  # Decreased width of the card
        ),
        className="justify-content-center"  # Horizontally center the column in the row
    ),
    # Display average watch time
    dbc.Row(
        dbc.Col(
            html.Div(id='average-watch-time', className="text-center mt-3 mb-3"),
            width=12
        )
    ),
    # Graph for video history
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='video-history-chart', style={'display': 'none'}),
            width=12
        )
    ),
    # Buttons for downloading data
    dbc.Row(
        [
            dbc.Col(
                html.Button(
                    "Download JSON as CSV",
                    id="downloadCSV",
                    className="btn btn-info btn-lg btn-block mt-3",
                    style={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'}
                ),
                width={"size": 4, "offset": 2}
            ),
            dbc.Col(
                html.Button(
                    "Download TikTok URL List (4CAT)",
                    id="downloadText",
                    className="btn btn-info btn-lg btn-block mt-3",
                    style={'backgroundColor': '#343a40', 'color': 'white', 'fontWeight': 'bold'}
                ),
                width=4
            )
        ],
        className="center-horizontal mt-4"
    ),
    # Download link component
    dbc.Row(
        dbc.Col(
            dcc.Download(id="download-link")
        )
    ),
    # Table to display processed data
    dbc.Row(
    dbc.Col(
        dash_table.DataTable(
            id='table',
            style_as_list_view=True,
            style_header={
                'backgroundColor': '#343a40',  # Dark background color for header
                'color': 'white',  # White text color for header
                'fontWeight': 'bold',  # Bold font weight for header text
                'border': 'none',  # Remove border for header
                'borderRadius': '5px 5px 0 0',  # Rounded corners for top of header
                'padding': '12px'  # Add padding to header cells
            },
            style_cell={
                'backgroundColor': 'white',  # White background color for cells
                'color': '#343a40',  # Dark text color for cells
                'border': 'none',  # Remove border for cells
                'padding': '10px',  # Add padding to cells
                'maxWidth': '300px',  # Limit maximum width of cells
                'overflow': 'hidden',  # Hide overflow content in cells
                'textOverflow': 'ellipsis'  # Show ellipsis for overflow text in cells
            },
            style_data_conditional=[  # Apply conditional styling to data cells
                {
                    'if': {'row_index': 'odd'},  # Apply style to odd rows
                    'backgroundColor': '#f8f9fa'  # Light background color for odd rows
                }
            ]
        ),
        width=12
    ),
    className="my-5"
),
], fluid=True, className="py-5")  # Padding top and bottom for the whole container

# Global variable to store video browsing history DataFrame
global video_browsing_history_df
video_browsing_history_df = pd.DataFrame()

# Callback to update output based on file upload and data selection
@app.callback(
    [Output('table', 'data'),
     Output('table', 'columns'),
     Output('video-history-chart', 'figure'),
     Output('average-watch-time', 'children'),
     Output('video-history-chart', 'style'),
     Output("downloadCSV", "style"),
     Output("downloadText", "style")],
    [Input('upload-data', 'contents'),
     Input('data-selection-checklist', 'value')],
    [State('upload-data', 'filename')]
)
def update_output(contents, selected_sections, filename):
    global video_browsing_history_df
    if contents is None:
        # No file uploaded, return empty data and hide elements
        return [{}], [], dash.no_update, "No file uploaded.", {'display': 'none'}, {'display': 'none'}, {'display': 'none'}

    try:
        # Assuming only the first file is processed if multiple files are uploaded
        content_type, content_string = contents[0].split(',')  
        decoded = base64.b64decode(content_string)
        data = json.loads(decoded.decode('utf-8'))  # Decode to string before JSON parsing
        
        all_videos = []
        # Extract selected data sections from the uploaded file
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
            # Process the extracted data and update components
            video_browsing_history_df = pd.DataFrame(all_videos)
            video_browsing_history_df['Date'] = pd.to_datetime(video_browsing_history_df['Date'])
            video_browsing_history_df.sort_values('Date', inplace=True)
            # Calculate the time difference between consecutive video start times
            video_browsing_history_df['Time_Diff'] = video_browsing_history_df['Date'].diff().dt.total_seconds()
            filtered_time_diff = video_browsing_history_df['Time_Diff'][video_browsing_history_df['Time_Diff'] <= 180]
            total_watch_time = 0
            num_sessions = 0
            for time_diff in filtered_time_diff:
                total_watch_time += time_diff
                num_sessions += 1
            if num_sessions > 0:
                average_watch_time = total_watch_time / num_sessions
            else:
                average_watch_time = 0
            average_time_text = html.Div([
                html.Span("Estimation of average time spent per video (excluding sessions longer than max video length > 3 mins): "),
                html.Span(f"{average_watch_time:.2f} seconds", className="font-weight-bold")
            ])
            links_per_month = video_browsing_history_df.groupby(video_browsing_history_df['Date'].dt.to_period('M')).size().reset_index(name='counts')
            links_per_month['year_month'] = links_per_month['Date'].astype(str)
            category_counts_per_date = video_browsing_history_df.groupby([video_browsing_history_df['Date'].dt.to_period('M'), 'Source']).size().unstack(fill_value=0)
            category_counts_per_date = category_counts_per_date.reset_index()
            category_counts_per_date['Date'] = category_counts_per_date['Date'].astype(str)
            fig = px.bar(category_counts_per_date, x='Date', y=['Browsing', 'Favorite', 'Liked'], title="Watched Videos per Month", labels={'value': 'Number of Videos', 'variable': 'Source'}, barmode='stack')
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
            return records, columns, fig, average_time_text, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}
        else:
            # No data found, hide elements except error message
            return [{}], [], {}, "No Browsing found.", {'display': 'none'}, {'display': 'block'}, {'display': 'block'}
        
    except Exception as e:
        # Error occurred, display error message and hide elements except error message
        return [{}], [], dash.no_update, f"Error processing the file: {str(e)}", {'display': 'none'}, {'display': 'block'}, {'display': 'block'}

# Callback to generate file downloads
@app.callback(
    Output("download-link", "data"),
    [Input("downloadCSV", "n_clicks"), Input("downloadText", "n_clicks")],
    prevent_initial_call=True
)
def generate_file(n_clicks_csv, n_clicks_text):
    triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == "downloadCSV":
        if not video_browsing_history_df.empty:
            return dcc.send_data_frame(video_browsing_history_df.to_csv, "video_browsing_history.csv", index=False)
    elif triggered_id == "downloadText":
        if not video_browsing_history_df.empty:
            links_str = ','.join(video_browsing_history_df['Link'].astype(str))
            return dcc.send_string(links_str, "video_browsing_history_links.txt")
    return None

# Entry point for running the app on Heroku
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=int(os.environ.get('PORT', 8051)))
