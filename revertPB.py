import datetime
import xml.etree.ElementTree as ET
import argparse

global attemptID
global attemptRT
global attemptGT

class splittimestamp:
    def __init__(self):
        self.dt = datetime.datetime(datetime.MINYEAR, 1, 1)

    def add(self, textrep):
        x = datetime.time.fromisoformat(textrep[:-1])
        delta = datetime.timedelta(hours=x.hour, minutes=x.minute, seconds=x.second, microseconds=x.microsecond)
        self.dt = self.dt + delta
        return self.dt.time().isoformat()+'0'
        

class splitsinfo:
    def __init__(self):
        self.game = ''
        self.category = ''
        self.platform = ''
        self.variables = {}
        self.completed_attempts = []
        self.attempt_count = 0
        self.segments = []
        pass

    def __str__(self):
        r = """\
Game: {game}
Category: {category}
Platform: {platform}
Attempt Count: {attempt_count}

Variables:\
""".format(game=self.game,
        category=self.category,
        platform=self.platform,
        attempt_count=self.attempt_count)
        
        for v in self.variables.keys():
            r = ("""%s\n\t%s = %s""" % (r, v, self.variables[v]))

        r = ("%s\n%-20s %16s / %-16s | %s" % (r,"Split Name", "PB GameTime", "PB RealTime", "Attempt Game/Real Time"))
        for s in self.segments:
            r = ("""%s\n%s""" % (r, s)) #inefficient, but easy to understand

        r = ("\n%s\n\n%-20s %s " % (r, "Split Name", "Attempt Accumulative Times"))
        for s in self.segments:
            r = ("""%s\n%-20s %16s / %-16s""" % (r, s.name, s.times['attempt']['GameTime'], s.times['attempt']['RealTime']))
        return r

class segmentinfo:
    def __init__(self, elem):
        self.XMLelem = elem
        self.name = elem.find('Name').text
        self.times = {}
        for child in elem.find('SplitTimes'):
            tname = child.attrib['name']
            self.times[tname] = {}
            for tchild in child:
                self.times[tname][tchild.tag] = tchild.text

        for child in elem.find('SegmentHistory'):
            tname = child.attrib['id']
            self.times[tname] = {}
            for tchild in child:
                self.times[tname][tchild.tag] = tchild.text
                #print("Segment History: tname: %s\ntchild tag / text: %s / %s" % (tname, tchild.tag, tchild.text))
                #break
        
        self.times['attempt'] = {}
        self.times['attempt']['GameTime'] = attemptGT.add(self.times[str(attemptID)]['GameTime'])
        self.times['attempt']['RealTime'] = attemptRT.add(self.times[str(attemptID)]['RealTime'])

    def __str__(self):
        if attemptID == 0:
            return self.name
        #else
        rt = 'RealTime'
        gt = 'GameTime'
        pb = self.times['Personal Best']
        attempt = ''
        try:
            attempt = self.times[str(attemptID)]
            attempt = ("%-16s / %s" % (attempt[gt], attempt[rt]))
        except KeyError as E:
            attempt = ("%-16s / %s" % ('?', '?'))
        return ("%-20s %16s / %-16s | %s" % (self.name, pb[gt], pb[rt], attempt))

def _GameName(splitinfo, elem):
    splitinfo.game = elem.text

def _CategoryName(splitinfo, elem):
    splitinfo.category = elem.text

def _AttemptCount(splitinfo, elem):
    splitinfo.attempt_count = elem.text

def _Metadata(splitinfo, elem):
    platform = elem.find('Platform').text
    splitinfo.platform = platform

    for e in elem.find('Variables'):
        splitinfo.variables[e.attrib['name']] = e.text
    pass

def _AttemptHistory(splitinfo, elem):
    pass

def _Segments(splitinfo, elem):
    for child in elem:
        splitinfo.segments.append(segmentinfo(child))
        #splitname = child.find('Name').text
        #splitinfo.segments.append(splitname)
    pass

tag_handlers = {}
tag_handlers['GameName'] = _GameName
tag_handlers['CategoryName'] = _CategoryName
tag_handlers['AttemptCount'] = _AttemptCount
tag_handlers['Metadata'] = _Metadata
tag_handlers['AttemptHistory'] = _AttemptHistory
tag_handlers['Segments'] = _Segments
#tag_handlers[''] = _


def getFinishedAttempts():
    pass

def main(splitsfile):
    tree = ET.parse(splitsfile)
    root = tree.getroot()
    info = splitsinfo()

    for child in root:
        try:
            tag_handlers[child.tag](info, child)
        except KeyError as e:
            #print("No handler for %s: %s" % (child.tag, child))
            pass
    print(info)

    for s in info.segments:
        for comparison in s.XMLelem.find('SplitTimes'):
            if comparison.attrib['name'] != 'Personal Best':
                continue
            comparison.find('GameTime').text = s.times['attempt']['GameTime']
            comparison.find('RealTime').text = s.times['attempt']['RealTime']
        pass
    tree.write(args.splitsfile, encoding="UTF-8", xml_declaration=True)
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Change effective PB run to prior attempt. Useful for reverting accidental replacement of the current PB in LiveSplit.')
    parser.add_argument('splitsfile', metavar='FILE', type=str, help='Splits file')
    parser.add_argument('attempt', metavar='ATTEMPT', type=int, help='Attempt ID', default=0)
    args = parser.parse_args()
    print('''File to process: %s''' % (args.splitsfile))
    attemptID = args.attempt
    attemptRT = splittimestamp()
    attemptGT = splittimestamp()
    main(args.splitsfile)
    #
