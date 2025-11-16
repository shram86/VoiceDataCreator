# Dataset Creator for TTS Training

A Python tool for creating text-to-speech (TTS) training datasets by recording audio for text phrases. This tool provides an interactive command-line interface for recording audio samples with automatic silence removal, audio validation, and progress tracking.

## Features

- 🎤 **High-quality audio recording** using `sounddevice` (22.05 kHz sample rate)
- 📝 **Flexible input formats** - supports both `wavfile|text` and plain text formats
- ✂️ **Automatic silence removal** with fade in/out to prevent clicks
- ✅ **Audio validation** - automatic testing of recorded audio quality
- 📊 **Progress tracking** - real-time display of recording progress
- 💾 **Auto-save** - saves progress on interruption (Ctrl+C)
- 🔄 **Re-record option** - easily re-record any phrase
- ⏭️ **Skip phrases** - skip unwanted phrases without recording
- 🚪 **Escape mode** - save current recording and exit gracefully
- 🎯 **Random filenames** - generates unique 8-character filenames for audio files

## Requirements

### Python Dependencies

- Python 3.6+
- `librosa` - Audio processing
- `soundfile` - Audio file I/O
- `sounddevice` - Audio recording
- `numpy` - Numerical operations

### System Requirements

- A working microphone/audio input device
- Terminal/command-line interface
- Sufficient disk space for audio files

## Installation

1. Install the required Python packages:

```bash
pip install librosa soundfile sounddevice numpy
```

2. Make the script executable (optional):

```bash
chmod +x dataset_creator_final.py
```

## Configuration

Edit the `CONFIG` dictionary in the `main()` function to set your paths:

```python
CONFIG = {
    'input_text': 't1.txt',      # Input text file
    'output_text': 't.txt',      # Output dataset file
    'wave_path': 'audio/',       # Directory to save WAV files
}
```

## Usage

### Basic Usage

```bash
python dataset_creator_final.py
```

Or if made executable:

```bash
./dataset_creator_final.py
```

### Workflow

1. **Prepare input file**: Create a text file with phrases to record (see Input Formats below)
2. **Run the script**: Execute `dataset_creator_final.py`
3. **Record phrases**: For each phrase:
   - Press **Enter** to start recording
   - Speak the phrase
   - Press **Enter** to stop recording
   - Choose an action (see Recording Controls below)
4. **Review output**: The tool automatically validates audio and saves the dataset

## Input File Formats

The tool automatically detects and supports two input formats:

### Format 1: Plain Text (one phrase per line)

```
Hello world
This is a test
How are you today?
```

### Format 2: wavfile|text Format

```
dummy.wav|Hello world
dummy.wav|This is a test
dummy.wav|How are you today?
```

**Note**: In `wavfile|text` format, the tool extracts only the text portion (after the `|`). The wavfile name before `|` is ignored but can be useful for reference.

## Output Format

The output dataset file contains one entry per line in the format:

```
audio/abc12345.wav|Hello world
audio/def67890.wav|This is a test
audio/ghi11111.wav|How are you today?
```

Where:
- `audio/` is the wave_path directory
- `abc12345.wav` is a randomly generated 8-character filename
- `|` separates the audio file path from the text
- The text is the original phrase

## Recording Controls

After recording a phrase, you'll be prompted with these options:

- **`y`** or **`yes`** - Save this recording and move to next phrase
- **`n`** or **`no`** - Record again (re-record the same phrase)
- **`s`** or **`skip`** - Skip this phrase (don't save, move to next)
- **`e`** or **`escape`** - Save current recording and exit (saves all progress)

### Keyboard Interrupt

Press **Ctrl+C** at any time to:
- Save all recorded files to the output dataset
- Exit gracefully
- Preserve all progress made so far

## Audio Processing

### Automatic Features

1. **Silence Removal**: Automatically trims silence from the beginning and end of recordings
   - Threshold: 0.005 (configurable)
   - Padding: 50ms before/after detected audio
   
2. **Click Prevention**: Applies fade in/out (10ms) to prevent audio clicks

3. **Format Standardization**: 
   - Sample rate: 22.05 kHz
   - Format: WAV (PCM_16)
   - Channels: Mono

### Audio Validation

After recording, the tool automatically:
- Checks recording duration
- Validates audio amplitude
- Detects potential clipping
- Measures energy levels
- Warns about very short/long recordings

## Example Session

```
🎯 Final Dataset Creator for TTS Training
==================================================
Input file: t1.txt
Output file: t.txt
Audio directory: audio/
==================================================

📝 Detected format: plain text (one per line)
📊 Loaded 3 phrases from plain_text format

📝 Progress: 1/3 | 🎵 Saved WAVs: 0

============================================================
Hello world
============================================================
Press Enter to start recording...
🎤 Recording... Press Enter to stop.
(Recording...)
Press Enter to stop recording...
✅ Recording completed successfully
⏱️  Recording duration: 2.34 seconds

Options:
  y - Save this recording
  n - Record again
  s - Skip this text (don't save, move to next)
  e - Escape (save all data and exit)

What would you like to do? (y/n/s/e): y
✅ Saved as: abc12345.wav (2.34s)
✅ Added to dataset: abc12345.wav
   Total recorded so far: 1
```

## File Structure

After running the tool, you'll have:

```
project/
├── dataset_creator_final.py
├── t1.txt                    # Input file
├── t.txt                     # Output dataset file
└── audio/                    # Audio files directory
    ├── abc12345.wav
    ├── def67890.wav
    └── ...
```

## Troubleshooting

### No Audio Recorded

- **Check microphone permissions**: Ensure your system allows microphone access
- **Check audio device**: Verify your microphone is connected and working
- **Test with system audio tools**: Try recording with other applications first

### Audio Quality Issues

- **Low volume**: Check microphone input levels in system settings
- **Clipping detected**: Reduce microphone input gain
- **Very short duration**: Ensure you're speaking clearly and loudly enough

### File Not Found Errors

- **Input file**: Ensure `t1.txt` (or your configured input file) exists
- **Output directory**: The tool creates `audio/` automatically, but ensure write permissions

### Import Errors

If you get import errors, install missing packages:

```bash
pip install librosa soundfile sounddevice numpy
```

## Technical Details

- **Sample Rate**: 22.05 kHz (configurable in `FinalAudioRecorder.__init__`)
- **Audio Format**: WAV, PCM_16, Mono
- **Silence Threshold**: 0.005 (configurable in `remove_silence()`)
- **Fade Duration**: 10ms
- **Padding**: 50ms before/after detected audio

## License

This tool is part of the shramVoice project. Modify and use as needed for your TTS training workflow.

## Contributing

To modify the tool:
- Edit the `CONFIG` dictionary in `main()` for paths
- Adjust `sample_rate` in `FinalAudioRecorder.__init__()` for different sample rates
- Modify `remove_silence()` threshold for different silence detection sensitivity

