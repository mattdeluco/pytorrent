
import re
import os

class PyTorrent(object):
    """Provide a simple interface to bencoded bittorrent files.

    http://www.bittorrent.org/beps/bep_0003.html
    http://wiki.theory.org/BitTorrentSpecification

    Keyword arguments:
    path: the path to the bittorrent file

    """

    tor_file = ""
    tor_dict = {}

    def __init__(self, path):
        self.tor_file = path

        tor_file_len = os.path.getsize(self.tor_file)
        with open(self.tor_file, 'r') as f:
            self.parse(f.read(tor_file_len))

    def __del__(self):
        pass

    # Providing the regex as a default parameter argument keeps it from being
    # recompiled on recursive calls.
    def parse(self, string, i=0, reg=re.compile("([idle])|(\d+):|(-?\d+)")):
        """Populate the tor_dict member by recursively parsing an arbitrarily
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

        self.tor_dict = result[0]
