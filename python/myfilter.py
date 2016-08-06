#!/usr/bin/env python

"""
Pandoc filter to process latex talks into markdown.
"""

from ndlfilters import octave, frame, inputdiagram, includetalkfile, tikz, only
import pandocfilters as pd

if __name__ == "__main__":
    pd.toJSONFilters([includetalkfile, frame, octave, inputdiagram, tikz, only])
