#!/bin/env python3
# Copyright (C) 2021 Trent Piepho <tpiepho@gmail.com>

import os.path
import sys
import pysrt
from fakeavidemux import Avidemux

if len(sys.argv) != 3:
    print('''
Usage: adm_edit_srt.py <project.py> <output.srt>

Will read in Avidemux project file project.py and run the edits contained
therein to .srt subtitle files.  The .srt files should be in the same folder
with the same name but with .srt extension as the video files they correspond
to.

Will write the combined edited sibtitles to the output file named as the second
argument.

.srt files can be generated with ffmpeg, typically:
    ffmpeg -i video.mkv -map 0:s video.srt

Or for ATSC captures with EIA-608 closed captions:
    ffmpeg -f lavfi -i movie=video.ts[out0+subcc] -map 0:s video.srt

Note that this simple script does not take into account the Avidemux timestamp
shift caused by leading B-frames.
''')
    sys.exit(1)

# Read in Avidemux Project, which will create an adm object that has the file
# and segment info
proj = open(sys.argv[1]).read()
exec(proj)

# Read all files loaded in project with .srt extension as subtitles
srt = [pysrt.open(os.path.splitext(f)[0] + '.srt') for f in adm.files]

subs = pysrt.SubRipFile() # Accumulated output subs
time_us = 0               # Current output timestamp in microseconds
for n, start_us, len_us in adm.segments:
    # There is some small negative offset we should apply to start_us because
    # of Avidemux's timestamp modification.
    start_srt = pysrt.SubRipTime(milliseconds=start_us/1000)
    end_srt = pysrt.SubRipTime(milliseconds=(start_us+len_us)/1000)
    seg = srt[n].slice(starts_after=start_srt, ends_before=end_srt)
    seg.shift(milliseconds=(time_us-start_us)/1000)
    subs += seg
    time_us += len_us

subs.clean_indexes()
subs.save(sys.argv[2])
