import spotipy
import time
import random
from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session,redirect,render_template

app = Flask(__name__)
app.config['SESSION_COOKIE_NAME']='Spotify cookie'
app.config["SESSION_PERMANENT"] = False
app.secret_key='sarisha190603!@#='
TOKEN_INFO = 'token_info'

@app.route("/")
def login():
    auth_url=create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route("/redirect")
def redirect_page():    
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code,check_cache=False)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('_aura_', external = True))

@app.route("/Aura")
def _aura_():
    try:
        token_info = get_token()
    except:
        print("Not logged in")
        return redirect('/')
    
    sp = spotipy.Spotify(auth = token_info['access_token'])
    user_id = sp.current_user()['id']
    user_name = sp.current_user()['display_name']
    
    recent_top = sp.current_user_top_tracks(limit = 20, time_range="short_term", offset = 0)["items"]
    top_songs = []
    for song in recent_top: 
        song_artists = [artist['name'] for artist in song['artists']]
        top_songs.append({'uri':song['uri'],'name':song['name'],'artists':song_artists})

    print('Your top songs are:')
    for song in top_songs:
        print(song['name'])


    features = []
    top_songs_uri = []
    for song in top_songs:
        uri = song['uri']
        top_songs_uri.append(uri) #to check for matching uris in recs
        song_feature = sp.audio_features(uri)[0]
        features.append({'danceability': song_feature['danceability'],
                         'energy': song_feature['energy'], 
                         'valence': song_feature['valence']})

    mean_features = {}
    for feature in features[0].keys():
        mean_features[feature] = sum(d[feature] for d in features) / len(features)

    danceability_val = mean_features['danceability']
    energy_val = mean_features['energy']
    valence_val = mean_features['valence']

    if (danceability_val >= 0.75 ):        
        d_colour = 'ff8400'
    elif(danceability_val >= 0.5):
        d_colour = 'f1a155'
    elif(danceability_val >= 0.25):
        d_colour = '9d5bc0'
    else:
        d_colour='801ba1'

    if (energy_val >= 0.75 ):        
        e_colour = 'ff0000'
    elif(energy_val >= 0.5):
        e_colour = 'd16539'
    elif(energy_val >= 0.25):
        e_colour = 'aae49b'
    else:
        e_colour='008a15'

    if (valence_val>= 0.75 ):        
        v_colour = 'ffff00'
    elif(valence_val>= 0.5):
        v_colour = 'ffff6b'
    elif(valence_val>= 0.25):
        v_colour = '1c57ba'
    else:
        v_colour='0000ff'

    seed_tracks=[song['uri'] for song in random.sample(top_songs,5)]
    song_recs = sp.recommendations(seed_tracks=seed_tracks,limit=50)
    song_id = []
    for song in song_recs['tracks']:
        if song['uri'] in top_songs_uri:
            continue
        song_id.append(song['id'])
        if len(song_id) == 20:
            break
    recs = sp.user_playlist_create(user=user_id,name='u might also like these',description = 'generated for u by Aura!')
    recs_id=recs['id']
    recs_link=recs['external_urls']['spotify']
    sp.playlist_add_items(recs_id, song_id)
    return('Hi '+user_name+ '!\n Check the spotify app for recommendations')



def get_token():
    token_info = session.get(TOKEN_INFO)
    if not token_info:
        redirect(url_for('login', external = False))

    now = int(time.time()) 

    is_expired = token_info['expires_at'] - now < 60 
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    
    return token_info


def create_spotify_oauth():
    print('created')
    return SpotifyOAuth(client_id = "4a87870b890643f1825c31b593f1886d",
                        client_secret = "56c5fb3ae0d048d8b5f3d7d1a1f8340c",
                        redirect_uri=url_for('redirect_page', _external=True),
                        scope = 'user-top-read,ugc-image-upload, playlist-modify-public, playlist-modify-private')

app.run(debug = True)