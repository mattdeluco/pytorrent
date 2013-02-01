
import re
import os

class PyTorrent(object):
    """Provide a simple interface to bencoded bittorrent files.

    http://www.bittorrent.org/beps/bep_0003.html
    http://wiki.theory.org/BitTorrentSpecification

    Keyword arguments
    * path: the path to the bittorrent file

    Exposed information
    * created_by: the client that created the torrent
    * creation_date: the date on which the torrent was created
    * announce: a list of lists of trackers
    * files: file information by file path

    """

    tor_file = ""
    torrent_data = {}

    created_by = ""
    creation_date = ""
    announce = ""           # http://bittorrent.org/beps/bep_0012.html
    files = {}

    def __init__(self, path):
        self.tor_file = path

        tor_file_len = os.path.getsize(self.tor_file)
        with open(self.tor_file, 'r') as f:
            self.parse(f.read(tor_file_len))

        self.created_by = self.torrent_data['created by']
        self.creation_date = self.torrent_data['creation date']

        # For convenience, create same data structure (list of lists)
        # for both announce and announce-list
        self.announce = (self.torrent_data['announce-list']
                if "announce-list" in self.torrent_data
                else [[self.torrent_data['announce']]])

        self.generateFileList()

    def __del__(self):
        pass

    def generateFileList(self):
        """Populates the files member.
        The idea here is to provide identical data structures regardless
        of whether this torrent is single or multiple file.
        """
        info = self.torrent_data['info']
        name = info['name']
        if "files" in info:
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

