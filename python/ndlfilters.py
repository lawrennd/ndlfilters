import os
import re
import shutil
import sys
from subprocess import call
from tempfile import mkdtemp
from pandocfilters import toJSONFilters, Para, Image, get_filename4code, get_extension, walk, CodeBlock
from caps import caps
import pypandoc as pd
import json

filters = ['../../../pandoc/python/myfilter.py']#, 'pandoc-citeproc']
pdoc_args = ['--mathjax', '--smart']#, '--parse-raw']

def octave2file(octave_src, outfile):
    #tmpdir = mkdtemp()
    #olddir = os.getcwd()
    #os.chdir(tmpdir)
    f = open(outfile+'.m', 'w')
    f.write(octave_src)
    f.close()

def tikz2image(tikz_src, filetype, outfile):
    tmpdir = mkdtemp()
    olddir = os.getcwd()
    os.chdir(tmpdir)
    f = open('tikz.tex', 'w')
    f.write("""\\documentclass{standalone}
             \\usepackage{tikz}
             \\begin{document}
             """)
    f.write(tikz_src)
    f.write("\n\\end{document}\n")
    f.close()
    call(["pdflatex", 'tikz.tex'], stdout=sys.stderr)
    os.chdir(olddir)
    if filetype == 'pdf':
        shutil.copyfile(tmpdir + '/tikz.pdf', outfile + '.pdf')
    else:
        call(["convert", tmpdir + '/tikz.pdf', outfile + '.' + filetype])
    shutil.rmtree(tmpdir)

def picture2image(picture_src, filetype, outfile):
    tmpdir = '.'
    #tmpdir = mkdtemp()
    #olddir = os.getcwd()
    #os.chdir(tmpdir)
    f = open('picture.tex', 'w')
    f.write("""\\documentclass{standalone}
             \\standaloneconfig{crop=true}
             \\usepackage{picture}
             \\usepackage{graphicx}
             \\input{notationDef.tex}
             \\input{definitions.tex}
             \\begin{document}
             """)
    f.write(picture_src)
    f.write("\n\\end{document}\n")
    f.close()
    sys.stderr.write(picture_src + '\n')
    call(["pdflatex", 'picture.tex'], stdout=sys.stderr)
    #os.chdir(olddir)
    if filetype == 'pdf':
        shutil.copyfile(tmpdir + '/picture.pdf', outfile + '.pdf')
    else:
        call(["convert", tmpdir + '/picture.pdf', outfile + '.' + filetype])
    #shutil.rmtree(tmpdir)


def inputdiagram(key, val, fmt, meta):
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\inputdiagram", code):
            outfile = get_filename4code("inputdiagram", code)
            filetype = get_extension(format, "png", html="png", latex="pdf")
            src = outfile + '.' + filetype
            if not os.path.isfile(src):
                picture2image(code, filetype, outfile)
                sys.stderr.write('Created image ' + src + '\n')
            return Image(['', [], []], [], [src, ""])

def MakeUppercase(key, val, fmt,meta):
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\MakeUppercase", code):
            sys.stderr.write('Whoop3')
            match_macro = re.compile(r"""\\MakeUppercase\{(.*)\}""")
            macro_match = match_macro.findall(code)
            for m in macro_match:
                M = caps(val, fmt, meta)
            return Str(M)

def only(key, val, fmt,meta):
    """This doesn't work yet, because it looks like it terminates the leaf before the backets are picked up, i.e. it is \only then the next leaf is <1>. Presume similar for includegraphics."""
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\only", code):
            match_macro = re.compile(r"""\\only<(.*)>\{(.*)\}""", re.DOTALL)
            macro_match = match_macro.findall(code)
            
            for m in macro_match:
                sys.stderr.write(m)
                return Para(m[1] + ' ' + m[0])

def includetalkfile(key, val, fmt, meta):
    "Deal with included talk files."
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\includetalkfile", code):
            match_macro = re.compile(r"""\\includetalkfile\{(.*)\}""")
            macro_match = match_macro.findall(code)
            for m in macro_match:
                f, ext = os.path.splitext(m)
                if ext == '':
                    m += '.tex'
                outputfile = f + '.md'                    
                if m[0] != '#':
                    # Call pandoc again on the included file
                    call(['pandoc',
                          '-R', m, '--to=markdown',
                          '--filter=../../../pandoc/python/myfilter.py',
                          '--from=latex',
                          '--output=' + outputfile],
                         stdout=sys.stderr)

def frame(key, val, fmt, meta):
    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{frame}", code):
                match_macro = re.compile(r"""\\begin{frame}(.*)\\end{frame}""", re.DOTALL)
                macro_match = match_macro.findall(code)
                for m in macro_match:
                    frame_text = '\input{notation_def.tex}\n\hline' + m + '\hline'
                    output=pd.convert_text(source=frame_text,
                                           to='json',
                                           format='latex',
                                           extra_args=pdoc_args,
                                           filters=filters)
                    return json.loads(output)[1]

def octave(key, val, fmt, meta):

    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\begin{octave}", code):
            match_macro = re.compile(r"""\\begin{octave}(.*)\\end{octave}""", re.DOTALL)
            macro_match = match_macro.findall(code)
            for m in macro_match:
                outfile = get_filename4code("octave", code)
                src = outfile + '.m'
                if not os.path.isfile(src):
                    octave2file(m, outfile)
                    sys.stderr.write('Created file ' + src + '\n')
                return CodeBlock(("mycode",["octave","numberLines"],[("startFrom","0")]),m)

def tikz(key, val, fmt, meta):

    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{tikzpicture}", code):
                outfile = get_filename4code("tikz", code)
                filetype = get_extension(format, "png", html="png", latex="pdf")
                src = outfile + '.' + filetype
                if not os.path.isfile(src):
                    tikz2image(code, filetype, outfile)
                    sys.stderr.write('Created image ' + src + '\n')
                return Para([Image(['', [], []], [], [src, ""])])

