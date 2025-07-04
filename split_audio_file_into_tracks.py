"""
This script splits an audio (.wav) file into tracks separated by silences.
"""

import re
import subprocess
from argparse import ArgumentParser, Namespace
from math import copysign
from pathlib import Path
from typing import List

OFFSET_DEFAULT = 0.4


def init_argument_parser() -> Namespace:
    """Initialize and return the command-line argument parser."""
    parser = ArgumentParser(description=__doc__)

    parser.add_argument(
        'file',
        type=str,
        help="The .wav file to be split."
    )
    parser.add_argument(
        'noise',
        type=float,
        help="Noise threshold in dB to detect silence (e.g., -50)."
    )
    parser.add_argument(
        'duration',
        type=float,
        help="Silence duration in seconds to detect (e.g., 1.5)."
    )
    parser.add_argument(
        '-o', '--offset',
        type=float,
        default=OFFSET_DEFAULT,
        help=(
            f"Offset in seconds before track start "
            f"(default: {OFFSET_DEFAULT})."
        )
    )
    parser.add_argument(
        '-x', '--execute',
        action='store_true',
        help="If set, write detected tracks to separate .wav files."
    )

    return parser.parse_args()


def fetch_silence_ends(
    file: str, noise: float, duration: float
) -> List[float]:
    """
    Run ffmpeg silence detection and return a list of silence_end timestamps.
    """
    cmd = [
        "ffmpeg", "-i", file,
        "-af", f"silencedetect=noise={noise}dB:d={duration}",
        "-f", "null", "-"
    ]

    process = subprocess.run(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True
    )

    silence_end_times = []
    for line in process.stderr.splitlines():
        match = re.search(r"silence_end: (\d+(\.\d+)?)", line)
        if match:
            silence_end_times.append(float(match.group(1)))

    return silence_end_times


def round_away_from_zero(value: float) -> int:
    """Round float away from zero to nearest integer."""
    return int(value + 0.5 * copysign(1, value))


def format_seconds(seconds: int) -> str:
    """Convert seconds to mm:ss format."""
    minutes = seconds // 60
    return f"{minutes:02}:{seconds % 60:02}"


def print_expected_tracks(silence_ends: List[float]) -> None:
    """
    Print the expected output track names and durations based on silence ends.
    """
    old_end = 0
    for number, end in enumerate(silence_ends, start=1):
        duration = round_away_from_zero(end - old_end)
        print(f"{number:02}.wav\t{format_seconds(duration)}")
        old_end = end


def write_tracks(
    file: str, silence_ends: List[float], offset: float
) -> None:
    """
    Write audio segments to separate files using sox.
    """
    old_end = 0
    for number, end in enumerate(silence_ends, start=1):
        end -= offset
        track_file = f"{number:02}.wav"
        args = ['sox', file, track_file, 'trim', str(old_end)]
        if number < len(silence_ends):
            args.append(f"={end}")
        print(f"Writing {track_file}")
        subprocess.run(args)
        old_end = end


# ------------------- MAIN -------------------

args = init_argument_parser()

if not Path(args.file).exists():
    print(f'File "{args.file}" does not exist.')
    exit(1)

if args.noise >= 0:
    print('Argument "noise" must be < 0 dB.')
    exit(1)

if args.duration <= 0:
    print('Argument "duration" must be > 0 seconds.')
    exit(1)

silence_ends = fetch_silence_ends(args.file, args.noise, args.duration)
print_expected_tracks(silence_ends)

if args.execute:
    write_tracks(args.file, silence_ends, args.offset)
