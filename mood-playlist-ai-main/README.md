# 🎵 Mood-Based Playlist Generator 🎵

> *"Music is the shorthand of emotion."* - Leo Tolstoy

Ever been in one of those moods where you just can't find the right playlist? Maybe you're "feeling nostalgic about summer road trips" or perhaps "need focus music with a hint of jazz"? Say no more! This API brings your musical moods to life by generating custom Spotify playlists based on your feelings.

## ✨ What Is This Magic?

This is a FastAPI application that creates personalized Spotify playlists based on your mood descriptions. It combines the intelligence of OpenAI's language models with Spotify's vast music library to curate the perfect soundtrack for any feeling.

### 🧠 → 🎧 How It Works

1. You describe your mood ("anxious but ready to conquer the day")
2. AI generates song suggestions that match your vibe
3. The app creates a custom Spotify playlist with those songs
4. You get a direct link to your new mood-matched playlist!

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Spotify account 
- Spotify Developer App credentials
- OpenAI API key
- A range of emotions (we all have them)

### Installation

```bash
# Clone the repo (or download it)
git clone https://github.com/Chukwuebuka-2003/mood-playlist-ai.git
cd mood-playlist-generator

# Install dependencies
pip install -r requirements.txt

# Create your .env file
touch .env
```

Add the following to your `.env` file:

```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
OPENAI_API_KEY=your_openai_api_key
REDIRECT_URI=http://localhost:8888/callback
```

### ⚙️ Spotify Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Create a new app
3. Add `http://localhost:8888/callback` as the Redirect URI
4. Copy your Client ID and Client Secret to your `.env` file

## 🎮 Using the API

Start the server:

```bash
uvicorn api:app --reload --port 8888
```

### 1️⃣ Step 1: Get an Authorization URL

```bash
curl http://localhost:8888/auth-url
```

This returns a Spotify authorization URL. Open it in your browser and authorize the app.

### 2️⃣ Step 2: Exchange the Code for a Token

After authorization, you'll be redirected to a URL with a code parameter. Extract this code and use it:

```bash
curl -X POST http://localhost:8888/get-token \
  -H "Content-Type: application/json" \
  -d '{"code":"your_authorization_code_here"}'
```

### 3️⃣ Step 3: Generate a Playlist Based on Your Mood

```bash
curl -X POST "http://localhost:8888/generate-playlist?access_token=your_access_token" \
  -H "Content-Type: application/json" \
  -d '{"mood_description":"feeling hopeful but with a touch of melancholy", "num_songs":10}'
```

## 🥳 Example Moods to Try

- "Energetic morning workout vibes"
- "Relaxed Sunday afternoon with coffee and a book"
- "Late night coding session focus"
- "90s nostalgia with an indie twist"
- "First date nervous excitement"
- "Rainy day contemplation"
- "Beach vacation sunset feels"

## 💡 Behind the Scenes

This app leverages:

- **FastAPI**: For creating the API endpoints
- **OpenAI API**: To interpret your mood and suggest appropriate songs
- **Spotify API**: To search for songs and create playlists
- **Your unique emotions**: The secret ingredient!

## 🐛 Troubleshooting

- **"Failed to get access token"**: Your authorization code has expired or was already used. Get a new one!
- **"Only valid bearer authentication supported"**: Check your access token format. No quotes or extra spaces!
- **"Failed to search Spotify"**: The song query format might be incorrect or your token expired.

## 🎁 The Mood Magic

The real magic happens in the `generate_song_queries` function, where AI interprets your mood into tangible song suggestions. It's like having a music-savvy friend who always knows exactly what you need to hear.

---

## 🎵 Playlist Showcase

Made any cool playlists with this app? Share them by adding to this README!

- ["Afrobeat Chill & Thrill"](https://open.spotify.com/playlist/0NyViXFkliEUad5mindYzY?si=ZPAHnV98RgGugFR9XEsY8A) - For that AfroBeats vibe
- ["Bittersweet Sunshine"](https://open.spotify.com/playlist/3x5V6ZUgwbgOYS2kDP70Dp?si=GHRPkl5ERoul1zbr59r0iA) - Feeling hopeful

---

Created with ❤️ and 🎵
