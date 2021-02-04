#!usr/bin/env python

import time
import random
from pathlib import Path

import ffmpeg
import ffprobe


audio_format = 'mp3'


clips_folder = Path() / 'clips'
out_video_path = clips_folder / f'_10hours.{audio_format}'
clip_plan_path = clips_folder / '_clip_plan.txt'

# wew long name
out_video_target_duration_hours = 10
out_video_target_duration_seconds = out_video_target_duration_hours * (60 ** 2)

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


def get_clip(banned):
    no_dupe = [f'(itsame)mario.{audio_format}']

    clip_to_add_name = weighted_choice(clips, banned=banned)
    clip_to_add = clips_folder / clip_to_add_name
    if banned:
        banned = []
    if clip_to_add_name in no_dupe:
        banned.append(clip_to_add_name)

    return clip_to_add, banned


def generate_list(clip_paths=None, duration_target=out_video_target_duration_seconds):
    if clip_paths is None:
        clip_paths = clips
    clip_paths = [clips_folder / clip_path for clip_path in clip_paths]

    print('Generating randomised list')
    print('Getting clip lengths with ffprobe')
    clip_lengths = {}
    for clip_path in clip_paths:
        clip_length = ffprobe_length_seconds(clip_path)
        clip_lengths[clip_path] = clip_length

        print(f'{clip_path}: {clip_length}s')

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


def main():
    if not clip_plan_path.is_file():
        with open(clip_plan_path, 'w') as clip_plan_file:
            clip_plan = generate_list()
            clip_plan_file.writelines([f"file '{clip_path}'\n" for clip_path in clip_plan])

    print('Concatenating videos')
    ffmpeg.input(str(clip_plan_path), format='concat', safe=0).output(str(out_video_path), c='copy').run()
    print('Done')


if __name__ == '__main__':
    main()
