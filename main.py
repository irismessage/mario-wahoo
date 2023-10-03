#!usr/bin/env python

import time
import random
import itertools
import concurrent.futures
from pathlib import Path

import ffmpeg
import ffprobe


with open("format.txt") as file_format_file:
    file_format = file_format_file.read().strip("\n. ")


clips_folder = Path() / "clips"
out_video_path = clips_folder / f"_10hours.{file_format}"
clip_plan_path = clips_folder / "_clip_plan.txt"

# wew long name
out_video_target_duration_hours = 10
out_video_target_duration_seconds = out_video_target_duration_hours * (60**2)

with open("clips.txt") as clips_list_file:
    clips = clips_list_file.readlines()
clips = [clip.rstrip("\n") for clip in clips]
clips = [f"{clip}.{file_format}" for clip in clips]


def weighted_choice(choices, default_weight=1, banned=None):
    if banned is None:
        banned = []

    choices_population = []
    choices_weights = []
    for choice in choices:
        if isinstance(choice, tuple):
            choice_item, choice_weight = choice[0], choice[1]
        else:
            choice_item, choice_weight = choice, default_weight

        if choice_item not in banned:
            choices_population.append(choice_item)
            choices_weights.append(choice_weight)

    return random.choices(choices_population, choices_weights)[0]


def ffprobe_length_seconds(audio_path):
    metadata = ffprobe.FFProbe(str(audio_path))
    for stream in metadata.streams:
        if stream.is_audio():
            return stream.duration_seconds()


def get_clip(banned):
    with open("no-dupe.txt") as no_dupe_file:
        no_dupe = no_dupe_file.readlines()
    no_dupe = [no_dupe_item.rstrip("\n") for no_dupe_item in no_dupe]
    no_dupe = [f"{no_dupe_item}.{file_format}" for no_dupe_item in no_dupe]

    clip_to_add_name = weighted_choice(clips, banned=banned)
    clip_to_add = clips_folder / clip_to_add_name
    if banned:
        banned = []
    if clip_to_add_name in no_dupe:
        banned.append(clip_to_add_name)

    return clip_to_add, banned


def add_clip_length_to_dict(clip_path, clip_lengths: dict):
    clip_length = ffprobe_length_seconds(clip_path)
    clip_lengths[clip_path] = clip_length

    print(f"{clip_path}: {clip_length}s")


def generate_list(clip_paths=None, duration_target=out_video_target_duration_seconds):
    if clip_paths is None:
        clip_paths = clips
    clip_paths = [clips_folder / clip_path for clip_path in clip_paths]

    print("Generating randomised list")
    print("Getting clip lengths with ffprobe")
    clip_lengths = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(
            add_clip_length_to_dict, clip_paths, itertools.cycle([clip_lengths])
        )

    banned = []
    clip_plan = []

    # while the total length of all clips in the plan is less than the target length
    current_duration = 0
    while current_duration < duration_target:
        print(
            f"Done {current_duration} seconds, {time.strftime('%H:%M:%S', time.gmtime(current_duration))}"
        )
        clip_to_add, banned = get_clip(banned)
        current_duration += clip_lengths[clip_to_add]
        clip_plan.append(clip_to_add)

    return clip_plan


def main():
    if not clip_plan_path.is_file():
        with open(clip_plan_path, "w") as clip_plan_file:
            clip_plan = generate_list()
            clip_plan_file.writelines(
                [f"file '{clip_path.name}'\n" for clip_path in clip_plan]
            )

    print("Concatenating videos")
    ffmpeg.input(str(clip_plan_path), format="concat", safe=0).output(
        str(out_video_path), c="copy"
    ).run()
    print("Done")


if __name__ == "__main__":
    main()
