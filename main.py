#!usr/bin/env python

import os
import random

import ffmpeg


# todo: auto check duration of current working video
iterations = 10
out_video = '10hours.mp4'
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


def main():
    for i in range(iterations):
        clip_to_add = weighted_choice(clips)

        if out_video not in os.listdir():
            ffmpeg.input(clip_to_add).output(out_video).run()
        else:
            concat_input = f"file '{out_video}'\nfile '{clip_to_add}'"
            ffmpeg.input(concat_input, format='concat', safe=0).output(f'new-{out_video}').run()
            os.remove(out_video)
            os.rename(f'new-{out_video}', out_video)


if __name__ == '__main__':
    main()
