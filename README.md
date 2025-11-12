# Create Playlists using concert setlists (WIP)


# How to use

## Create Conda Environment
```
# If you do not have anaconda installed download it for your specific OS

conda create -f .\environment.yml
conda activate setlist-to-playlist
```

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