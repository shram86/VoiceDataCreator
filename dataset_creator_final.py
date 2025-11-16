#!/usr/bin/env python3
"""
Final Dataset Creator for TTS Training
Uses only system commands and basic Python libraries.
"""

import os
import subprocess
import time
import random
import string
import librosa
import soundfile as sf
from pathlib import Path
import numpy as np
from typing import List, Optional
import sounddevice as sd

class FinalAudioRecorder:
    """Audio recorder using sounddevice for high quality recording."""
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate

    def record_audio(self) -> str:
        """Record audio using Enter key to start/stop (modern, high quality)."""
        temp_filename = f"temp_recording_{np.random.randint(1000, 9999)}.wav"
        print("Press Enter to start recording...")
        input()
        print("🎤 Recording... Press Enter to stop.")
        print("(Recording...)")
        print("Press Enter to stop recording...")
        recording = []
        is_recording = [False]  # Start as False to avoid capturing the Enter key press

        def callback(indata, frames, time, status):
            if is_recording[0]:
                recording.append(indata.copy())

        with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=callback):
            # Add a small delay to avoid capturing the Enter key press
            time.sleep(0.3)
            is_recording[0] = True
            
            # Wait for user to press Enter to stop
            input()
            is_recording[0] = False
            
            # Add a small delay to avoid capturing the Enter key press
            time.sleep(0.2)

        if not recording:
            print("❌ No audio recorded")
            return None
            
        audio = np.concatenate(recording, axis=0)
        sf.write(temp_filename, audio, self.sample_rate)
        print("✅ Recording completed successfully")
        return temp_filename

    def cleanup_temp_file(self, temp_file):
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

class FinalDatasetCreator:
    """Final dataset creation application."""
    
    def __init__(self, input_text_path: str, output_text_path: str, wave_path: str):
        self.input_text_path = input_text_path
        self.output_text_path = output_text_path
        self.wave_path = Path(wave_path)
        self.wave_path.mkdir(exist_ok=True)
        self.recorder = FinalAudioRecorder()
        self.phrases = []
        self.recorded_files = []
        
    def load_phrases(self) -> List[str]:
        """Load phrases from input text file. Supports both formats:
        1. wavfile|text format (e.g., dummy.wav|Hello world)
        2. plain text format (one text per line)
        """
        try:
            with open(self.input_text_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            phrases = []
            format_detected = None
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                # Auto-detect format on first non-empty line
                if format_detected is None:
                    if '|' in line:
                        format_detected = 'wavfile|text'
                        print(f"📝 Detected format: wavfile|text")
                    else:
                        format_detected = 'plain_text'
                        print(f"📝 Detected format: plain text (one per line)")
                
                # Parse based on detected format
                if format_detected == 'wavfile|text':
                    if '|' in line:
                        # Extract text part (after |)
                        text = line.split('|', 1)[1].strip()
                    else:
                        # Fallback: treat as plain text if no | found
                        text = line
                else:  # plain_text format
                    text = line
                
                if text:  # Only add non-empty phrases
                    phrases.append(text)
                    
            print(f"📊 Loaded {len(phrases)} phrases from {format_detected} format")
            return phrases
            
        except FileNotFoundError:
            print(f"Error: Input text file '{self.input_text_path}' not found.")
            return []
        except Exception as e:
            print(f"Error loading phrases: {e}")
            return []
    
    def generate_filename(self) -> str:
        """Generate a random filename for the audio file."""
        # Generate 8-character random string
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{random_str}.wav"
    
    def remove_silence(self, audio: np.ndarray, threshold=0.005) -> np.ndarray:
        """Remove silence from the beginning and end of audio with improved click removal."""
        if len(audio) == 0:
            return audio
            
        # Find non-silent regions with a more sensitive threshold
        energy = np.abs(audio)
        silent_mask = energy < threshold
        
        # Find first non-silent sample
        start_idx = 0
        for i, silent in enumerate(silent_mask):
            if not silent:
                start_idx = i
                break
        
        # Find last non-silent sample
        end_idx = len(audio)
        for i in range(len(silent_mask) - 1, -1, -1):
            if not silent_mask[i]:
                end_idx = i + 1
                break
        
        # Add some padding to avoid cutting too close to the actual audio
        start_idx = max(0, start_idx - int(0.05 * self.recorder.sample_rate))  # 50ms padding
        end_idx = min(len(audio), end_idx + int(0.05 * self.recorder.sample_rate))  # 50ms padding
        
        trimmed_audio = audio[start_idx:end_idx]
        
        # Apply fade in/out to smooth any remaining clicks
        if len(trimmed_audio) > 0:
            fade_samples = int(0.01 * self.recorder.sample_rate)  # 10ms fade
            if len(trimmed_audio) > 2 * fade_samples:
                # Fade in
                fade_in = np.linspace(0, 1, fade_samples)
                trimmed_audio[:fade_samples] *= fade_in
                
                # Fade out
                fade_out = np.linspace(1, 0, fade_samples)
                trimmed_audio[-fade_samples:] *= fade_out
        
        return trimmed_audio
    
    def save_audio(self, temp_file: str, filename: str) -> str:
        """Save audio to file with proper format."""
        filepath = self.wave_path / filename
        
        try:
            # Load the temporary recording
            audio, sr = librosa.load(temp_file, sr=self.recorder.sample_rate)
            
            # Remove silence
            audio_trimmed = self.remove_silence(audio)
            
            if len(audio_trimmed) == 0:
                raise ValueError("Audio is empty after silence removal")
            
            # Save as WAV file
            sf.write(str(filepath), audio_trimmed, self.recorder.sample_rate, subtype='PCM_16')
            
            return str(filepath)
        except Exception as e:
            print(f"❌ Error processing audio: {e}")
            return None
    
    def record_phrase(self, phrase: str) -> Optional[str]:
        """Record a single phrase with user interaction."""
        while True:
            # Display the phrase each time (including when recording again)
            print(f"\n{'='*60}")
            print(f"\033[38;2;122;250;79m{phrase}\033[0m")  # RGB(122,250,79) - bright green
            print(f"{'='*60}")
            
            # Record audio using Enter key
            temp_file = self.recorder.record_audio()
            
            if not temp_file:
                print("❌ Recording failed. Try again? (y/n): ", end="")
                if input().lower().strip() in ['y', 'yes']:
                    continue
                else:
                    return None
            
            # Get duration of the recording
            try:
                audio, sr = librosa.load(temp_file, sr=self.recorder.sample_rate)
                duration = len(audio) / sr
                print(f"⏱️  Recording duration: {duration:.2f} seconds")
            except Exception as e:
                print(f"⚠️  Could not determine duration: {e}")
                duration = 0
            
            # Ask user if they want to save
            while True:
                print("\nOptions:")
                print("  y - Save this recording")
                print("  n - Record again")
                print("  s - Skip this text (don't save, move to next)")
                print("  e - Escape (save all data and exit)")
                
                try:
                    response = input("\nWhat would you like to do? (y/n/s/e): ").lower().strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n⚠️  Input interrupted. Skipping this recording...")
                    self.recorder.cleanup_temp_file(temp_file)
                    return None
                
                if response in ['y', 'yes']:
                    # Generate filename and save
                    filename = self.generate_filename()
                    filepath = self.save_audio(temp_file, filename)
                    
                    # Clean up temp file
                    self.recorder.cleanup_temp_file(temp_file)
                    
                    if filepath:
                        print(f"✅ Saved as: {filename} ({duration:.2f}s)")
                        return filepath
                    else:
                        print("❌ Error saving audio. Try again? (y/n): ", end="")
                        try:
                            if input().lower().strip() in ['y', 'yes']:
                                continue
                            else:
                                return None
                        except (EOFError, KeyboardInterrupt):
                            print("\n⚠️  Input interrupted. Skipping...")
                            return None
                elif response in ['n', 'no']:
                    # Clean up temp file and continue the outer loop to record again
                    self.recorder.cleanup_temp_file(temp_file)
                    print("🔄 Recording again...")
                    break  # This breaks the inner while loop and continues the outer loop
                elif response in ['s', 'skip']:
                    # Skip this text - clean up temp file and return None
                    self.recorder.cleanup_temp_file(temp_file)
                    print("⏭️  Skipping this text...")
                    return None
                elif response in ['e', 'escape']:
                    # Escape - save current recording first, then exit
                    print("🚪 Escaping - saving current recording and exiting...")
                    
                    # Generate filename and save current recording
                    filename = self.generate_filename()
                    filepath = self.save_audio(temp_file, filename)
                    
                    # Clean up temp file
                    self.recorder.cleanup_temp_file(temp_file)
                    
                    if filepath:
                        print(f"✅ Saved current recording as: {filename} ({duration:.2f}s)")
                        return ("ESCAPE", filepath)  # Return tuple indicating escape with saved file
                    else:
                        print("❌ Error saving current recording, but continuing with escape...")
                        return "ESCAPE"
                else:
                    print("Please enter 'y', 'n', 's', or 'e'.")
    
    def create_dataset(self):
        """Main dataset creation loop."""
        print("\033[1;34m🎯 Final Dataset Creator for TTS Training\033[0m")  # Blue, bold
        print("\033[1;34m" + "=" * 50 + "\033[0m")
        
        # Load phrases
        print(f"\033[1;37mLoading phrases from: {self.input_text_path}\033[0m")  # White, bold
        self.phrases = self.load_phrases()
        print(f"\033[1;37mLoaded {len(self.phrases)} phrases\033[0m")
        
        if not self.phrases:
            print("\033[1;31m❌ No phrases found in input file.\033[0m")
            return
        
        # Recording loop
        try:
            for i, phrase in enumerate(self.phrases, 1):
                print(f"\n\033[1;33m📝 Progress: {i}/{len(self.phrases)} | 🎵 Saved WAVs: {len(self.recorded_files)}\033[0m")  # Yellow, bold
                
                # Record the phrase
                audio_file = self.record_phrase(phrase)
                
                # Check for escape signal
                if audio_file == "ESCAPE":
                    print(f"\n\033[1;35m📊 Recording stopped by user. Total files recorded: {len(self.recorded_files)}\033[0m")  # Magenta, bold
                    break
                elif isinstance(audio_file, tuple) and audio_file[0] == "ESCAPE":
                    # Escape with saved file - add the file to dataset then exit
                    saved_file = audio_file[1]
                    self.recorded_files.append((saved_file, phrase))
                    print(f"\033[1;32m✅ Added to dataset: {os.path.basename(saved_file)}\033[0m")  # Green, bold
                    print(f"   Total recorded so far: {len(self.recorded_files)}")
                    print(f"\n\033[1;35m📊 Recording stopped by user. Total files recorded: {len(self.recorded_files)}\033[0m")  # Magenta, bold
                    break
                elif audio_file:
                    self.recorded_files.append((audio_file, phrase))
                    print(f"\033[1;32m✅ Added to dataset: {os.path.basename(audio_file)}\033[0m")  # Green, bold
                    print(f"   Total recorded so far: {len(self.recorded_files)}")
                else:
                    print(f"\033[1;31m❌ Skipped or failed to record phrase\033[0m")  # Red, bold
                    print(f"   Total recorded so far: {len(self.recorded_files)}")
        except KeyboardInterrupt:
            print(f"\n\n⏹️  Recording interrupted by user (Ctrl+C).")
            print(f"📊 Total files recorded so far: {len(self.recorded_files)}")
            if len(self.recorded_files) > 0:
                print("💾 Saving current progress...")
                self.save_output_dataset()
                print("✅ Progress saved successfully!")
            return
        
        print(f"\n\033[1;35m📊 Recording complete. Total files recorded: {len(self.recorded_files)}\033[0m")  # Magenta, bold
        
        # Save output dataset
        self.save_output_dataset()
        
        # Check alignment
        self.check_alignment()
        
        print(f"\n\033[1;32m🎉 Dataset creation complete!\033[0m")  # Green, bold
        print(f"\033[1;37m📁 Output saved to: {self.output_text_path}\033[0m")  # White, bold
        print(f"\033[1;37m🎵 Audio files saved to: {self.wave_path}\033[0m")  # White, bold
        
        # Automatically run audio test
        self.run_audio_test()
    
    def run_audio_test(self):
        """Run audio test on the created dataset."""
        print(f"\n🔍 Running audio test on created dataset...")
        
        if not self.recorded_files:
            print("❌ No files to test.")
            return
        
        try:
            # Import test_audio functionality
            import subprocess
            import sys
            
            print("🎵 Testing audio files...")
            
            # Test each recorded file
            for i, (audio_file, phrase) in enumerate(self.recorded_files, 1):
                print(f"\n📝 Testing file {i}/{len(self.recorded_files)}: {os.path.basename(audio_file)}")
                print(f"   Phrase: {phrase}")
                
                try:
                    # Load and analyze audio
                    audio, sr = librosa.load(audio_file, sr=22050)
                    duration = len(audio) / sr
                    max_amplitude = np.max(np.abs(audio))
                    
                    print(f"   ✅ Duration: {duration:.2f}s")
                    print(f"   ✅ Max amplitude: {max_amplitude:.4f}")
                    
                    # Check for potential issues
                    if duration < 0.5:
                        print(f"   ⚠️  Very short duration")
                    elif duration > 10.0:
                        print(f"   ⚠️  Very long duration")
                    
                    if max_amplitude < 0.01:
                        print(f"   ⚠️  Very low volume")
                    elif max_amplitude > 0.95:
                        print(f"   ⚠️  Possible clipping")
                    
                    # Check for silence
                    energy = np.mean(np.abs(audio))
                    if energy < 0.001:
                        print(f"   ❌ Very low energy - possible silence")
                    else:
                        print(f"   ✅ Good energy level: {energy:.4f}")
                        
                except Exception as e:
                    print(f"   ❌ Error testing file: {e}")
            
            print(f"\n🎉 Audio test completed!")
            print(f"   Total files tested: {len(self.recorded_files)}")
            
        except Exception as e:
            print(f"❌ Error running audio test: {e}")
    
    def save_output_dataset(self):
        """Save the final dataset to output file."""
        try:
            print(f"\n💾 Saving dataset with {len(self.recorded_files)} files...")
            
            with open(self.output_text_path, 'w', encoding='utf-8') as f:
                for audio_file, phrase in self.recorded_files:
                    f.write(f"{audio_file}|{phrase}\n")
                    print(f"   Added: {audio_file}|{phrase}")
            
            print(f"✅ Dataset saved to: {self.output_text_path}")
            
            # Also create an empty file if no recordings were made
            if len(self.recorded_files) == 0:
                print("⚠️  No recordings were saved. Creating empty dataset file.")
                with open(self.output_text_path, 'w', encoding='utf-8') as f:
                    f.write("# Empty dataset - no recordings were saved\n")
                print(f"✅ Empty dataset file created: {self.output_text_path}")
                
        except Exception as e:
            print(f"❌ Error saving dataset: {e}")
            print(f"   Attempted to save to: {self.output_text_path}")
            print(f"   Number of recorded files: {len(self.recorded_files)}")
    
    def check_alignment(self):
        """Check alignment of created dataset."""
        print("\n🔍 Checking dataset alignment...")
        
        if not self.recorded_files:
            print("❌ No files to check.")
            return
        
        total_duration = 0
        valid_files = 0
        
        for audio_file, phrase in self.recorded_files:
            try:
                # Load audio and get duration
                audio, sr = librosa.load(audio_file, sr=22050)
                duration = len(audio) / sr
                total_duration += duration
                valid_files += 1
                
                # Check if audio is too short or too long
                if duration < 0.5:
                    print(f"⚠️  {os.path.basename(audio_file)}: Very short ({duration:.2f}s)")
                elif duration > 10.0:
                    print(f"⚠️  {os.path.basename(audio_file)}: Very long ({duration:.2f}s)")
                else:
                    print(f"✅ {os.path.basename(audio_file)}: {duration:.2f}s")
                    
            except Exception as e:
                print(f"❌ Error checking {audio_file}: {e}")
        
        if valid_files > 0:
            avg_duration = total_duration / valid_files
            print(f"\n📊 Dataset Statistics:")
            print(f"   Total files: {valid_files}")
            print(f"   Total duration: {total_duration:.2f}s")
            print(f"   Average duration: {avg_duration:.2f}s")
        else:
            print("❌ No valid files found.")

def main():
    """Main entry point."""
    # Configuration - modify these paths as needed
    CONFIG = {
        'input_text': 't1.txt',      # Input text file (wavfile|text format or plain text)
        'output_text': 't.txt',            # Output dataset file
        'wave_path': 'audio/',                     # Directory to save WAV files
    }
    
    print("🎯 Final Dataset Creator for TTS Training")
    print("=" * 50)
    print(f"Input file: {CONFIG['input_text']}")
    print(f"Output file: {CONFIG['output_text']}")
    print(f"Audio directory: {CONFIG['wave_path']}")
    print("=" * 50)
    
    # Create dataset creator
    creator = FinalDatasetCreator(CONFIG['input_text'], CONFIG['output_text'], CONFIG['wave_path'])
    
    try:
        # Start dataset creation
        creator.create_dataset()
    except KeyboardInterrupt:
        print("\n\n⏹️  Recording interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 
