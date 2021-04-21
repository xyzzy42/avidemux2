# Hack to create a fake Avidemux() class so that Avidemux project scripts, which
# are basically Python, can be run by a real Python program.  It just stubs most
# functions and only keeps track of files and segments.

class Avidemux:
    def __init__(self):
        self.files = []
        self.segments = []

    def loadVideo(self, name):
        self.files += [name]
        return True

    def appendVideo(self, name):
        return self.loadVideo(name)

    def clearSegments(self):
        self.segments = []

    def addSegment(self, source, start, length):
        self.segments.append( (source, start, length) )

    def audioTotalTracksCount(self):
        return len(self.files)

    def videoCodec(self, *args):
        pass

    def addVideoFilter(self, *args):
        pass

    def audioClearTracks(self, *args):
        pass

    def setSourceTrackLanguage(self, *args):
        pass

    def audioAddTrack(self, *args):
        pass

    def audioCodec(self, *args):
        pass

    def audioSetMixer(self, *args):
        pass

    def audioSetDrc(self, *args):
        pass

    def audioSetShift(self, *args):
        pass

    def setContainer(self, *args):
        pass
