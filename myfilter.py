#!/usr/bin/env python

"""
Pandoc filter to process latex talks into markdown.
"""

from ndlfilters import makeuppercase, octave, frame, inputdiagram, includetalkfile, tikz, only, columns, overprint, animateinline, overlay, onslide, only, includecvfile, widelist, meta_data
import pandocfilters as pd

if __name__ == "__main__":
    pd.toJSONFilters([makeuppercase, includetalkfile, octave, inputdiagram, tikz, frame, columns, overprint, animateinline, only, onslide, includecvfile, widelist, meta_data])
