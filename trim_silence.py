"""
This script trims leading and trailing silence from a .wav file.
"""

import re
import subprocess
from argparse import ArgumentParser, Namespace
from math import copysign
from pathlib import Path


OFFSET_DEFAULT = 0.4


def init_argument_parser() -> Namespace:
    """Initialize and return the command-line argument parser."""
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        'file',
        type=str,
        help="The .wav file to be trimmed."
    )
    parser.add_argument(
        '-t', '--threshold',
        type=float,
        default=-70.0,
        help=(
            "Silence threshold in dB (default: -70). "
            "Use a higher value (e.g. -50) if silences are louder."
        )
    )
    parser.add_argument(
        '-o', '--offset',
        type=float,
        default=OFFSET_DEFAULT,
        help=(
            f"Offset in seconds applied before start and after end of "
            f"non-silence (default: {OFFSET_DEFAULT})."
        )
    )
    parser.add_argument(
        '-x', '--execute',
        action='store_true',
        help="If set, write the trimmed file to disk."
    )
    parser.add_argument(
        '-n', '--normalize',
        action='store_true',
        help="If set, normalize the trimmed audio (only valid with --execute)."
    )

    return parser.parse_args()


def round_away_from_zero(value: float) -> int:
    """Round float away from zero to nearest integer."""
    return int(value + 0.5 * copysign(1, value))


def format_seconds(seconds: int) -> str:
    """Convert seconds to mm:ss format."""
    minutes = seconds // 60
    return f"{minutes:02}:{seconds % 60:02}"


def detect_trim_points(file: str, noise: float) -> tuple[float, float, float]:
    """
    Use ffmpeg to detect start and end points of audio by silence detection.

    Returns:
        (start_time, end_time, duration) in seconds
    """
    cmd = [
        "ffmpeg", "-i", file,
        "-af", f"silencedetect=noise={noise}dB",
        "-f", "null", "-"
    ]

    process = subprocess.run(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True
    )

    silence_starts = []
    silence_ends = []
    duration = 0.0

    for line in process.stderr.splitlines():
        if "Duration" in line:
            match = re.search(r"Duration: (\d+):(\d+):(\d+\.?\d*)", line)
            if match:
                h, m, s = map(float, match.groups())
                duration = h * 3600 + m * 60 + s
        if "silence_start" in line:
            match = re.search(r"silence_start: (\d+(\.\d+)?)", line)
            if match:
                silence_starts.append(float(match.group(1)))
        if "silence_end" in line:
            match = re.search(r"silence_end: (\d+(\.\d+)?)", line)
            if match:
                silence_ends.append(float(match.group(1)))

    start_time = silence_ends[0] if silence_ends else 0.0
    end_time = silence_starts[-1] if silence_starts else duration

    return start_time, end_time, duration


def trim_audio(file: str, start: float, end: float, output_file: str) -> None:
    """Trim the audio using sox from start to end."""
    duration = end - start
    cmd = [
        "sox", file, output_file,
        "trim", f"{start}", f"{duration}"
    ]
    print(f"Trimming to: {output_file}")
    subprocess.run(cmd)


def normalize_audio(file: str) -> None:
    """
    Normalize audio using sox after removing DC offset.
    Leaves 0.5 dB headroom to prevent dither clipping.
    """
    temp_file = Path(file).with_suffix(".normalized.wav")

    print(f"Removing DC offset and normalizing: {file}")
    subprocess.run([
        "sox", file, str(temp_file),
        "dcshift", "-0.0",
        "gain", "-n", "-0.5"
    ])

    temp_file.replace(file)


# ------------------- MAIN -------------------

args = init_argument_parser()

if not Path(args.file).exists():
    print(f'File "{args.file}" does not exist.')
    exit(1)

if args.threshold >= 0:
    print('Argument "threshold" must be < 0 dB.')
    exit(1)

start, end, duration = detect_trim_points(args.file, args.threshold)
start = max(0.0, start - args.offset)
end = min(duration, end + args.offset)

if end <= start:
    print("Trimmed duration would be 0 or negative. Exiting.")
    exit(1)

trimmed_duration = round_away_from_zero(end - start)
original_duration = round_away_from_zero(duration)

print(
    f"Original duration: {original_duration} seconds "
    f"({format_seconds(original_duration)})"
)
print(
    f"Expected trimmed duration: {trimmed_duration} seconds "
    f"({format_seconds(trimmed_duration)})"
)

if args.execute:
    output_path = Path(args.file).with_stem(
        Path(args.file).stem + "_trimmed"
    ).with_suffix(".wav")

    trim_audio(args.file, start, end, str(output_path))

    if args.normalize:
        normalize_audio(str(output_path))

else:
    print("Preview only — no files were written.")
    if args.normalize:
        print("Note: --normalize has no effect without --execute.")
