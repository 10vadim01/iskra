import spotipy
from spotipy.oauth2 import SpotifyOAuth

print("Starting Spotify player")
scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

devices = sp.devices()

device_id = None

for device in devices['devices']:
    print(f"Device name {device['name']} Device id {device['id']}")
    device_id = device['id']

results = sp.search(q=f'track:Money Trees', type='track', limit=1)
tracks = results['tracks']['items']
    
if tracks:
    track = tracks[0]
    track_id = f"spotify:track:{track['id']}"
    
    recommendations = sp.recommendations(seed_tracks=[track['id']], limit=5)
    recommended_tracks = [track_id]
    
    for rec in recommendations['tracks']:
        recommended_tracks.append(f"spotify:track:{rec['id']}")
    
    sp.start_playback(device_id=device_id, uris=recommended_tracks)
    print(f"Message from Spotify: Found '{track['name']}' by {track['artists'][0]['name']}")
    print("Added to queue:")
    for rec in recommendations['tracks']:
        print(f"- {rec['name']} by {rec['artists'][0]['name']}")
else:
    print(f"Message from Spotify: No 'Money Trees' was found on Spotify.")
