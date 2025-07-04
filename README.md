# Audio Processing Scripts

This repository contains two Python scripts for audio processing using `ffmpeg` and `sox`:

- **split_audio_file_into_tracks.py**: Splits a `.wav` audio file into multiple tracks by detecting silences.
- **trim_silence.py**: Trims leading and trailing silence from a `.wav` audio file, with optional normalization.

## Requirements

- Python 3
- `ffmpeg`
- `sox`

## split_audio_file_into_tracks.py

Splits an audio file into tracks separated by silences.

### Usage

```bash
python split_audio_file_into_tracks.py <file.wav> <noise_threshold_dB> <silence_duration_s> [options]
```

### Arguments
- `file`: Path to the `.wav` file to split.
- `noise`: Noise threshold in dB to detect silence (e.g., `-50`).
- `duration`: Minimum silence duration in seconds to detect (e.g., `1.5`).

### Options
- `-o`, `--offset`: Offset in seconds before each track start (default: `0.4`).
- `-x`, `--execute`: Write detected tracks to separate `.wav` files.

## trim_silence.py

Trims leading and trailing silence from a `.wav` file, with optional normalization.

### Usage

```bash
python trim_silence.py <file.wav> [options]
```

### Options
- `-t`, `--threshold`: Silence threshold in dB (default: `-70`). Use a higher value (e.g., `-50`) if silences are louder.
- `-o`, `--offset`: Offset in seconds applied before start and after end of non-silence (default: `0.4`).
- `-x`, `--execute`: Write the trimmed file to disk.
- `-n`, `--normalize`: Normalize the trimmed audio (only valid with `--execute`).

## Notes

- Both scripts require `ffmpeg` and `sox` installed and accessible in your system PATH.
- Use the `--execute` flag to perform actual file writing; otherwise, scripts run in preview mode.

## License

[MIT](LICENSE)

