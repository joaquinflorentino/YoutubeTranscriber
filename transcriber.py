import youtube_dl
import requests
import os
import json
import time
from dotenv import load_dotenv
load_dotenv()

ASSEMBLYAI_TOKEN = os.getenv('ASSEMBLYAI_TOKEN')
CHUNK_SIZE = 5242880
WORKING_DIR = os.getcwd()
TRANSCRIPT_FILENAME = 'transcript.txt'

upload_endpoint = 'https://api.assemblyai.com/v2/upload'
transcript_endpoint = 'https://api.assemblyai.com/v2/transcript'

headers_auth = {'authorization': ASSEMBLYAI_TOKEN}
headers = {
    'authorization': ASSEMBLYAI_TOKEN,
    'content-type': 'application/json'
}

ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }],
    'ffmpeg-location': './',
}

def download_audio(url):
    source_id = url.strip()
    dl_audio = youtube_dl.YoutubeDL(ydl_opts).extract_info(source_id)

def get_audio_file():
    for file in os.listdir():
        if file.endswith('.mp3'):
            audio_file = os.path.join(WORKING_DIR, file)
            return audio_file
    return None

def read_file(filename, chunk_size=CHUNK_SIZE):
    with open(filename, 'rb') as file:
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            yield data

def upload_audio_file():
    audio_file = get_audio_file()
    upload_response = requests.post(upload_endpoint, headers=headers_auth, data=read_file(audio_file))
    print(upload_response.json())
    os.remove(audio_file)

    return upload_response.json()['upload_url']

def request_transcript_json(audio_url):
    transcript_request = {
        'audio_url': audio_url
    }

    transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
    print(transcript_response.json())
    return transcript_response.json()['id']

def poll_transcript_endpoint(transcript_id):
    polling_endpoint = transcript_endpoint + '/' + transcript_id
    time.sleep(15)
    polling_response = requests.get(polling_endpoint, headers=headers)

    while polling_response.json()['status'] != 'completed':
        print('Unable to retrieve a finished transcript at this point. Polling again in 30s')
        time.sleep(30)
        polling_response = requests.get(polling_endpoint, headers=headers)
    return polling_response

def save_transcript(url):
    download_audio(url)
    upload_response = upload_audio_file()
    transcript_id = request_transcript_json(upload_response)
    polling_response = poll_transcript_endpoint(transcript_id)
    transcript = polling_response.json()['words']

    with open(TRANSCRIPT_FILENAME, 'w') as file:
        file.write(json.dumps(transcript))
    print('Transcript saved to', TRANSCRIPT_FILENAME)
