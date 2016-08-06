#!/usr/bin/env python

"""
Pandoc filter to convert all regular text to uppercase.
Code, link URLs, etc. are not affected.
"""

from pandocfilters import toJSONFilter, Str, walk


def caps(key, value, format, meta):
    if key == 'Str':
        return Str(value.upper())

def inputdiagram(key, val, fmt, meta):
    print(key)
    #if key == 'emph':
     #   return walk(val, caps, fmt, meta)
    
if __name__ == "__main__":
    #toJSONFilter(caps)
    toJSONFilter(inputdiagram)
