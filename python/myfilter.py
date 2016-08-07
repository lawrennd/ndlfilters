#!/usr/bin/env python

"""
Pandoc filter to process latex talks into markdown.
"""

from ndlfilters import octave, frame, inputdiagram, includetalkfile, tikz, only, columns, overprint, animateinline, overlay, column, onslide
import pandocfilters as pd

if __name__ == "__main__":
    pd.toJSONFilters([includetalkfile, octave, inputdiagram, tikz, frame, columns, overprint, animateinline, overlay, column])
