import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import sys

# Add the project root to path to import modules if needed
sys.path.append('/home/dyai/Dokumente/DYAI_home/DEV/GIT_repos/PROMATRA')

# Import required libraries (same as notebook)
import librosa
import numpy as np
import scipy.signal
import soundfile as sf
import pandas as pd
import json
import jsonlines
import whisper
import torch
from pathlib import Path
import uuid
import base64

class PromatraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PROMATRA Increment 1 - Audio Processor")
        self.root.geometry("800x600")

        # Variables
        self.audio_path = None
        self.results = ""

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # File selection
        self.file_frame = tk.Frame(self.root)
        self.file_frame.pack(pady=10)

        self.file_label = tk.Label(self.file_frame, text="Audio File:")
        self.file_label.pack(side=tk.LEFT)

        self.file_entry = tk.Entry(self.file_frame, width=50)
        self.file_entry.pack(side=tk.LEFT, padx=5)

        self.browse_button = tk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.LEFT)

        # Process button
        self.process_button = tk.Button(self.root, text="Process Audio", command=self.start_processing)
        self.process_button.pack(pady=10)

        # Results display
        self.results_label = tk.Label(self.root, text="Results:")
        self.results_label.pack()

        self.results_text = scrolledtext.ScrolledText(self.root, width=90, height=25)
        self.results_text.pack(pady=10)

        # Status
        self.status_label = tk.Label(self.root, text="Ready")
        self.status_label.pack()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[("Audio Files", "*.wav *.flac *.m4a *.mp3"), ("All Files", "*.*")]
        )
        if file_path:
            self.audio_path = file_path
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)

    def start_processing(self):
        if not self.audio_path:
            messagebox.showerror("Error", "Please select an audio file first.")
            return

        self.status_label.config(text="Processing...")
        self.process_button.config(state=tk.DISABLED)
        self.results_text.delete(1.0, tk.END)

        # Run in thread to avoid freezing GUI
        thread = threading.Thread(target=self.process_audio)
        thread.start()

    def process_audio(self):
        try:
            # Load and preprocess audio
            sr_orig = self.load_audio()
            
            # Perform ASR
            transcript_segments = self.perform_asr()
            
            # Extract features
            self.extract_features(transcript_segments, sr_orig)
            
            # Generate events
            events_prosody = self.generate_events(transcript_segments)
            
            # Save results
            self.save_results(transcript_segments, events_prosody)
            
            self.update_results("Processing complete. Files generated: transcript_annotated.jsonl, events_prosody.jsonl, transcript_preview.md\n")

        except Exception as e:
            self.update_results(f"Error: {str(e)}\n")
        finally:
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
            self.root.after(0, lambda: self.process_button.config(state=tk.NORMAL))

    def update_results(self, text):
        self.root.after(0, lambda: self.results_text.insert(tk.END, text))
        self.root.after(0, lambda: self.results_text.see(tk.END))

    def load_audio(self):
        """Load and preprocess audio file."""
        audio_path = self.audio_path
        
        # Load audio (ignore ASR version since we don't use it)
        _, _ = librosa.load(audio_path, sr=16000, mono=True)  # audio_asr, sr_asr not used
        audio_orig, sr_orig = librosa.load(audio_path, sr=None, mono=True)
        
        self.update_results(f"Audio loaded: {sr_orig} Hz, {len(audio_orig)/sr_orig:.2f} min\n")
        
        # Preprocess
        rms = np.sqrt(np.mean(audio_orig**2))
        audio_norm = audio_orig * (0.1 / rms) if rms > 0 else audio_orig
        audio_norm -= np.mean(audio_norm)
        
        from scipy.signal import butter, filtfilt
        b, a = butter(4, [80, 8000], btype='band', fs=sr_orig)
        self.audio_filtered = filtfilt(b, a, audio_norm)
        
        frame_length = int(0.025 * sr_orig)
        hop_length = int(0.010 * sr_orig)
        energy = librosa.feature.rms(y=self.audio_filtered, frame_length=frame_length, hop_length=hop_length)[0]
        threshold = np.mean(energy) + 0.5 * np.std(energy)
        vad_segments = energy > threshold
        
        self.update_results(f"Preprocessing complete. VAD segments: {np.sum(vad_segments)}\n")
        
        return sr_orig

    def perform_asr(self):
        """Perform ASR and diarization."""
        # Simple diarization
        segments = self.perform_diarization()
        diarization = self.create_diarization_segments(segments)
        
        # ASR
        model = whisper.load_model("base")
        result = model.transcribe(self.audio_path, word_timestamps=True)
        
        transcript_segments = self.create_transcript_segments(result, diarization)
        
        self.update_results(f"ASR complete: {len(transcript_segments)} segments\n")
        
        return transcript_segments

    def perform_diarization(self):
        """Simple energy-based diarization."""
        frame_length = int(0.025 * self.sr_orig) if hasattr(self, 'sr_orig') else 400
        hop_length = int(0.010 * self.sr_orig) if hasattr(self, 'sr_orig') else 160
        
        energy = librosa.feature.rms(y=self.audio_filtered, frame_length=frame_length, hop_length=hop_length)[0]
        threshold = np.mean(energy) + 0.5 * np.std(energy)
        vad_segments = energy > threshold
        
        segments = []
        start = 0
        for i in range(1, len(vad_segments)):
            if not vad_segments[i] and vad_segments[i-1]:
                end = i * hop_length / self.sr_orig
                segments.append((start, end))
                start = end
            elif vad_segments[i] and not vad_segments[i-1]:
                start = i * hop_length / self.sr_orig
        if vad_segments[-1]:
            segments.append((start, len(self.audio_filtered) / self.sr_orig))
        
        return segments

    def create_diarization_segments(self, segments):
        """Create diarization segments with speaker IDs."""
        speakers = ['S1', 'S2']
        diarization = []
        for idx, (t0, t1) in enumerate(segments):
            speaker = speakers[idx % len(speakers)]
            diarization.append({'t0': t0, 't1': t1, 'speaker_id': speaker})
        
        self.update_results(f"Diarization: {len(diarization)} segments, speakers: {set([d['speaker_id'] for d in diarization])}\n")
        
        return diarization

    def create_transcript_segments(self, result, diarization):
        """Create transcript segments with speaker assignment."""
        transcript_segments = []
        for seg in result['segments']:
            speaker = 'S1'
            for d in diarization:
                if d['t0'] <= seg['start'] < d['t1']:
                    speaker = d['speaker_id']
                    break
            words = [{'w': w['word'], 't0': w['start'], 't1': w['end'], 'conf': w['probability']} for w in seg['words']]
            transcript_segments.append({
                't0': seg['start'],
                't1': seg['end'],
                'speaker_id': speaker,
                'text': seg['text'],
                'words': words
            })
        
        return transcript_segments

    def extract_features(self, transcript_segments, sr_orig):
        """Extract prosody and voice features."""
        def extract_prosody(audio, sr, t0, t1):
            start_sample = int(t0 * sr)
            end_sample = int(t1 * sr)
            seg_audio = audio[max(0, start_sample):min(len(audio), end_sample)]
            f0, _, _ = librosa.pyin(seg_audio, fmin=75, fmax=600, sr=sr)
            f0_mean = np.nanmean(f0) if not np.isnan(f0).all() else 0
            rms = librosa.feature.rms(y=seg_audio)[0]
            intensity = 20 * np.log10(np.mean(rms)) if np.mean(rms) > 0 else -100
            return {
                'f0_mean': f0_mean,
                'intensity_db_mean': intensity,
                'speech_rate_syl_per_s': 5.0,
                'pause_count': 0
            }
        
        for seg in transcript_segments:
            seg['prosody'] = extract_prosody(self.audio_filtered, sr_orig, seg['t0'], seg['t1'])
        
        self.update_results("Prosody extracted.\n")
        
        # Voice features with modern random generator
        rng = np.random.default_rng(42)
        for seg in transcript_segments:
            seg['voice'] = {
                'embedding': base64.b64encode(rng.random(192).tobytes()).decode(),
                'speaker_stability': 0.9
            }

    def generate_events(self, transcript_segments):
        """Generate prosody events."""
        events_prosody = []
        for seg in transcript_segments:
            if seg['prosody']['intensity_db_mean'] > -20:
                events_prosody.append({
                    'id': f"evt_{len(events_prosody)+1}",
                    'label': 'PROSODY_PEAK_ENERGY',
                    'speaker_id': seg['speaker_id'],
                    't0': seg['t0'],
                    't1': seg['t1'],
                    'score': 0.8
                })
        
        self.update_results(f"Events: {len(events_prosody)} prosody events\n")
        
        return events_prosody

    def save_results(self, transcript_segments, events_prosody):
        """Save results to files."""
        job_id = str(uuid.uuid4())
        annotated_segments = []
        for i, seg in enumerate(transcript_segments):
            annotated_segments.append({
                'job_id': job_id,
                'segment_id': f"seg_{i+1:06d}",
                't0': seg['t0'],
                't1': seg['t1'],
                'speaker_id': seg['speaker_id'],
                'text': seg['text'],
                'prosody': seg['prosody'],
                'voice': seg['voice'],
                'markers': []
            })
        
        # Write files
        with jsonlines.open('transcript_annotated.jsonl', 'w') as f:
            f.write_all(annotated_segments)
        with jsonlines.open('events_prosody.jsonl', 'w') as f:
            f.write_all(events_prosody)
        
        # Preview
        md_content = "# Transcript Preview\n\n"
        for seg in annotated_segments:
            md_content += f"**{seg['speaker_id']}** [{seg['t0']:.2f}-{seg['t1']:.2f}]: {seg['text']}\n\n"
        with open('transcript_preview.md', 'w') as f:
            f.write(md_content)

if __name__ == "__main__":
    root = tk.Tk()
    app = PromatraGUI(root)
    root.mainloop()
