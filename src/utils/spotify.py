
from spotipy.oauth2 import SpotifyOAuth
import spotipy


scope = "user-read-playback-state,user-modify-playback-state"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

async def get_librespot_device():
    devices = sp.devices()
    device_id = None
    for device in devices['devices']:
        print(f"Device name {device['name']} Device id {device['id']}")
        device_id = device['id']
    return device_id

async def stop_track() -> str:
    device_id = await get_librespot_device()
    if device_id:
        sp.pause_playback(device_id=device_id)
        return "Message from Spotify: Playback paused"
    return "Message from Spotify: Librespot device not found"

async def play_next_track() -> str:
    device_id = await get_librespot_device()
    if device_id:
        sp.next_track(device_id=device_id)
        return "Message from Spotify: Playing next track"
    return "Message from Spotify: Librespot device not found"

async def play_previous_track() -> str:
    device_id = await get_librespot_device()
    if device_id:
        sp.previous_track(device_id=device_id)
        return "Message from Spotify: Playing previous track"
    return "Message from Spotify: Librespot device not found"

async def search_and_play_track(track_name: str) -> str:

    print(f"Searching for: {track_name}")

    try:
        device_id = await get_librespot_device()
        if not device_id:
            return "Message from Spotify: Librespot device not found"

        track_name = track_name.replace('>', '').strip()
        
        results = sp.search(q=track_name, type='track', limit=1)
        tracks = results['tracks']['items']
        
        if tracks:
            track = tracks[0]
            track_id = f"spotify:track:{track['id']}"
            print(f"Found track: {track['name']} by {track['artists'][0]['name']}")
            print(f"Playing on device: {device_id}")
            
            try:
                sp.start_playback(device_id=device_id, uris=[track_id])
                
                # recommendations = sp.recommendations(seed_tracks=[track['id']], limit=10)
                response = [f"Message from Spotify: Playing '{track['name']}' by {track['artists'][0]['name']}\nUp next:"]
                
                # for rec in recommendations['tracks']:
                #     sp.add_to_queue(uri=f"spotify:track:{rec['id']}", device_id=device_id)
                #     response.append(f"- {rec['name']} by {rec['artists'][0]['name']}")
                
                return "\n".join(response)
            except Exception as playback_error:
                print(f"Playback error: {playback_error}")
                return f"Message from Spotify: Error during playback: {str(playback_error)}"
        else:
            return f"Message from Spotify: No tracks found for '{track_name}' on Spotify."
    except Exception as e:
        print(f"Error in search_and_play_track: {e}")
        return f"Message from Spotify: An error occurred while trying to play the track: {str(e)}"
