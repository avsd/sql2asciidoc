# Author: David Avsajanishvili
# Contact: avsd05@gmail.com

"""
Different methods for ASCIIDOC formatting/reformatting
"""

import re

def make_title_references(dest, src=None):
    """
    Finds titles in src, makes links in dest and returns it
    """

    if not src:
        src = dest

    # List of found titles
    titles = []

    # Find titles in src
    rx = re.compile(r"^(\w.*)\n([=\^\+~-]+)$", re.MULTILINE)
    for a, b in rx.findall(src):
        if len(a)==len(b):
            titles.append(a)

    # Replace
    def anchored(t):
        return "<<_%s,%s>>" % (re.sub("\W", "_", t).strip("_").lower(),t)
    for a in titles:
        dest = re.sub("(?i)(\\b%s\\b)(?!\\n[=\\^\\+~-]+)([^>]{2})" % re.escape(a), "%s\\2" % anchored(a), dest)

    return dest
                    
