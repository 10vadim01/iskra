import spotipy
from spotipy.oauth2 import SpotifyOAuth

print("Starting Spotify player")
scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.search(q=f'track:Money Trees', type='track', limit=1)
tracks = results['tracks']['items']
    
if tracks:
    track = tracks[0]
    track_id = f"spotify:track:{track['id']}"
    sp.start_playback(uris=[track_id])
    print(f"Message from Spotify: Found '{track['name']}' by {track['artists'][0]['name']}")
else:
    print(f"Message from Spotify: No 'Money Trees' was found on Spotify.")
