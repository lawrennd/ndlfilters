#!/usr/bin/env python

# File for reading in tex files and finding diagram entries. It then moves the diagrams into a new directory.

import os
import sys
import re
import string
import shutil
import posix
sys.path.append('/Users/neil/SheffieldML/projects/')
import ndltex
import yaml
import pypandoc as pd


# process.env.PATH = ["/usr/bin",
#                     "/usr/local/bin",
#                     ].join(":")
filters = ['./tikz.py']
pdoc_args = ['--mathjax',
             '--smart', '--parse-raw']


def decamel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


if len(sys.argv) < 2:
    raise("There must be at least two input arguments")
texfile_lines = []
new_name = sys.argv[1]
texFile = sys.argv[2:]

for file in texFile:
    new_lines = ndltex.readlines(file)
    if new_lines is not None:
        for l in new_lines:
            texfile_lines.append(l)

input_files = ndltex.extractInputs(texfile_lines)
print(input_files)
md_list = []
for file in input_files:
    md_dir = new_name
    filename = ndltex.expand_dir(ndltex.inputFileName(file))
    if filename is not None:
        defsname = ndltex.expand_dir('test_notation.tex')
        macroname = ''#ndltex.expand_dir('test_definitions.tex')
        print(filename)
        md_filename = decamel(os.path.split(filename)[1][:-4])+".md"
        md_name = os.path.join(md_dir, md_filename)
        md_command = "pandoc -R -f latex " + macroname + ' ' + defsname + ' ' + filename + " -o " + md_name
        print(macroname)
        pdoc_args.append(defsname)
        output = pd.convert_file(source_file=filename,
                         to='markdown',
                         format='latex',
                                 extra_args=pdoc_args,
                        filters=filters)
        print(output)
        #os.system(md_command)
        print(md_command)
        md_list.append(md_name)
#unlink(new_name)


