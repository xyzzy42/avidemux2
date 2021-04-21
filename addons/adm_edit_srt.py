#!/bin/env python3
# Copyright (C) 2021 Trent Piepho <tpiepho@gmail.com>

import os.path
import subprocess
import codecs
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

def getsrt(name):
    srtname = os.path.splitext(name)[0] + '.srt'
    if os.path.exists(srtname):
        print(f"Reading for existing srt file '{srtname}'")
        return pysrt.open(srtname)
    if not os.path.exists(name):
        print(f"Can't find {srtname} or {name}, giving up")
        sys.exit(1)
    probe = subprocess.run(
        ['ffprobe', '-show_entries', 'stream=index', '-select_streams', 's', '-of', 'flat', name],
        capture_output=True, check=True)
    if probe.stdout.decode(sys.stdout.encoding).find('.index=') != -1:
        print(f"Extracting subs from {name}")
        cmd = ['ffmpeg', '-i', name, '-map', 's', '-f', 'srt', 'pipe:']
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as srtpipe:
            subs = pysrt.SubRipFile()
            subs.extend(subs.stream(codecs.getreader('UTF-8')(srtpipe.stdout)))
            return subs
    probe = subprocess.run( ['ffprobe', '-hide_banner', name], capture_output=True, check=True)
    if probe.stderr.decode(sys.stdout.encoding).find('Closed Captions'):
        print(f"Extracting EIA-608 Closed Captions from {name} (this make take awhile)")
        cmd = ['ffmpeg', '-f', 'lavfi', '-i', f"movie={name}[out0+subcc]", '-map', 's', '-f', 'srt', 'pipe:']
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as srtpipe:
            subs = pysrt.SubRipFile()
            subs.extend(subs.stream(codecs.getreader('UTF-8')(srtpipe.stdout)))
            return subs
    else:
        print(f"no subs in {name}")
        return None

# Read in Avidemux Project, which will create an adm object that has the file
# and segment info
proj = open(sys.argv[1]).read()
exec(proj)

# Read all files loaded in project with .srt extension as subtitles
srt = [getsrt(f) for f in adm.files]

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
