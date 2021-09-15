# __main__.py

import subprocess
from argparse import Namespace, ArgumentParser


offset_default = 0.3
tracks_file_name = 'tracks.txt'


def init_argument_parser() -> Namespace:
    parser = ArgumentParser(description=__doc__)

    # mandatory:
    parser.add_argument('file', type=str,
                        help="The .wav file that is to be split")
    # mandatory:
    parser.add_argument('noise', type=float,
                        help="The noise measured in decibel that is to be regarded as silence (e.g. -50)")
    # mandatory:
    parser.add_argument('duration', type=float,
                        help="The silence duration in seconds that should be detected (e.g. 1.5)")
    # optional:
    parser.add_argument('-o', '--offset', type=float, default=offset_default,
                        help=f'The offset in seconds before a track starts'
                             f' (if not specified, the default value {offset_default} will be taken!)')
    # optional flag:
    parser.add_argument('-x', '--execute', action='store_true',
                        help='If set, the detected audio tracks will be written into current working directory')
    return parser.parse_args()


args = init_argument_parser()
print(args)

if not args.duration > 0:
    print('duration must be >0')
    exit()

p1 = subprocess.Popen(["ffmpeg", "-i", f"{args.file}", "-af", f"silencedetect=noise={args.noise}dB:d={args.duration}", "-f", "null", "-"], stderr=subprocess.PIPE)
p2 = subprocess.Popen(["grep", "silence_end"], stdin=p1.stderr, stdout=subprocess.PIPE)
with open(tracks_file_name, 'w') as tracks_file:
    p3 = subprocess.Popen(["awk", "{print $5}"], stdin=p2.stdout, stdout=tracks_file)
    p3.communicate()

subprocess.run(['cat', tracks_file_name])



