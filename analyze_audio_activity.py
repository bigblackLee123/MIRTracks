import os
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import matplotlib.cm as cm
import matplotlib.colors as colors

def detect_silence(y, sr, threshold_db=-40, min_silence_duration=0.5):
    """
    Detect silent segments in audio
    
    Parameters:
    - y: audio signal
    - sr: sample rate
    - threshold_db: silence threshold (dB)
    - min_silence_duration: minimum silence duration (seconds)
    
    Returns:
    - silence_intervals: list of time intervals for silence [(start_time, end_time), ...]
    """
    # Calculate RMS energy
    frame_length = int(sr * 0.025)  # 25ms frame length
    hop_length = int(sr * 0.010)    # 10ms hop length
    
    # Calculate dB values
    S = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)
    S_db = librosa.amplitude_to_db(S, ref=np.max)
    
    # Extract silent frames
    silence_frames = np.where(S_db < threshold_db)[1]
    
    # Convert to time
    frame_times = librosa.frames_to_time(np.arange(len(S_db[0])), sr=sr, hop_length=hop_length)
    
    # Get continuous silence intervals
    silence_intervals = []
    if len(silence_frames) > 0:
        # Find silence frame boundaries
        silence_tags = np.zeros(frame_times.shape)
        silence_tags[silence_frames] = 1
        
        # Find silence interval boundary frames
        silence_edges = np.diff(np.concatenate([[0], silence_tags, [0]]))
        silence_starts = np.where(silence_edges == 1)[0]
        silence_ends = np.where(silence_edges == -1)[0]
        
        # Convert to time and filter out short silence segments
        for start, end in zip(silence_starts, silence_ends):
            duration = frame_times[end-1] - frame_times[start-1]
            if duration >= min_silence_duration:
                silence_intervals.append((frame_times[start-1], frame_times[end-1]))
    
    return silence_intervals

def get_active_segments(audio_duration, silence_intervals):
    """
    Calculate active segments based on silence intervals
    
    Parameters:
    - audio_duration: total audio duration (seconds)
    - silence_intervals: list of silence time intervals
    
    Returns:
    - active_intervals: list of active time intervals [(start_time, end_time), ...]
    """
    if not silence_intervals:
        return [(0, audio_duration)]
    
    active_intervals = []
    current_time = 0
    
    for start, end in sorted(silence_intervals):
        # If current time is less than silence start, add an active segment
        if current_time < start:
            active_intervals.append((current_time, start))
        current_time = end
    
    # Add the last active segment (if any)
    if current_time < audio_duration:
        active_intervals.append((current_time, audio_duration))
    
    return active_intervals

def analyze_audio_file(file_path, threshold_db=-40, min_silence_duration=4):
    """
    Analyze a single audio file
    
    Parameters:
    - file_path: audio file path
    - threshold_db: silence threshold (dB)
    - min_silence_duration: minimum silence duration (seconds)
    
    Returns:
    - audio_info: dictionary containing audio analysis results
    """
    print(f"Analyzing file: {os.path.basename(file_path)}")
    
    try:
        # Load audio file
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # Detect silence segments
        silence_intervals = detect_silence(y, sr, threshold_db, min_silence_duration)
        
        # Calculate active segments
        active_intervals = get_active_segments(duration, silence_intervals)
        
        # Calculate active time percentage
        total_silence_duration = sum(end - start for start, end in silence_intervals)
        total_active_duration = sum(end - start for start, end in active_intervals)
        active_percentage = (total_active_duration / duration) * 100 if duration > 0 else 0
        
        return {
            'file_name': os.path.basename(file_path),
            'duration': duration,
            'silence_intervals': silence_intervals,
            'active_intervals': active_intervals,
            'active_percentage': active_percentage,
            'total_active_duration': total_active_duration,
            'total_silence_duration': total_silence_duration
        }
    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return None

def generate_activity_chart(analysis_results, output_dir, bpm=None):
    """
    Generate audio activity charts
    
    Parameters:
    - analysis_results: list of audio analysis results
    - output_dir: output directory
    - bpm: beats per minute (if known)
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create DataFrame with all results
    results_df = pd.DataFrame([
        {
            'file_name': result['file_name'],
            'duration': result['duration'],
            'active_percentage': result['active_percentage'],
            'total_active_duration': result['total_active_duration'],
            'total_silence_duration': result['total_silence_duration']
        }
        for result in analysis_results if result is not None
    ])
    
    # Save analysis results as CSV
    results_df.to_csv(os.path.join(output_dir, 'audio_analysis_results.csv'), index=False)
    
    # Sort by active percentage
    results_df = results_df.sort_values('active_percentage', ascending=False)
    
    # Set global font size
    plt.rcParams['font.size'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    
    # Generate active percentage bar chart
    plt.figure(figsize=(12, 8))
    ax = plt.gca()  # Get current Axes object
    bars = ax.barh(results_df['file_name'], results_df['active_percentage'], color='skyblue')
    
    # Set color gradient
    norm = colors.Normalize(vmin=0, vmax=100)
    sm = cm.ScalarMappable(cmap=cm.viridis, norm=norm)
    sm.set_array([])
    
    for i, bar in enumerate(bars):
        bar.set_color(sm.to_rgba(results_df['active_percentage'].iloc[i]))
    
    plt.xlabel('Active Percentage (%)', fontsize=14)
    plt.ylabel('Audio Files', fontsize=14)
    plt.title('Audio File Activity Analysis', fontsize=18)
    plt.colorbar(sm, ax=ax, label='Active Percentage (%)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'audio_activity_percentage.png'), dpi=300)
    plt.close()
    
    # Generate timeline activity chart
    max_duration = max(result['duration'] for result in analysis_results if result is not None)
    
    plt.figure(figsize=(15, 10))
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), height_ratios=[1, 4], gridspec_kw={'hspace': 0.05})
    
    # Draw tempo changes in the first subplot
    # Define tempo change intervals
    tempo_changes = [
        (0, 52, 78),    # 0-52s: 78 BPM
        (52, 150, 120), # 52-150s: 120 BPM
        (150, max_duration, 100) # 150s to end: 100 BPM
    ]
    
    # Draw tempo changes
    for start, end, tempo in tempo_changes:
        # Draw different tempo region backgrounds
        alpha = 0.3
        if tempo == 78:
            color = 'lightblue'
        elif tempo == 120:
            color = 'lightgreen'
        else:
            color = 'lightsalmon'
            
        ax1.axvspan(start, end, alpha=alpha, color=color)
        
        # Add text labels
        mid_point = (start + end) / 2
        ax1.text(mid_point, 0.5, f"{tempo} BPM", ha='center', va='center', fontsize=14)
    
    # Set tempo chart Y-axis
    ax1.set_ylim(0, 1)
    ax1.set_yticks([])
    ax1.set_xlim(0, max_duration)
    ax1.set_title('Tempo Changes (BPM)', fontsize=16)
    
    # Remove X-axis ticks from tempo chart
    ax1.set_xticklabels([])
    
    # Define simple colors - all tracks blue
    simple_colors = ['#3393FF'] * 20  # Enough blue colors for all tracks
    
    # Track spacing
    track_height = 1.0
    y_positions = {}
    rect_height = 0.4  # Reduced rectangle height
    
    # Draw audio track activity in the second subplot
    for i, result in enumerate(sorted(analysis_results, key=lambda x: x['file_name'] if x else '')):
        if not result:
            continue
        
        file_name = result['file_name']
        y_pos = i * track_height
        y_positions[file_name] = y_pos
        
        # Get current track color - always blue
        track_color = '#3393FF'
        
        # Draw active segments
        for start, end in result['active_intervals']:
            ax2.fill_between([start, end], [y_pos, y_pos], [y_pos + rect_height, y_pos + rect_height], 
                             color=track_color, alpha=0.9)
    
    # Add vertical lines at tempo change points
    for start, _, _ in tempo_changes[1:]:  # Start from the second one
        ax1.axvline(x=start, color='red', linestyle='-', linewidth=1.5)
        ax2.axvline(x=start, color='red', linestyle='-', linewidth=1.5)
    
    # Set track chart Y-axis
    ax2.set_yticks(list(y_positions.values()))
    ax2.set_yticklabels(list(y_positions.keys()))
    ax2.set_xlabel('Time (seconds)', fontsize=14)
    ax2.set_ylabel('Audio Tracks', fontsize=14)
    ax2.set_xlim(0, max_duration)
    
    # Add title for the whole figure
    fig.suptitle('Audio Track Activity and Tempo Timeline', fontsize=18, y=0.98)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)  # Make space for title
    plt.savefig(os.path.join(output_dir, 'audio_activity_tempo_timeline.png'), dpi=300)
    plt.close()
    
    # Generate heatmap
    activity_matrix = np.zeros((len(results_df), int(max_duration * 10)))  # Sample every 0.1 second
    
    for i, result in enumerate(analysis_results):
        if not result:
            continue
            
        idx = results_df[results_df['file_name'] == result['file_name']].index[0]
        
        for start, end in result['active_intervals']:
            start_idx = int(start * 10)
            end_idx = min(int(end * 10), activity_matrix.shape[1])
            activity_matrix[idx, start_idx:end_idx] = 1
    
    plt.figure(figsize=(15, 10))
    ax = plt.gca()  # Get current Axes object
    im = plt.imshow(activity_matrix, aspect='auto', cmap='Blues', 
               extent=[0, max_duration, 0, len(results_df)], interpolation='nearest')
    plt.colorbar(im, ax=ax, label='Active State')
    plt.xlabel('Time (seconds)', fontsize=14)
    plt.ylabel('Audio Tracks', fontsize=14)
    plt.yticks(np.arange(len(results_df)) + 0.5, results_df['file_name'])
    plt.title('Audio Track Activity Heatmap', fontsize=18)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'audio_activity_heatmap.png'), dpi=300)
    plt.close()
    
    print(f"Analysis results and charts saved to directory: {output_dir}")

def main():
    # Set analysis parameters
    input_dir = "D:/audio_acessment/electronica/BenFlowers_Ecstasy_Full/BenFlowers_Ecstasy_Full"
    output_dir = "D:/audio_acessment/electronica/BenFlowers_Ecstasy_Full/analysis_results"
    threshold_db = -40  # Silence threshold (dB)
    min_silence_duration = 4  # Minimum silence duration (seconds)
    bpm = 186  # BPM value from Readme.txt
    
    print(f"Starting analysis of directory: {input_dir}")
    print(f"Silence threshold: {threshold_db}dB, Minimum silence duration: {min_silence_duration}s")
    
    # Get all WAV files
    audio_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.wav')]
    print(f"Found {len(audio_files)} audio files")
    
    # Analyze all audio files
    analysis_results = []
    for file_path in tqdm(audio_files, desc="Analyzing audio files"):
        result = analyze_audio_file(file_path, threshold_db, min_silence_duration)
        if result:
            analysis_results.append(result)
    
    # Generate activity charts
    generate_activity_chart(analysis_results, output_dir, bpm)

if __name__ == "__main__":
    main() 