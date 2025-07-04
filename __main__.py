"""
This script can split an audio (.wav) file into tracks that are separated by silences between them.
"""

import subprocess
from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import List
from math import copysign

OFFSET_DEFAULT = 0.4


def init_argument_parser() -> Namespace:
    parser = ArgumentParser(description=__doc__)

    # mandatory:
    parser.add_argument('file', type=str,
                        help="the .wav file that is to be split")
    # mandatory:
    parser.add_argument('noise', type=float,
                        help="the noise measured in decibel that is to be regarded as silence (e.g. -50)")
    # mandatory:
    parser.add_argument('duration', type=float,
                        help="the silence duration in seconds that should be detected (e.g. 1.5)")
    # optional:
    parser.add_argument('-o', '--offset', type=float, default=OFFSET_DEFAULT,
                        help=f'the offset in seconds before a track starts'
                             f' (if not specified, the default value {OFFSET_DEFAULT} will be taken!)')
    # optional flag:
    parser.add_argument('-x', '--execute', action='store_true',
                        help='if set, the detected audio tracks will be written into current working directory')
    return parser.parse_args()


def fetch_silence_ends(file, noise, duration) -> List[float]:
    # e.g.
    # ffmpeg -i recording.wav -af silencedetect=noise=-45dB:d=1.5 -f null - 2> >(grep 'silence_end') | awk '{print $5}'
    #
    p1 = subprocess.Popen(
        ["ffmpeg", "-i", f"{file}", "-af", f"silencedetect=noise={noise}dB:d={duration}",
         "-f", "null", "-"], stderr=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "silence_end"], stdin=p1.stderr, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["awk", "{print $5}"], stdin=p2.stdout, stdout=subprocess.PIPE)

    # stdout_result is of type 'bytes'  e.g.  b'540.132\n947.927\n1300.19\n1627.23\n2018.4\n2647.47\n2842\n'
    stdout_result = p3.communicate()[0]
    split_mark = bytes(b'\n')
    return [float(b) for b in stdout_result.split(split_mark) if b != b'']


def round_away_from_zero(f: float) -> int:
    return int(f + 0.5 * copysign(1, f))


def format_seconds(seconds: int) -> str:
    minutes = seconds / 60
    return '%.02d:%.02d' % (minutes, seconds % 60)


def print_expected_tracks():
    old_silence_end = 0
    for number, silence_end in enumerate(silence_ends, start=1):
        track_duration_in_seconds = round_away_from_zero(silence_end - old_silence_end)
        print('%.02d.wav' % number, '\t', format_seconds(track_duration_in_seconds))
        old_silence_end = silence_end


def write_tracks(file, offset):
    number_of_tracks = len(silence_ends)
    old_silence_end = 0
    for number, silence_end in enumerate(silence_ends, start=1):
        silence_end -= offset
        track = '%.02d.wav' % number
        subprocess_args = ['sox', file, track, 'trim', str(old_silence_end)]
        if number < number_of_tracks:
            subprocess_args.append(f'={silence_end}')
        print(f'Writing {track}')
        # e.g.  sox recording.wav 01.wav trim 0 =539.832
        #       sox recording.wav 02.wav trim 539.832 =947.627
        #       sox recording.wav 03.wav trim 947.627
        subprocess.run(subprocess_args)
        old_silence_end = silence_end


############## START ##############

args = init_argument_parser()
# print(args)

if not Path(args.file).exists():
    print(f'File "{args.file}" does not exist')
    exit(1)
if not args.noise < 0:
    print('Argument "noise" must be <0')
    exit(1)
if not args.duration > 0:
    print('Argument "duration" must be >0')
    exit(1)

silence_ends = fetch_silence_ends(args.file, args.noise, args.duration)
print_expected_tracks()
if args.execute:
    write_tracks(args.file, args.offset)
