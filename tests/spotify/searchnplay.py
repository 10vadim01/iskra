import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.search(q='track:Shape of You', type='track')
tracks = results['tracks']['items']

for track in tracks:
    print(f"Track Name: {track['name']}, Artist: {track['artists'][0]['name']}, URL: {track['external_urls']['spotify']}")
    
track_id = 'spotify:track:' + tracks[0]['id']
    
sp.start_playback(uris=[track_id])