from flask import Flask, render_template, request
import pandas as pd
from model.recommendation import *
import requests
import base64
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
app = Flask(__name__)

CLIENT_ID = '306e8a22cf0549a49a4d7c86ee9008a3'
CLIENT_SECRET = 'f0591016a12148f4a9b4cd374d341212'

# Base64 encode the client ID and client secret
client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
client_credentials_base64 = base64.b64encode(client_credentials.encode())

# Request the access token
token_url = 'https://accounts.spotify.com/api/token'
headers = {'Authorization': f'Basic {client_credentials_base64.decode()}'}
data = {'grant_type': 'client_credentials'}
response = requests.post(token_url, data=data, headers=headers)

if response.status_code == 200:
    access_token = response.json()['access_token']
    print("Mã thông báo truy cập đã được lấy thành công.")
else:
    print("Lỗi lấy mã thông báo truy cập.")
    exit()
def get_trending_playlist_data(playlist_id, access_token):
    # Thiết lập Spotipy bằng mã thông báo truy cập
    sp = spotipy.Spotify(auth=access_token)

    # Nhận các bản nhạc từ danh sách phát
    playlist_tracks = sp.playlist_tracks(playlist_id, fields='items(track(id, name, artists, album(id, name)))')

    # Trích xuất thông tin liên quan và lưu trữ trong danh sách từ điển
    music_data = []
    for track_info in playlist_tracks['items']:
        track = track_info['track']
        track_name = track['name']
        artists = ', '.join([artist['name'] for artist in track['artists']])
        album_name = track['album']['name']
        album_id = track['album']['id']
        track_id = track['id']

        # Nhận các tính năng âm thanh cho bản nhạc
        audio_features = sp.audio_features(track_id)[0] if track_id != 'Not available' else None

        # Nhận ngày phát hành album
        try:
            album_info = sp.album(album_id) if album_id != 'Not available' else None
            release_date = album_info['release_date'] if album_info else None
        except:
            release_date = None

       # Nhận được sự phổ biến của bài hát
        try:
            track_info = sp.track(track_id) if track_id != 'Not available' else None
            popularity = track_info['popularity'] if track_info else None
        except:
            popularity = None

        # Thêm thông tin bản nhạc bổ sung vào dữ liệu bản nhạc
        track_data = {
            'Track Name': track_name,
            'Artists': artists,
            'Album Name': album_name,
            'Album ID': album_id,
            'Track ID': track_id,
            'Popularity': popularity,
            'Release Date': release_date,
            'Duration (ms)': audio_features['duration_ms'] if audio_features else None,
            'Explicit': track_info.get('explicit', None),
            'External URLs': track_info.get('external_urls', {}).get('spotify', None),
            'Danceability': audio_features['danceability'] if audio_features else None,
            'Energy': audio_features['energy'] if audio_features else None,
            'Key': audio_features['key'] if audio_features else None,
            'Loudness': audio_features['loudness'] if audio_features else None,
            'Mode': audio_features['mode'] if audio_features else None,
            'Speechiness': audio_features['speechiness'] if audio_features else None,
            'Acousticness': audio_features['acousticness'] if audio_features else None,
            'Instrumentalness': audio_features['instrumentalness'] if audio_features else None,
            'Liveness': audio_features['liveness'] if audio_features else None,
            'Valence': audio_features['valence'] if audio_features else None,
            'Tempo': audio_features['tempo'] if audio_features else None,

        }

        music_data.append(track_data)
    music_df = pd.DataFrame(music_data)
        # Chuẩn hóa các đặc trưng âm nhạc
    scaler = MinMaxScaler()
    music_features = music_df[['Danceability', 'Energy', 'Key', 
                               'Loudness', 'Mode', 'Speechiness', 'Acousticness',
                               'Instrumentalness', 'Liveness', 'Valence', 'Tempo']].values
    music_features_scaled = scaler.fit_transform(music_features)
    return music_df, music_features_scaled
playlist_id = '0s26Op11drslSFu5WgWVWJ'
# Gọi hàm để lấy dữ liệu nhạc từ danh sách phát và lưu trữ nó trong một DataFrame
music_df, music_features_scaled = get_trending_playlist_data(playlist_id, access_token)
def get_random_recommendations(music_df, num_recommendations=10):
    random_indices = random.sample(range(len(music_df)), num_recommendations)
    random_recommendations = music_df.iloc[random_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]
    return random_recommendations
@app.route('/', methods=['GET', 'POST'])
def index():
    input_song_name = None
    external_urls = None
    if request.method == 'POST':
        input_song_name = request.form.get('input_song_name')

    random_recommendations = get_random_recommendations(music_df)
    external_urls = get_external_urls('', random_recommendations['Track Name'], music_df)

    if input_song_name:
        recommendations = hybrid_recommendations(input_song_name=input_song_name, music_df=music_df, music_features_scaled=music_features_scaled, num_recommendations=5)
        external_urls.update(get_external_urls(input_song_name, recommendations['Track Name'], music_df))
        return render_template('index.html', input_song_name=input_song_name, hybrid_recommendations=recommendations, external_urls=external_urls, random_recommendations=random_recommendations)
    else:
        return render_template('index.html', random_recommendations=random_recommendations, external_urls=external_urls)

if __name__ == "__main__":
    app.run(debug=True)
