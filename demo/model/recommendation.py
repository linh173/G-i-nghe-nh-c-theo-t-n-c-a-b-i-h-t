import pandas as pd
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import random

def calculate_weighted_popularity(release_date):
    release_date = datetime.strptime(release_date, '%Y-%m-%d')
    time_span = datetime.now() - release_date
    weight = 1 / (time_span.days + 1)
    return weight

def content_based_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return

    input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]
    similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)
    similar_song_indices = similarity_scores.argsort()[0][::-1][1:num_recommendations + 1]
    content_based_recommendations = music_df.iloc[similar_song_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]
    return content_based_recommendations

def hybrid_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations=5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return

    content_based_rec = content_based_recommendations(input_song_name, music_df, music_features_scaled, num_recommendations + 1)
    input_song_row = music_df[music_df['Track Name'] == input_song_name]
    weighted_popularity_score = input_song_row['Popularity'].iloc[0] * calculate_weighted_popularity(input_song_row['Release Date'].iloc[0])
    input_song_df = input_song_row.copy()
    input_song_df['Popularity'] = weighted_popularity_score
    hybrid_recommendations_df = pd.concat([content_based_rec, input_song_df])
    hybrid_recommendations_df = hybrid_recommendations_df.sort_values(by='Popularity', ascending=False)

    return hybrid_recommendations_df
def get_external_urls(input_song_name, recommended_songs, music_df):
    external_urls = {}

    # Truy xuất URL bên ngoài của bài hát đầu vào
    input_song_row = music_df[music_df['Track Name'] == input_song_name]
    if not input_song_row.empty:
        input_song_url = input_song_row['External URLs'].iloc[0]
        input_song_id = input_song_row['Track ID'].iloc[0]
        external_urls[input_song_name] = {'url': input_song_url, 'id': input_song_id}
    else:
        print(f"URL not found for '{input_song_name}'.")
        external_urls[input_song_name] = {'url': None, 'id': None}

    # Truy xuất URL bên ngoài của các bài hát được đề xuất
    for song_name in recommended_songs:
        song_row = music_df[music_df['Track Name'] == song_name]
        if not song_row.empty:
            external_url = song_row['External URLs'].iloc[0]
            track_id = song_row['Track ID'].iloc[0]
            external_urls[song_name] = {'url': external_url, 'id': track_id}
        else:
            print(f"URL not found for '{song_name}'.")
            external_urls[song_name] = {'url': None, 'id': None}

    return external_urls
def get_random_recommendations(music_df, num_recommendations=10):
    random_indices = random.sample(range(len(music_df)), num_recommendations)
    random_recommendations = music_df.iloc[random_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]
    return random_recommendations

