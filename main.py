#!usr/bin/env python

import os
import random
from pathlib import Path

import ffmpeg
import ffprobe


# file structure this program uses:
# mario/
#   out_video
#   clips/
#     clips go here
#   mario-code/
#     main.py

# todo: auto check duration of current working video
iterations = 10
out_folder = Path().resolve().parent
out_video = out_folder / '10hours.wav'
# wew long name
out_video_target_duration_hours = 10
out_video_target_duration_seconds = out_video_target_duration_hours * (60 ** 2)
clips_folder = out_folder / 'clips'
clips = [
    '(itsame)mario.wav',
    'wa.wav',
    'waha.wav',
    'whoa.wav',
    'wohoo.wav',
    'woo.wav',
    'ya.wav',
    'yah.wav',
    'yahh.wav',
    'yahoo.wav',
    'yippee.wav',
]


def weighted_choice(choices, default_weight=100):
    choices_processed = []
    for choice in choices:
        if not isinstance(choice, tuple):
            choices_processed += [choice] * default_weight
        else:
            choices_processed += [choice[0]] * choice[1]

    return random.choice(choices_processed)


def over_duration_target(video_path=out_video, duration_target=out_video_target_duration_seconds):
    if not out_video.is_file():
        return False

    metadata = ffprobe.FFProbe(str(video_path))
    for stream in metadata.streams:
        if stream.is_video():
            return stream.duration_seconds() >= duration_target


def add_clip():
    clip_to_add = clips_folder / weighted_choice(clips)

    if not out_video.is_file():
        ffmpeg.input(str(clip_to_add)).output(str(out_video)).run()
    else:
        concat_input = out_folder / 'concat_input.txt'
        with open(out_folder / 'concat_input.txt', 'w') as concat_input_file:
            concat_input_file.write(f"file '{out_video}'\nfile '{clip_to_add}'\n")
        out_video_temp = out_video.with_stem(f'{out_video.stem}-temp')

        ffmpeg.input(str(concat_input), format='concat', safe=0).output(str(out_video_temp)).run()
        os.remove(out_video)
        os.rename(out_video_temp, out_video)


def main():
    # for i in range(iterations):
    while not over_duration_target():
        add_clip()


if __name__ == '__main__':
    main()
