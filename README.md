# Concert Setlist to Spotify Playlist Generator
A full-stack web application that lets users search for an artist, browse their concert setlists, preview songs, and generate a Spotify playlist.  
This project integrates multiple third-party APIs, includes rate limiting and caching, and provides a React UI for selecting and filtering songs before playlist creation.

## Features
- Artist Search - Search artists using the setlist.fm API
- Browse Concert Setlists - View past and upcoming concerts by venue and date
- Setlist Preview - See full song order, including encores and covers
- Selective Song Inclusion - Toggle individual songs on/off before playlist creation
- Spotify Playlist Creation - Create public or private playlists

## Tech Stack
### Frontend
- React
- CSS
- Fetch API

### Backend
- Python
- Flask
- REST API architecture
- OAuth authentication with Spotify

### APIs & Libraries
- setlist.fm API
- Spotify Web API (via spotipy)


# How to use
## Create Conda Environment
```
# If you do not have anaconda installed download it for your specific OS

conda create -f .\environment.yml
conda activate setlist-to-playlist
```
## Environment Variables
Create a `.env` file in the project root using `.env.example` template

## Start Flask Server
```
python app.py
```

## Start Vite app
```
cd setlist-to-playlist-app
npm install
npm run dev
# press "o" to open the site
```

## If using Windows Terminal and Powershell 7.5.4
```
# Can run this script to open in split pane after installing all dependencies
./run.bat
```
