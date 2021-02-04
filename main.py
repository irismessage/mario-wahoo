#!usr/bin/env python

import os
import time
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

# to switch between concat demuxer and concat protocol change this and the concat func to use
audio_format = 'mpeg'

out_folder = Path().resolve().parent
out_video = out_folder / f'10hours.{audio_format}'
out_video_temp = out_video.with_stem(f'{out_video.stem}-temp')

# wew long name
out_video_target_duration_hours = 10
out_video_target_duration_seconds = out_video_target_duration_hours * (60 ** 2)
# out_video_target_duration_seconds = 30
# if avg clip is about 1 second then the tolerance in seconds will be about equal to this. 5 minutes or so is ok so 300
duration_check_interval = 300
clips_folder = out_folder / 'clips'
clips = [
    '(itsame)mario',
    'wa',
    'waha',
    'whoa',
    'wohoo',
    'woo',
    'ya',
    'yah',
    'yahh',
    'yahoo',
    'yippee',
]
clips = [f'{clip}.{audio_format}' for clip in clips]


def weighted_choice(choices, default_weight=100, banned=None):
    if banned is None:
        banned = []

    choices_processed = []
    for choice in choices:
        if choice not in banned:
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
        if stream.is_audio():
            seconds = stream.duration_seconds()
            print(f"Done {seconds} seconds, {time.strftime('%H:%M:%S', time.gmtime(seconds))}")
            return seconds >= duration_target


def concat_demuxer(clip_to_add):
    concat_input = out_folder / 'concat_input.txt'
    with open(out_folder / 'concat_input.txt', 'w') as concat_input_file:
        concat_input_file.write(f"file '{out_video}'\nfile '{clip_to_add}'\n")

    ffmpeg.input(str(concat_input), format='concat', safe=0).output(str(out_video_temp), c='copy')\
        .global_args('-hide_banner', '-loglevel', 'warning').run()


def concat_protocol(clip_to_add):
    ffmpeg.input(f'concat:{out_video}|{clip_to_add}').output(str(out_video_temp), c='copy')\
        .global_args('-hide_banner', '-loglevel', 'warning').run()


concat = concat_protocol


def add_clip(banned):
    no_dupe = [f'(itsame)mario.{audio_format}']

    clip_to_add_name = weighted_choice(clips, banned=banned)
    clip_to_add = clips_folder / clip_to_add_name
    if banned:
        banned = []
    if clip_to_add_name in no_dupe:
        banned.append(clip_to_add_name)

    if not out_video.is_file():
        ffmpeg.input(str(clip_to_add)).output(str(out_video)).run()
    else:
        concat(clip_to_add)
        os.remove(out_video)
        os.rename(out_video_temp, out_video)

    return banned


def main():
    banned = []
    while not over_duration_target():
        # for speed, only check duration every n additions
        for i in range(duration_check_interval):
            banned = add_clip(banned)


if __name__ == '__main__':
    main()
