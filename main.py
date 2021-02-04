#!usr/bin/env python

import os
import time
import json
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


def weighted_choice(choices, default_weight=1, banned=None):
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


def ffprobe_length_seconds(audio_path):
    metadata = ffprobe.FFProbe(str(audio_path))
    for stream in metadata.streams:
        if stream.is_audio():
            return stream.duration_seconds()


def over_duration_target(audio_path=out_video, duration_target=out_video_target_duration_seconds):
    if not out_video.is_file():
        return False

    seconds = ffprobe_length_seconds(audio_path)
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


def get_clip(banned):
    no_dupe = [f'(itsame)mario.{audio_format}']

    clip_to_add_name = weighted_choice(clips, banned=banned)
    clip_to_add = clips_folder / clip_to_add_name
    if banned:
        banned = []
    if clip_to_add_name in no_dupe:
        banned.append(clip_to_add_name)

    return clip_to_add, banned


def add_clip(banned):
    clip_to_add, banned = get_clip(banned)

    if not out_video.is_file():
        ffmpeg.input(str(clip_to_add)).output(str(out_video)).run()
    else:
        concat(clip_to_add)
        os.remove(out_video)
        os.rename(out_video_temp, out_video)

    return banned


def generate_list(clip_paths=None, duration_target=out_video_target_duration_seconds):
    if clip_paths is None:
        clip_paths = clips
    clip_paths = [clips_folder / clip_path for clip_path in clip_paths]

    print('Getting clip lengths with ffprobe')
    clip_lengths = {clip_path: ffprobe_length_seconds(clip_path) for clip_path in clip_paths}

    banned = []
    clip_plan = []

    # while the total length of all clips in the plan is less than the target length
    current_duration = 0
    while current_duration < duration_target:
        print(f"Done {current_duration} seconds, {time.strftime('%H:%M:%S', time.gmtime(current_duration))}")
        clip_to_add, banned = get_clip(banned)
        current_duration += clip_lengths[clip_to_add]
        clip_plan.append(str(clip_to_add))

    return clip_plan


def concat_protocol_many(clip_plan):
    concat_input = f"concat:{'|'.join(clip_plan)}"
    print(concat_input)
    ffmpeg.input(concat_input).output(str(out_video), c='copy').run()


def main():
    with open('clip_plan.txt', 'w') as concat_file:
        clip_plan = generate_list()
        concat_file.writelines([f"file '{clip_path}'\n" for clip_path in clip_plan])

    ffmpeg.input('clip_plan.txt', format='concat', safe=0).output(str(out_video), c='copy').run()


if __name__ == '__main__':
    main()
