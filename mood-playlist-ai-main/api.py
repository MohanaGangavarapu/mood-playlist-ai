import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import base64
from typing import List, Optional
import json
import openai 
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Mood-Based Playlist Generator")


# .env var
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIRECT_URI = os.getenv("REDIRECT_URI")

# Print configuration for debugging
print(f"REDIRECT_URI: {REDIRECT_URI}")
print(f"CLIENT_ID: {SPOTIFY_CLIENT_ID[:5]}..." if SPOTIFY_CLIENT_ID else "CLIENT_ID: Not set")
print(f"CLIENT_SECRET: {'*****' if SPOTIFY_CLIENT_SECRET else 'Not set'}")

openai.api_key = OPENAI_API_KEY

class MoodRequest(BaseModel):
    mood_description: str
    num_songs: int = 10

class AuthRequest(BaseModel):
    code: str

class Song(BaseModel):
    name: str
    artist: str
    uri: str
    album_image: Optional[str] = None


class PlaylistResponse(BaseModel):
    playlist_name: str
    songs: List[Song]
    spotify_playlist_url: Optional[str] = None


def get_spotify_auth_url():
    scope = "playlist-modify-private playlist-modify-public user-read-private"
    auth_url = f"https://accounts.spotify.com/authorize?client_id={SPOTIFY_CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={scope}"
    return auth_url


def access_token(auth_code):
    # FIXED: Removed the space between client ID and secret
    auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }
    
    # Print request details for debugging
    print(f"Token request details:")
    print(f"Endpoint: https://accounts.spotify.com/api/token")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Auth code length: {len(auth_code)} characters")
    
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)

    if response.status_code != 200:
        # Get the full error message from Spotify
        error_detail = f"Failed to get access token: {response.status_code}\nSpotify response: {response.text}"
        print(error_detail)  # Log to console for debugging
        raise HTTPException(status_code=400, detail=error_detail)
        
    return response.json()


def search_spot_songs(query, access_token, limit=5):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": query,
        "type": "track",
        "limit": limit
    }

    response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to search Spotify")
    
    results = response.json()
    songs = []

    for item in results["tracks"]["items"]:
    
        songs.append(
            Song(
                name=item["name"],
                artist=", ".join([artist["name"] for artist in item["artists"]]),
                uri=item["uri"],
                album_image=item["album"]["images"][0]["url"] if item["album"]["images"] else None
            )
        )

    return songs


def create_spot_playlist(name, description, uris, access_token):
    # Clean the access token to ensure proper formatting
    if access_token:
        access_token = access_token.strip()
        # Remove quotes if they were accidentally included
        if access_token.startswith('"') and access_token.endswith('"'):
            access_token = access_token[1:-1]
            
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    
    user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if user_response.status_code != 200:
        error_detail = f"Failed to get user info: {user_response.status_code}\nSpotify response: {user_response.text}"
        print(error_detail)  # Log to console for debugging
        raise HTTPException(status_code=400, detail=error_detail)
    
    user_id = user_response.json()["id"]

    # create playlist
    playlist_data = {
        "name": name,
        "description": description,
        "public": True
    }

   
    playlist_response = requests.post(
        f"https://api.spotify.com/v1/users/{user_id}/playlists",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(playlist_data)
    )

    if playlist_response.status_code not in [200, 201]:
        error_detail = f"Failed to create playlist: {playlist_response.status_code}\nSpotify response: {playlist_response.text}"
        print(error_detail)  # Log to console for debugging
        raise HTTPException(status_code=400, detail=error_detail)
    
    playlist_id = playlist_response.json()["id"]

    # add tracks to the created playlist
    add_tracks_response = requests.post(
        f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps({"uris": uris})
    )

    if add_tracks_response.status_code not in [200, 201]:
        error_detail = f"Failed to add tracks to playlist: {add_tracks_response.status_code}\nSpotify response: {add_tracks_response.text}"
        print(error_detail)  # Log to console for debugging
        raise HTTPException(status_code=400, detail=error_detail)
    
    return playlist_response.json()["external_urls"]["spotify"]


# OpenAI LLM functions
def generate_song_queries(mood_description, num_songs=10):
    prompt = f"""
    Generate {num_songs} specific song search queries based on the following mood description:
    "{mood_description}"

    Each query should be a SIMPLE search term without special formatting.
    For example: "Adele Hello" or "Ed Sheeran Shape of You" or "Queen Bohemian Rhapsody"
    
    Format your response as a JSON object with a "queries" array.
    Example: {{"queries": ["Adele Hello", "Ed Sheeran Shape of You"]}}
    """

    print(f"Generating song queries for mood: {mood_description}")
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a music expert that suggests songs matching specific moods."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    try:
        content = response.choices[0].message.content
        print(f"OpenAI response: {content[:100]}...")
        queries = json.loads(content)["queries"]
        print(f"Parsed {len(queries)} queries: {queries[:3]}...")
        return queries
    except (KeyError, json.JSONDecodeError) as e:
        error_message = f"Failed to parse OpenAI response: {str(e)}"
        print(error_message)
        print(f"Raw response: {response.choices[0].message.content}")
        raise HTTPException(status_code=500, detail=error_message)
    

def generate_playlist_name(mood_description):
    prompt = f"""
    Create a catchy, fun and descriptive playlist name based on this mood description:
    "{mood_description}"

    Return ONLY the playlist name as plain text, no quotes, asterisk or explanation
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You have an experience in the music industry, and you are a creative playlist naming assistant"},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

# Routes
@app.get("/auth-url")
async def get_auth_url_route():
    """Gets spotify auth url"""
    auth_url = get_spotify_auth_url()
    return {"auth_url": auth_url}

@app.post("/get-token")
async def get_token_route(request: AuthRequest):
    """Exchange auth code for access token"""
    try:
        token_info = access_token(request.code)
        return token_info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/generate-playlist", response_model=PlaylistResponse)
async def generate_playlist(mood_request: MoodRequest, access_token: str):
    """Generate a playlist based on mood description"""
    try:
        # Log the access token format for debugging
        print(f"Received access token: {access_token[:10]}..." if access_token and len(access_token) > 10 else "Invalid access token")
        
        # Clean the token for consistency
        if access_token:
            access_token = access_token.strip()
            if access_token.startswith('"') and access_token.endswith('"'):
                access_token = access_token[1:-1]
                print("Removed quotes from access token")
        
        playlist_name = generate_playlist_name(mood_request.mood_description)
        print(f"Generated playlist name: {playlist_name}")

        song_queries = generate_song_queries(mood_request.mood_description, mood_request.num_songs)
        print(f"Generated {len(song_queries)} song queries")

        all_songs = []

        for query in song_queries:
            print(f"Processing query: {query}")
            songs = search_spot_songs(query, access_token, limit=1)

            if songs:
                all_songs.append(songs[0])
                print(f"Added song: {songs[0].name} by {songs[0].artist}")

            if len(all_songs) >= mood_request.num_songs:
                break

        if not all_songs:
            raise HTTPException(status_code=400, detail="Could not find any matching songs")
        
        print(f"Found {len(all_songs)} songs")
        uris = [song.uri for song in all_songs]

        playlist_url = create_spot_playlist(
            playlist_name,
            f"Generated based on mood: {mood_request.mood_description}",
            uris,
            access_token
        )

        return PlaylistResponse(
            playlist_name=playlist_name,
            songs=all_songs,
            spotify_playlist_url=playlist_url
        )
    except Exception as e:
        error_message = str(e)
        print(f"Error in generate_playlist: {error_message}")
        raise HTTPException(status_code=500, detail=error_message)
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)