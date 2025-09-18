import streamlit as st
import os
import sys
sys.path.append('/home/dyai/Dokumente/DYAI_home/DEV/GIT_repos/PROMATRA')

# Import required libraries
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
import tempfile
import yaml

def extract_prosody_enhanced(pcm_f32: np.ndarray, sr: int, t0: float, t1: float) -> dict:
    """Simplified enhanced prosody extraction with CONFIG ENGI features"""
    i0, i1 = max(int(t0 * sr), 0), max(int(t1 * sr), 0)
    seg = pcm_f32[i0:i1] if i1 > i0 else np.zeros(0, dtype=np.float32)

    if seg.size == 0:
        return _get_default_prosody_features()

    # Basic features
    rms = float(np.sqrt(float(np.mean(seg.astype(np.float32) ** 2)) + 1e-9))
    zcr = float(np.mean(np.abs(np.diff(np.signbit(seg))) > 0)) if seg.size > 1 else 0.0

    # F0 analysis
    f0_features = _extract_f0_features(seg, sr, t0, t1)

    # Jitter/Shimmer
    voice_quality = _extract_voice_quality(seg, f0_features['f0v'])

    # Spectral features
    spectral_features = _extract_spectral_features(seg, sr)

    return {
        **f0_features,
        **voice_quality,
        **spectral_features,
        "rms": rms,
        "zcr": zcr,
        "intensity_db_mean": 20 * np.log10(rms) if rms > 0 else -100.0,
        "speech_rate_syl_per_s": 5.0,
        "articulation_rate_syl_per_s": 5.5,
        "pause_count": 0,
        "pause_total_s": 0.0,
    }


def _get_default_prosody_features():
    """Default prosody features for empty segments"""
    return {
        "f0_mean": 0.0, "f0_std": 0.0, "f0_med": 0.0, "f0_p10": 0.0, "f0_p90": 0.0,
        "f0_range": 0.0, "f0_slope_end": 0.0, "voicing": 0.0,
        "jitter_rel": 0.0, "shimmer_rel": 0.0,
        "zcr_mean": 0.0, "spectral_flux_mean": 0.0, "flatness": 0.0,
        "rms": 0.0, "intensity_db_mean": -100.0,
        "speech_rate_syl_per_s": 5.0, "articulation_rate_syl_per_s": 5.5,
        "pause_count": 0, "pause_total_s": 0.0, "final_f0_slope": 0.0
    }


def _extract_f0_features(seg, sr, t0, t1):
    """Extract F0-related features"""
    try:
        f0, _, _ = librosa.pyin(seg.astype(np.float32), fmin=50, fmax=500, sr=sr,
                              frame_length=2048, hop_length=256)
        f0 = np.nan_to_num(f0, nan=0.0)
        voiced = f0 > 0
        f0v = f0[voiced]
        voicing = float(np.mean(voiced)) if f0.size else 0.0

        if f0v.size:
            f0_med = float(np.median(f0v))
            f0_p10 = float(np.percentile(f0v, 10))
            f0_p90 = float(np.percentile(f0v, 90))
            f0_range = float(f0_p90 - f0_p10)
            f0_mean = float(np.mean(f0v))
            f0_std = float(np.std(f0v))

            # F0 slope calculation
            n = len(f0v)
            k = max(3, min(n, 10))
            y = f0v[-k:]
            x = np.arange(len(y), dtype=np.float32)
            x = (x - x[0]) / max(1.0, len(y) - 1)
            A = np.vstack([x, np.ones_like(x)]).T
            m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
            fps = n / max(1e-3, (t1 - t0))
            f0_slope_end = float(m * fps)
        else:
            f0_med = f0_p10 = f0_p90 = f0_range = f0_mean = f0_std = f0_slope_end = 0.0
    except Exception:
        f0_med = f0_p10 = f0_p90 = f0_range = f0_mean = f0_std = f0_slope_end = voicing = 0.0
        f0v = np.zeros(0, dtype=np.float32)

    return {
        "f0_mean": f0_mean, "f0_std": f0_std, "f0_med": f0_med,
        "f0_p10": f0_p10, "f0_p90": f0_p90, "f0_range": f0_range,
        "f0_slope_end": f0_slope_end, "voicing": voicing, "f0v": f0v
    }


def _extract_voice_quality(seg, f0v):
    """Extract jitter and shimmer"""
    if f0v.size > 10:
        f0_diffs = np.abs(np.diff(f0v))
        jitter = np.mean(f0_diffs) / np.mean(f0v) if np.mean(f0v) > 0 else 0.0
    else:
        jitter = 0.0

    rms_frames = librosa.feature.rms(y=seg, frame_length=256, hop_length=128)[0]
    if len(rms_frames) > 10:
        rms_diffs = np.abs(np.diff(rms_frames))
        shimmer = np.mean(rms_diffs) / np.mean(rms_frames) if np.mean(rms_frames) > 0 else 0.0
    else:
        shimmer = 0.0

    return {"jitter_rel": float(jitter), "shimmer_rel": float(shimmer)}


def _extract_spectral_features(seg, sr):
    """Extract spectral features"""
    if seg.size > 0:
        n = 1 << (int(np.ceil(np.log2(len(seg)))) or 1)
        X = np.abs(np.fft.rfft(seg, n=n)) + 1e-12
        geo = np.exp(np.mean(np.log(X)))
        arith = np.mean(X)
        flatness = float(geo / arith)
    else:
        flatness = 0.0

    zcr = float(np.mean(np.abs(np.diff(np.signbit(seg))) > 0)) if seg.size > 1 else 0.0
    spectral_flux = float(np.mean(librosa.onset.onset_strength(y=seg, sr=sr)))

    return {
        "zcr_mean": zcr,
        "spectral_flux_mean": spectral_flux,
        "flatness": flatness
    }


def evaluate_marker_rule(rule_str, prosody_values):
    """
    Safely evaluate marker rules with variable substitution
    """
    try:
        # Replace variables with their values
        eval_str = rule_str
        
        # Handle numeric comparisons
        eval_str = eval_str.replace('jitter_z', str(prosody_values.get('jitter_rel', 0)))
        eval_str = eval_str.replace('shimmer_z', str(prosody_values.get('shimmer_rel', 0)))
        eval_str = eval_str.replace('final_f0_slope', str(prosody_values.get('f0_slope_end', 0)))
        eval_str = eval_str.replace('f0_mean', str(prosody_values.get('f0_mean', 0)))
        eval_str = eval_str.replace('f0_std', str(prosody_values.get('f0_std', 0)))
        eval_str = eval_str.replace('intensity_db_mean', str(prosody_values.get('intensity_db_mean', 0)))
        eval_str = eval_str.replace('voicing', str(prosody_values.get('voicing', 0)))
        eval_str = eval_str.replace('threshold', '0.3')
        
        # Replace logical operators with Python equivalents
        eval_str = eval_str.replace(' OR ', ' or ')
        eval_str = eval_str.replace(' AND ', ' and ')
        eval_str = eval_str.replace(' NOT ', ' not ')
        
        # Evaluate the expression
        result = eval(eval_str)
        return bool(result), eval_str
        
    except Exception as e:
        print(f"Rule evaluation error: {e}, rule: {eval_str}")
        return False, eval_str


def load_marker_weights():
    """Load marker weights from CONFIG ENGI style configuration"""
    weights_config = {
        'SEM_SOFT_DECLINE': 1.2,
        'CLU_PROCRASTINATION_LOOP': 1.5,
        'SEM_TENSION_MICROINSTABILITY': 1.8,
        'SEM_ASSURED_CLOSURE': 1.6,
        'ATO_JITTER_HIGH': 1.4,
        'ATO_SHIMMER_HIGH': 1.3,
        'ATO_VOICE_BREAK_EVENT': 1.7,
        'SEM_INSECURE_QUESTION': 1.1,
        'ATO_BOUNDARY_SETTING': 1.4,
        'ATO_FIRST_PERSON_PRONOUN': 1.0,
        'MEMA_SELF_NARRATIVE_STABILITY': 2.0,
        'ATO_F0_RISE_FINAL': 1.2,
        'ATO_F0_VARIANCE_LOW': 1.1,
        'ATO_INTENSITY_DIP': 1.3,
        'ATO_LAUGHTER': 1.5,
        'ATO_LONG_RESPONSE_GAP': 1.2,
        'ATO_OVERLAP_INTERRUPT': 1.6,
        'ATO_PAUSE_LONG': 1.1,
        'ATO_SIGH': 1.4,
        'ATO_SPEECHRATE_DROP': 1.3,
        'CLU_DISSONANCE_ALERT_AUDIO': 1.7,
        'CLU_MISUNDERSTANDING_AUDIO': 1.5,
        'MEMA_DissonanceTrend_AUDIO': 1.8,
        'SEM_AROUSAL_SPIKE_AT_BREAK': 1.6,
        'SEM_REACTION_FORMATION_AUDIO': 1.4,
        'SEM_REPAIR_ATTEMPT_AUDIO': 1.3,
        'SEM_REPAIR_FAILURE_AUDIO': 1.2,
        'SEM_SHAME_PROSODY': 1.5,
        'SEM_UNCERTAINTY_PROSODY': 1.4,
        'ATO_JITTER_SHIMMER_HIGH': 1.4
    }
    return weights_config


def apply_adaptive_thresholds(marker_id, base_score, context=None):
    """
    Apply adaptive thresholds based on CONFIG ENGI intuition system
    Uses context-aware weighting and precision-based adjustments
    """
    weights = load_marker_weights()

    # Base weight from configuration
    weight = weights.get(marker_id, 1.0)

    # Context adjustments
    if context:
        if context.get('lang') == 'de':
            weight *= 1.1  # German language adjustment
        if context.get('channel') == 'audio':
            weight *= 1.2  # Audio channel priority
        if context.get('channel') == 'chat':
            weight *= 0.9  # Chat channel adjustment

    # Adaptive threshold based on base_score
    if base_score > 0.8:
        threshold = 0.3  # Lower threshold for high confidence
    elif base_score > 0.6:
        threshold = 0.5  # Medium threshold
    else:
        threshold = 0.7  # Higher threshold for low confidence

    adjusted_score = base_score * weight

    return adjusted_score, threshold, weight


def extract_prosody(audio, sr, t0, t1):
    start_sample = int(t0 * sr)
    end_sample = int(t1 * sr)
    seg_audio = audio[start_sample:end_sample]
    
    # F0 extraction
    f0, _, _ = librosa.pyin(seg_audio, fmin=75, fmax=600, sr=sr)
    f0_mean = np.nanmean(f0)
    f0_std = np.nanstd(f0)
    
    # Voicing ratio
    voicing = float(np.mean(~np.isnan(f0))) if len(f0) > 0 else 0.0
    
    # Final F0 slope
    final_f0_slope = _calculate_f0_slope(f0)
    
    # Intensity
    rms = librosa.feature.rms(y=seg_audio)[0]
    intensity_db_mean = 20 * np.log10(np.mean(rms))
    
    # Speech rate (placeholder - will be calculated from words)
    speech_rate = 5.0
    articulation_rate = 5.5
    
    # Pauses
    pause_count = 0
    pause_total = 0.0
    
    # Jitter/Shimmer calculation
    jitter, shimmer = _calculate_jitter_shimmer(f0, rms)
    
    # ZCR
    zcr = np.mean(librosa.feature.zero_crossing_rate(seg_audio)[0])
    
    # Spectral flux
    spectral_flux = np.mean(librosa.onset.onset_strength(y=seg_audio, sr=sr))
    
    return {
        'f0_mean': float(f0_mean),
        'f0_std': float(f0_std),
        'intensity_db_mean': float(intensity_db_mean),
        'speech_rate_syl_per_s': float(speech_rate),
        'articulation_rate_syl_per_s': float(articulation_rate),
        'pause_count': int(pause_count),
        'pause_total_s': float(pause_total),
        'jitter_rel': float(jitter),
        'shimmer_rel': float(shimmer),
        'zcr_mean': float(zcr),
        'spectral_flux_mean': float(spectral_flux),
        'final_f0_slope': float(final_f0_slope),
        'voicing': float(voicing)  # Add voicing ratio
    }


def _calculate_f0_slope(f0):
    """Calculate final F0 slope from the last frames."""
    if len(f0) > 10:
        last_frames = min(50, len(f0) // 2)
        f0_last = f0[-last_frames:]
        times = np.arange(last_frames)
        valid = ~np.isnan(f0_last)
        if np.sum(valid) > 5:
            slope = np.polyfit(times[valid], f0_last[valid], 1)[0]
        else:
            slope = 0.0
    else:
        slope = 0.0
    return slope


def _calculate_jitter_shimmer(f0, rms):
    """Calculate jitter and shimmer from F0 and RMS."""
    # Filter out NaN values from F0
    f0_clean = f0[~np.isnan(f0)]
    if len(f0_clean) > 10:
        # Jitter: average absolute difference of consecutive F0 periods
        f0_diffs = np.abs(np.diff(f0_clean))
        jitter = np.mean(f0_diffs) / np.mean(f0_clean) if np.mean(f0_clean) > 0 else 0.0
        
        # Shimmer: average absolute difference of consecutive amplitudes
        rms_clean = rms[~np.isnan(rms)]
        if len(rms_clean) > 10:
            rms_diffs = np.abs(np.diff(rms_clean))
            shimmer = np.mean(rms_diffs) / np.mean(rms_clean) if np.mean(rms_clean) > 0 else 0.0
        else:
            shimmer = 0.0
    else:
        jitter = 0.0
        shimmer = 0.0
    
    return jitter, shimmer

st.title("PROMATRA Increment 1 - Audio Processor")

st.markdown("Lade eine Audiodatei hoch (.wav, .flac, .m4a, .mp3) und verarbeite sie zu einem annotierten Transkript.")

uploaded_file = st.file_uploader("Wähle eine Audiodatei", type=["wav", "flac", "m4a", "mp3"])

if uploaded_file is not None:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.read())
        audio_path = tmp_file.name

    st.audio(uploaded_file, format='audio/wav')

    if st.button("Verarbeiten"):
        with st.spinner("Verarbeitung läuft..."):
            try:
                # Load audio
                audio_asr, sr_asr = librosa.load(audio_path, sr=16000, mono=True)
                audio_orig, sr_orig = librosa.load(audio_path, sr=None, mono=True)

                st.write(f"Audio geladen: {sr_orig} Hz, {len(audio_orig)/sr_orig:.2f} min")

                # Preprocess
                rms = np.sqrt(np.mean(audio_orig**2))
                audio_norm = audio_orig * (0.1 / rms) if rms > 0 else audio_orig
                audio_norm -= np.mean(audio_norm)

                from scipy.signal import butter, filtfilt
                b, a = butter(4, [80, 8000], btype='band', fs=sr_orig)
                audio_filtered = filtfilt(b, a, audio_norm)

                frame_length = int(0.025 * sr_orig)
                hop_length = int(0.010 * sr_orig)
                energy = librosa.feature.rms(y=audio_filtered, frame_length=frame_length, hop_length=hop_length)[0]
                threshold = np.mean(energy) + 0.5 * np.std(energy)
                vad_segments = energy > threshold

                st.write(f"Vorverarbeitung abgeschlossen. VAD-Segmente: {np.sum(vad_segments)}")

                # Diarization (simple)
                segments = []
                start = 0
                for i in range(1, len(vad_segments)):
                    if not vad_segments[i] and vad_segments[i-1]:
                        end = i * hop_length / sr_orig
                        segments.append((start, end))
                        start = end
                    elif vad_segments[i] and not vad_segments[i-1]:
                        start = i * hop_length / sr_orig
                if vad_segments[-1]:
                    segments.append((start, len(audio_filtered) / sr_orig))

                speakers = ['S1', 'S2']
                diarization = []
                for idx, (t0, t1) in enumerate(segments):
                    speaker = speakers[idx % len(speakers)]
                    diarization.append({'t0': t0, 't1': t1, 'speaker_id': speaker})

                st.write(f"Diarisierung: {len(diarization)} Segmente, Sprecher: {set([d['speaker_id'] for d in diarization])}")

                # ASR
                model = whisper.load_model("base")
                result = model.transcribe(audio_path, word_timestamps=True)

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

                st.write(f"ASR abgeschlossen: {len(transcript_segments)} Segmente")

                # Prosody (simplified)
                for seg in transcript_segments:
                    seg['prosody'] = extract_prosody(audio_filtered, sr_orig, seg['t0'], seg['t1'])
                    
                    # Calculate speech rate from word timestamps
                    if seg['words']:
                        word_count = len(seg['words'])
                        duration = seg['t1'] - seg['t0']
                        if duration > 0:
                            # Words per second (approximate syllables per second)
                            seg['prosody']['speech_rate_syl_per_s'] = float(word_count / duration)
                            # Articulation rate (slightly higher than speech rate)
                            seg['prosody']['articulation_rate_syl_per_s'] = float(word_count / duration * 1.1)
                        else:
                            seg['prosody']['speech_rate_syl_per_s'] = 5.0
                            seg['prosody']['articulation_rate_syl_per_s'] = 5.5

                st.write("Prosodie extrahiert.")

                # Voice (dummy)
                rng = np.random.default_rng(42)  # Use modern random number generator
                for seg in transcript_segments:
                    seg['voice'] = {
                        'embedding': base64.b64encode(rng.random(192).tobytes()).decode(),
                        'quality': {
                            'roughness': float(rng.uniform(0.2, 0.8)),
                            'breathiness': float(rng.uniform(0.1, 0.5))
                        },
                        'speaker_stability': float(rng.uniform(0.8, 1.0))
                    }

                # Events
                # Collect per speaker
                speaker_data = {}
                voice_data = {}
                for seg in transcript_segments:
                    sid = seg['speaker_id']
                    if sid not in speaker_data:
                        speaker_data[sid] = []
                        voice_data[sid] = []
                    speaker_data[sid].append(seg['prosody'])
                    voice_data[sid].append(seg['voice'])

                # Compute baselines
                baselines = {}
                voice_baselines = {}
                for sid, pros in speaker_data.items():
                    baselines[sid] = {k: np.mean([p[k] for p in pros]) for k in pros[0].keys()}
                    voice_baselines[sid] = {
                        'roughness': np.mean([v['quality']['roughness'] for v in voice_data[sid]]),
                        'breathiness': np.mean([v['quality']['breathiness'] for v in voice_data[sid]]),
                        'jitter_rel': np.mean([p['jitter_rel'] for p in pros]),
                        'shimmer_rel': np.mean([p['shimmer_rel'] for p in pros]),
                        'final_f0_slope': np.mean([p['final_f0_slope'] for p in pros])
                    }

                # Load markers
                marker_dir = 'Marker_5.0_VOICE'
                markers = []
                if os.path.exists(marker_dir):
                    for file in os.listdir(marker_dir):
                        if file.endswith('.yaml'):
                            with open(os.path.join(marker_dir, file), 'r') as f:
                                marker = yaml.safe_load(f)
                                markers.append(marker)

                events_prosody = []
                events_clu = []
                events_voice = []
                prev_speaker = None
                for i, seg in enumerate(transcript_segments):
                    sid = seg['speaker_id']
                    base = baselines[sid]
                    vbase = voice_baselines[sid]
                    
                    # Compute z-scores
                    prosody_z = {k: (seg['prosody'][k] - base[k]) / base[k] if base[k] != 0 else 0 for k in base.keys()}
                    voice_z = {
                        'roughness': (seg['voice']['quality']['roughness'] - vbase['roughness']) / vbase['roughness'] if vbase['roughness'] != 0 else 0,
                        'breathiness': (seg['voice']['quality']['breathiness'] - vbase['breathiness']) / vbase['breathiness'] if vbase['breathiness'] != 0 else 0,
                        'jitter_rel': (seg['prosody']['jitter_rel'] - vbase['jitter_rel']) / vbase['jitter_rel'] if vbase['jitter_rel'] != 0 else 0,
                        'shimmer_rel': (seg['prosody']['shimmer_rel'] - vbase['shimmer_rel']) / vbase['shimmer_rel'] if vbase['shimmer_rel'] != 0 else 0,
                        'final_f0_slope': (seg['prosody']['final_f0_slope'] - vbase['final_f0_slope']) / vbase['final_f0_slope'] if vbase['final_f0_slope'] != 0 else 0
                    }
                    
                    # PROSODY_PEAK_ENERGY
                    if prosody_z['intensity_db_mean'] > 1.8:
                        events_prosody.append({
                            'id': f"evt_{len(events_prosody)+1}",
                            'label': 'PROSODY_PEAK_ENERGY',
                            'speaker_id': sid,
                            't0': seg['t0'],
                            't1': seg['t1'],
                            'score': 0.8
                        })
                    
                    # CLU_EMO_JOY
                    if seg['prosody']['f0_mean'] > base['f0_mean'] * 1.2:
                        events_clu.append({
                            'id': f"evt_joy_{len(events_clu)+1}",
                            'class': 'CLU_EMO_JOY',
                            'speaker_id': sid,
                            't0': seg['t0'],
                            't1': seg['t1'],
                            'score': 0.85,
                            'stable_s': 30,
                            'confirm': 1,
                            'retract': 0
                        })
                    
                    # Voice events
                    if prev_speaker and prev_speaker != sid:
                        events_voice.append({
                            'id': f"evt_change_{len(events_voice)+1}",
                            'label': 'SPEAKER_CHANGE',
                            'speaker_id': sid,
                            't0': seg['t0'],
                            't1': seg['t1'],
                            'score': 1.0
                        })
                    
                    if seg['voice']['speaker_stability'] < 0.8:
                        events_voice.append({
                            'id': f"evt_stability_{len(events_voice)+1}",
                            'label': 'SPEAKER_STABILITY_LOW',
                            'speaker_id': sid,
                            't0': seg['t0'],
                            't1': seg['t1'],
                            'score': seg['voice']['speaker_stability']
                        })
                    
                    if voice_z['roughness'] > 0.8:
                        events_voice.append({
                            'id': f"evt_roughness_{len(events_voice)+1}",
                            'label': 'VOICE_QUALITY_ROUGHNESS',
                            'speaker_id': sid,
                            't0': seg['t0'],
                            't1': seg['t1'],
                            'score': seg['voice']['quality']['roughness']
                        })
                    
                    if voice_z['breathiness'] > 0.8:
                        events_voice.append({
                            'id': f"evt_breathiness_{len(events_voice)+1}",
                            'label': 'VOICE_QUALITY_BREATHINESS',
                            'speaker_id': sid,
                            't0': seg['t0'],
                            't1': seg['t1'],
                            'score': seg['voice']['quality']['breathiness']
                        })
                    
                    # Apply loaded markers with CONFIG ENGI style weighting
                    for marker in markers:
                        if 'pattern' in marker and marker['pattern']:
                            pat = marker['pattern'][0]
                            if pat['detect_class'] == 'voice':
                                rule = pat['rule']
                                
                                # Use the new safe rule evaluation
                                prosody_values = {
                                    'jitter_rel': voice_z['jitter_rel'],
                                    'shimmer_rel': voice_z['shimmer_rel'],
                                    'f0_slope_end': seg['prosody'].get('final_f0_slope', 0),
                                    'f0_mean': seg['prosody'].get('f0_mean', 0),
                                    'f0_std': seg['prosody'].get('f0_std', 0),
                                    'intensity_db_mean': seg['prosody'].get('intensity_db_mean', 0),
                                    'voicing': seg['prosody'].get('voicing', 1.0)  # Default to 1.0 if not present
                                }
                                
                                rule_result, evaluated_rule = evaluate_marker_rule(rule, prosody_values)
                                
                                if rule_result:
                                    # Apply CONFIG ENGI style weighting
                                    base_score = 0.8
                                    context = {'channel': 'audio', 'lang': 'de'}
                                    adjusted_score, threshold, weight = apply_adaptive_thresholds(
                                        marker['id'], base_score, context
                                    )

                                    events_voice.append({
                                        'id': f"evt_{marker['id']}_{len(events_voice)+1}",
                                        'label': marker['id'],
                                        'speaker_id': sid,
                                        't0': seg['t0'],
                                        't1': seg['t1'],
                                        'score': adjusted_score,
                                        'weight': weight,
                                        'threshold': threshold,
                                        'rule_triggered': evaluated_rule,
                                        'detected': True
                                    })
                    
                    prev_speaker = sid

                st.write(f"Ereignisse: Prosody {len(events_prosody)}, CLU {len(events_clu)}, Voice {len(events_voice)}")

                # Generate outputs
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
                with jsonlines.open('events_clu.jsonl', 'w') as f:
                    f.write_all(events_clu)
                with jsonlines.open('events_voice.jsonl', 'w') as f:
                    f.write_all(events_voice)

                # Display results
                st.subheader("Transkript-Vorschau")
                for seg in annotated_segments:
                    st.write(f"**{seg['speaker_id']}** [{seg['t0']:.2f}-{seg['t1']:.2f}]: {seg['text']}")

                # Download links
                st.subheader("Downloads")
                # For simplicity, show as text; in real, use st.download_button
                st.text("Dateien generiert: transcript_annotated.jsonl, events_prosody.jsonl, events_clu.jsonl, events_voice.jsonl, transcript_preview.md")

                st.success("Verarbeitung abgeschlossen!")

            except Exception as e:
                st.error(f"Fehler: {str(e)}")
            finally:
                os.unlink(audio_path)  # Clean up temp file
