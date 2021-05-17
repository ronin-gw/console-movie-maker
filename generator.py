#!/usr/bin/env python3
import argparse
import os
import bz2
import time
from array import array
from itertools import cycle
from base64 import b85encode, b85decode

import cv2
import numpy as np


def _main():
    p = argparse.ArgumentParser()
    p.add_argument("video", nargs='?', default="video.mp4")
    p.add_argument("--height", nargs='?', default=9, type=int)
    p.add_argument("--width-scale", nargs='?', default=2., type=float)
    p.add_argument("--drop-frame", nargs='?', default=2, type=int)
    p.add_argument("--data-perline", nargs='?', default=150, type=int)
    p.add_argument("--invert", action="store_true")
    p.add_argument("--speed-scale", nargs='?', default=1., type=float)
    p.add_argument("-o", "--output", nargs='?', default="exapmle.py")

    args = p.parse_args()
    width = int(args.height / 3 * 4 * args.width_scale)
    fps = 30 / args.drop_frame * args.speed_scale
    spf = 1 / fps

    data = load(args.video, width, args.height, args.drop_frame)

    first, data = encode(data)
    first = not first if args.invert else first
    pixels = "# " if first else " #"

    with open(args.output, 'w') as f:
        output(data, args.data_perline, width, args.height, spf, pixels, f)

    # seq = makeseq(data, pixels)
    # play(seq, width, args.height, spf)


def load(path, width, height, drop_frame):
    c = cv2.VideoCapture(path)

    ret, frame = c.read()
    data = convert(frame, width, height).ravel()
    ret, frame = c.read()
    i = 1
    while ret:
        if i % drop_frame == 0:
            data = np.concatenate((data, convert(frame, width, height).ravel()))
        ret, frame = c.read()
        i += 1

    return data


def convert(frame, width, height):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (width, height))
    _, frame = cv2.threshold(frame, 127, 255, cv2.THRESH_BINARY)
    return frame


def encode(data):
    first = data[0] == 255
    data = np.concatenate(([True], data[1:] != data[:-1], [True])).nonzero()
    data = np.ediff1d(data)
    data = b85encode(bz2.compress(data.tobytes()))
    return first, data


def output(data, perline, width, height, spf, pixels, fp):
    print('import os,bz2,time,array,itertools,base64;Q="""', file=fp)
    for i in range(len(data) // perline):
        print(data[(i * perline):((i + 1) * perline)].decode('ascii'), file=fp)
    i += 1
    print(data[(i * perline):((i + 1) * perline)].decode('ascii'), end='"""\n', file=fp)
    print("""I=bz2.decompress(base64.b85decode(Q.replace('\\n','').replace(' ','')));a=array.array("q");a.frombytes(I);s=''.join(c*l for c,l in zip(itertools.cycle("{4}"),a))
for i in range(len(s)//{0}):frame=s[i*{0}:(i+1)*{0}];os.system('cls' if os.name=='nt' else 'clear');print(
'\\n'.join(frame[(j*{1}):((j+1)*{1})]for j in range({2})));time.sleep({3})""".format(width * height, width, height, spf, pixels), file=fp)


def makeseq(data, pixels):
    seq = ''
    data = bz2.decompress(b85decode(data))
    arr = array("q")
    arr.frombytes(data)
    for c, length in zip(cycle(pixels), arr):
        seq += c * length
    return seq


def play(seq, width, height, spf):
    pixels = width * height

    clear = 'cls' if os.name == 'nt' else 'clear'
    for i in range(len(seq) // pixels):
        frame = seq[(i * pixels):((i + 1) * pixels)]
        os.system(clear)
        print('\n'.join(frame[(j * width):((j + 1) * width)] for j in range(height)))
        time.sleep(spf)


if __name__ == "__main__":
    _main()
