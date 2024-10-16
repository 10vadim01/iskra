import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

async def play_track(track_name: str) -> str:
    try:
        results = sp.search(q=f'track:{track_name}', type='track', limit=1)
        tracks = results['tracks']['items']
        
        if tracks:
            track = tracks[0]
            track_id = f"spotify:track:{track['id']}"
            sp.start_playback(uris=[track_id])
            return f"Message from Spotify: Found '{track['name']}' by {track['artists'][0]['name']}"
        else:
            return f"Message from Spotify: No '{track_name}' was found on Spotify."
    except Exception as e:
        return f"Message from Spotify: An error occurred while trying to play the track: {str(e)}"

async def stop_track() -> str:
    sp.pause_playback()
    return "Message from Spotify: Playback paused"
    
async def play_next_track() -> str:
    sp.next_track()
    return "Message from Spotify: Playing next track"

async def play_previous_track() -> str:
    sp.previous_track()
    return "Message from Spotify: Playing previous track"
