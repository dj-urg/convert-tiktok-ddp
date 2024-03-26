# TikTok Data Processing Dash App

## Overview
This Dash application is designed to upload, convert, and download TikTok data, specifically focusing on users' "Video Browsing History". It offers an intuitive web interface for users to upload their personal data file received from TikTok, processes it from JSON to CSV format, and allows for the download of the processed data.

## Features
- **Data Upload**: Users can upload their TikTok data package in JSON format.
- **Data Conversion**: The app converts the "Video Browsing History" from JSON to a user-friendly CSV format, including video URLs and the dates videos were watched.
- **Privacy-Focused**: Processes data in real-time without storing any personal information on the server. All temporary data is discarded after the session ends.
- **Data Selection**: Users can select which parts of their TikTok data to process (e.g., Browsing, Favorite, Liked videos).
- **Interactive Visualization**: Provides a bar chart visualization of the watched videos per month.
- **Data Download**: Users can download the processed CSV file directly from the web interface.

## Installation
To set up the Dash app on your local machine, follow these steps:

1. Ensure you have Python installed on your system.
2. Clone the repository or download the source code.
3. Install the required Python packages:
pip install dash dash-bootstrap-components pandas plotly
4. Run the application:
python app.py

## Usage
1. Open the application in your web browser.
2. Drag and drop your TikTok data file in JSON format or use the "Select Files" button to upload your file.
3. Choose which data sections you wish to process (Browsing, Favorite, Liked videos).
4. Click on "Download CSV" to download your processed data.

## Deployment
This application includes an `os` module import for Heroku deployment compatibility. For deploying on Heroku, ensure you have a `Procfile` and specify the necessary buildpacks and dependencies in `requirements.txt`.

## Contact
For any questions or issues related to this application, please contact Daniel Jurg at daniel.jurg@vub.be.

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.
