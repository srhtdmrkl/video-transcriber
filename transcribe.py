import wave
import json
import os
from vosk import Model, KaldiRecognizer
from moviepy.editor import VideoFileClip
import srt
from datetime import timedelta
from pydub import AudioSegment

# Function to extract audio from video
def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)

# Function to convert audio to required format
def convert_audio(audio_path, wav_path):
    audio = AudioSegment.from_file(audio_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")

# Function to transcribe audio to text using Vosk
def transcribe_audio(model_path, wav_path):
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)

    results = []
    with wave.open(wav_path, "rb") as wf:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                results.append(json.loads(rec.Result()))
            else:
                results.append(json.loads(rec.PartialResult()))
        results.append(json.loads(rec.FinalResult()))

    words = []
    for result in results:
        if 'result' in result:
            words.extend(result['result'])
    return words

# Function to group words into subtitle segments
def group_words_into_segments(words, max_segment_duration=5.0):
    segments = []
    segment = []
    segment_start = words[0]['start']
    
    for word in words:
        segment.append(word)
        segment_end = word['end']
        
        # Check if the segment duration exceeds the maximum duration
        if segment_end - segment_start > max_segment_duration:
            segments.append(segment)
            segment = [word]
            segment_start = word['start']
    
    # Append the last segment
    if segment:
        segments.append(segment)
    
    return segments

# Function to create SRT file from transcription segments
def create_srt(segments, srt_path):
    subs = []
    for i, segment in enumerate(segments):
        start = timedelta(seconds=segment[0]["start"])
        end = timedelta(seconds=segment[-1]["end"])
        content = " ".join([word["word"] for word in segment])
        subs.append(srt.Subtitle(index=i+1, start=start, end=end, content=content))
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(subs))

# Main function to process video
def transcribe_video_to_srt(video_path, audio_path, wav_path, srt_path, model_path):
    extract_audio(video_path, audio_path)
    convert_audio(audio_path, wav_path)
    words = transcribe_audio(model_path, wav_path)
    segments = group_words_into_segments(words)
    create_srt(segments, srt_path)

# Example usage
video_path = "example/invideo.mp4"  # Path to your MKV video file
audio_path = "example/extracted_audio.mp3"
wav_path = "example/extracted_audio.wav"
srt_path = "example/output_subtitle.srt"
model_path = "eaxmple/vosk-model-small-en-us-0.15"  # Path to the Vosk model directory

transcribe_video_to_srt(video_path, audio_path, wav_path, srt_path, model_path)