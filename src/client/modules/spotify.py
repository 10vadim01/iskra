
from spotipy.oauth2 import SpotifyOAuth
import spotipy


scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

async def stop_track() -> str:
    sp.pause_playback()
    return "Message from Spotify: Playback paused"
    
async def play_next_track() -> str:
    sp.next_track()
    return "Message from Spotify: Playing next track"

async def play_previous_track() -> str:
    sp.previous_track()
    return "Message from Spotify: Playing previous track"

async def search_and_play_track(track_name: str) -> str:

    print(f"Searching for: {track_name}")

    try:
        results = sp.search(q=f'track:{track_name}', type='track', limit=1)
        tracks = results['tracks']['items']
        
        if tracks:
            track = tracks[0]
            track_id = f"spotify:track:{track['id']}"

            
            recommendations = sp.recommendations(seed_tracks=[track['id']], limit=10)
            playlist_queue = [track_id]
            
            response = [f"Message from Spotify: Found '{track['name']}' by {track['artists'][0]['name']}\nAdded to queue:"]
            
            for rec in recommendations['tracks']:
                playlist_queue.append(f"spotify:track:{rec['id']}")
                response.append(f"- {rec['name']} by {rec['artists'][0]['name']}")

            sp.start_playback(uris=playlist_queue)
            
            return "\n".join(response)

        else:
            return f"Message from Spotify: No '{track_name}' was found on Spotify."
    except Exception as e:
        return f"Message from Spotify: An error occurred while trying to play the track: {str(e)}"
