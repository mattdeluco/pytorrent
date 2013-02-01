
import re
import os

from datetime import datetime

# Inheriting from object creates a "new-style" class (post 2.1).
# Among other things, this enables properties (example below - # piece_length)
# and descriptors.
class PyTorrent(object):
    """Provide a simple interface to bencoded bittorrent files.

    http://www.bittorrent.org/beps/bep_0003.html
    http://wiki.theory.org/BitTorrentSpecification

    Keyword arguments
    * path: the path to the bittorrent file

    Exposed information
    * created_by: the client that created the torrent
    * creation_date: the date on which the torrent was created
    * comment: any comment included with the torrent
    
    * announce: a list of lists of trackers
    * private: 1 indicates torrent is tracked by private tracker

    * files: file information by file path
    * pieces: a list of 20-byte SHA1 hash values
    * piece_length: the length of each piece

    """

    torrent_file = ""
    torrent_data = {}

    created_by = ""
    comment = ""

    announce = []           # http://bittorrent.org/beps/bep_0012.html
    private = 0

    name = ""
    files = {}
    pieces = []
    piece_length = 0

    def getDate(self):
        return self._creation_date.strftime("%a. %b. %d, %Y %H:%M")

    def setDate(self, value):
        self._creation_date = datetime.fromtimestamp(value)

    creation_date = property(getDate, setDate, doc="The date this torrent was created.")

    def __init__(self, path):
        self.torrent_file = path

        tor_file_len = os.path.getsize(self.torrent_file)
        with open(self.torrent_file, 'r') as f:
            self.parse(f.read(tor_file_len))

        data = self.torrent_data

        self.created_by = data.get("created by", "")
        self.creation_date = data.get("creation date", "")
        self.comment = data.get("comment", "")
        
        # For convenience, create same data structure (list of lists)
        # for both announce and announce-list
        self.announce = data.get("announce-list", [[data['announce']]])

        self.generateFileList()

        info = data['info']
        pieces = bytearray(info['pieces'])
        self.pieces = [ pieces[i:i+20] for i in range(0, len(pieces), 20) ]
        self.piece_length = info['piece length']
        self.private = info.get("private", 0)
        self.name = info['name']

    def __del__(self):
        pass

    def __str__(self):
        return ("File: {filename}\n"
                "Name: {name}\n"
                "Date: {date}\n"
                "Client: {client}\n"
                "Tracker(s){private}: {tracker}\n"
                "Comment: {comment}\n").format(
                        filename=self.torrent_file,
                        name=self.name,
                        client=self.created_by,
                        date=self.creation_date,
                        tracker=self.announce,
                        private=(" (private)" if self.private else ""),
                        comment=self.comment)

    def generateFileList(self):
        """Populates the files member.
        The idea here is to provide identical data structures regardless
        of whether this torrent is single or multiple file.
        """
        info = self.torrent_data['info']
        name = info['name']
        if "files" in info:
            # Prepend "name" (of directory) to file path
            self.files = dict(("{0}/{1}".format(name, '/'.join(f['path'])), f)
                    for f in info['files'])
        else:
            # Ok, I know what you're thinking.  This is kinda bad.  I did it
            # just for fun.  Two things: 1) I wanted to conditionally add the
            # "md5sum" key, hence the comprehension.  2) In order to match the
            # multiple file structure above, the "name" key had to change to
            # "path".
            self.files = { name:
                    dict(((key if key != "name" else "path"), info[key])
                        for key in ("name", "length", "md5sum")
                        if key in info) }

    # Providing the regex as a default parameter argument keeps it from being
    # recompiled on recursive calls.
    def parse(self, string, i=0, reg=re.compile("([idle])|(\d+):|(-?\d+)")):
        """Populate the torrent_data member by recursively parsing an arbitrarily
        complex bencoded structure.
        """
        result = []
        while i < len(string):
            match = reg.match(string, i)
            m_str = match.group(match.lastindex)
            i = match.end()
            if match.lastindex == 1:
                if m_str in ("d", "l"):
                    i, r = self.parse(string, i, reg)
                    if m_str == "d":
                        r = dict(zip(r[0::2], r[1::2]))
                    result.append(r)
                elif m_str == "e":
                    return (i, result)
            elif match.lastindex == 2:
                result.append(string[i:i + int(m_str)])
                i += int(m_str)
            else:
                result.append(int(m_str))
                i += 1

        self.torrent_data = result[0]


__all__ = ['PyTorrent']

