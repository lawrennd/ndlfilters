import os
import re
import shutil
import sys
from subprocess import call
from tempfile import mkdtemp
from pandocfilters import toJSONFilters, Para,RawBlock, RawInline, Plain, Image, get_filename4code, get_extension, walk, CodeBlock, Link, Str
from caps import caps
import pypandoc as pd
import json
import pdb

filters = ['../../../pandoc/python/myfilter.py']#, 'pandoc-citeproc']
pdoc_args = ['--mathjax', '--smart', '--parse-raw']

def latex(x):
    return RawBlock('latex', x)


def html(x):
    return RawBlock('html', x)

def decamel(name):
    """Remove camel case from a string"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    #s1 = re.sub('([^0-9]([0-9][0-9])[^0-9]', r'0\1', s1)
    #s1 = re.sub('([^0-9]([0-9])[^0-9]', r'00\1', s1)
    #sys.stderr.write(s1)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def get_filename(source):
    """Generate the file name given directory and source file."""
    pass

def octave2file(octave_src, outfile):
    """Write given code to an octave file."""
    #tmpdir = mkdtemp()
    #olddir = os.getcwd()
    #os.chdir(tmpdir)
    f = open(outfile+'.m', 'w')
    f.write(octave_src)
    f.close()

def tikz2image(tikz_src, filetype, outfile):
    """Create an image from a tikz file"""
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
    """Create an image from latex code that defines a picture."""
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

def get_file(fullfile):
    """Get a decamelled filename"""
    base = os.path.basename(fullfile)
    outfile = decamel(os.path.splitext(base)[0])
    dirname = os.path.dirname(fullfile)
    return os.path.join(dirname, outfile)

def include_file(name, ext='.tex', docstr=None):
    """Deal with included files."""
    def fun(key, val, fmt, meta):
        if key == 'RawInline':
            [fmt, code] = val
            if fmt == "latex" and re.match(r"\\{name}".format(name=name), code):
                macro_pattern = re.compile(r"\\{name}{{(.*)}}".format(name=name))
                m = macro_pattern.match(code)
                if m:
                    body = m.group(1)
                    sys.stderr.write(body)
                    f, e = os.path.splitext(body)
                    if e == '':
                        body += ext
                    f = get_file(f)
                    outputfile = f + '.md'
                    if body[0] != '#':
                        if not os.path.isfile(outputfile):
                            # Call pandoc again on the included file
                            call(['pandoc',
                                  '-R', body, '--to=markdown',
                                  '--filter=../../../pandoc/python/myfilter.py',
                                  '--from=latex',
                                  '--output=' + outputfile],
                                 stdout=sys.stderr)
                        return RawInline('tex', '#include ' + outputfile)
    fun.__name__ = name
    if docstr is not None:
        fun.__doc__ = docstr
    else:
        fun.__doc__ = "Deal with file included in " + name + " environment."
    return fun

                        
def environment_replace(name,
                        preamble='\\input{notation_def.tex}',
                        template='{preamble} {body}', docstr=None):
    """Process a latex environment."""
    def fun(key, val, fmt, meta):
        if key == 'RawBlock':
            [fmt, code] = val
            if fmt == "latex":
                if re.match(r"\\begin{{{name}}}".format(name=name), code):
                    macro_pattern = re.compile(r"""\\begin{{{name}}}(.*)\\end{{{name}}}""".format(name=name), re.DOTALL)
                    m = macro_pattern.match(code)
                    if m:
                        body = m.group(1)
                        environment_text = template.format(preamble=preamble, name=name, body=body)
                        output=pd.convert_text(source=environment_text,
                                               to='json',
                                               format='latex',
                                               extra_args=pdoc_args,
                                               filters=filters)
                        return [html('<!--{name} start-->'.format(name=name))] + json.loads(output)['blocks'] + [html('<!--{name} end-->'.format(name=name))]
                    
                    
    fun.__name__ = name
    if docstr is not None:
        fun.__doc__ = docstr
    else:
        fun.__doc__ = "Process the " + name + " environment."
    return fun

def command_replace(name, replace='{name} {body}', docstr=None):
    """Process a latex command."""
    def fun(key, val, fmt, meta):
        if key == 'RawInline':
            [fmt, code] = val
            if fmt == "latex":
                if re.match(r"\\{name}".format(name=name), code):
                    macro_pattern = re.compile(r"""\\{name}{{(.*)}}""".format(name=name), re.DOTALL)
                    m = macro_pattern.match(code)
                    if m:
                        sys.stderr.write(str(m.group(1)))
                        body = m.group(1)
                        command_text = replace.format(name=name, body=body)
                        return Str(command_text)
    fun.__name__ = name
    if docstr is not None:
        fun.__doc__ = docstr
    else:
        fun.__doc__ = "Process the " + name + " command."
    return fun

def only(key, val, fmt, meta):
    """Deal with beamer's \only command"""
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\only", code):
                macro_pattern = re.compile(r"""\\only{?<(.*)>}?{(.*)}""", re.DOTALL)
                m = macro_pattern.match(code)
                if m:
                    sys.stderr.write(str(m.group(2)))
                    body = m.group(2)
                    number = m.group(1)
                    environment_text = '\input{{notation_def}}\n\n{body}'.format(body=body)
                    sys.stderr.write(environment_text)
                    f = open('tmp.tmp', 'w')
                    f.write(environment_text)
                    f.close()
                    output=pd.convert_text(source=environment_text,
                                           to='json',
                                           format='latex',
                                           extra_args=pdoc_args,
                                           filters=filters)
                    f = open('tmp2.tmp', 'w')
                    f.write(output)
                    f.close()
                    out = json.loads(output)['blocks']
                    pre = [html('only sildeno={number}'.format(number=number))]
                    f = open('tmp3.tmp', 'w')
                    f.write(json.dumps(pre+out))
                    f.close()
                    
                    if isinstance(out, list):
                        return  RawInline('latex', Para(pre + out))
                    else:
                        return RawInline('latex', Para(pre + [out]))
            

def animateinline(key, val, fmt, meta):
    """Handle the animateinline environment making a gif file"""
    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{animateinline}", code):
                macro_pattern = re.compile(r"""\\begin{animateinline}[(.*)]{(.*)}(.*)\\end{animateinline}""", re.DOTALL)
                m = macro_pattern.match(code)
                if m:
                    body = m.group(3)
                    return latex(body)

def columns(key, val, fmt, meta):
    """Replace Beamer columns with an html table"""
    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{columns}", code):
                macro_pattern = re.compile(r"""\\begin{columns}(.*)\\end{columns}""", re.DOTALL)
                m = macro_pattern.match(code)
                if m:
                    body = m.group(1)
                    preamble = '\\input{notation_def.tex}\n'
                    environment_text = '{preamble}{body}'.format(preamble=preamble, body=body)
                    output=pd.convert_text(source=environment_text,
                                           to='json',
                                           format='latex',
                                           extra_args=pdoc_args,
                                           filters=filters)
                    out = json.loads(output)['blocks']
                    pre = [html('<table><tr><td>')]
                    post = [html('</td></tr></table>')]
                    if isinstance(out, list):
                        return  pre + out + post
                    else:
                        return pre + [out] + post



column = command_replace('column', replace='{{{name} width={body}}}')
onslide = command_replace('onslide', replace='{{{name} slideno={body}}}')

env_replace = []
env_replace.append({'name': 'overprint',
                    'docstr': "Replace the overprint environment"})
                    
overprint = environment_replace('overprint', docstr="Replace the overprint environment")

frame = environment_replace('frame', docstr="Replace the frame environment")
widelist = environment_replace('widelist', template='\\begin{{description}}\n{body}\\end{{description}}')

includetalkfile = include_file('includetalkfile')
includecvfile = include_file('includecvfile')

def MakeUppercase(key, val, fmt,meta):
    """Replace the MakeUppercase macro with the upper case text."""
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\MakeUppercase", code):
            sys.stderr.write('Whoop3')
            match_macro = re.compile(r"""\\MakeUppercase\{(.*)\}""")
            macro_match = match_macro.findall(code)
            for m in macro_match:
                M = caps(val, fmt, meta)
            return Str(M)

def inputdiagram(key, val, fmt, meta):
    """Convert an inputdiagram section to a image file for inclusion."""
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\inputdiagram", code):
            #outfile = get_filename4code("inputdiagram", code)
            match_macro = re.compile(r"""\\inputdiagram\{(.*)\}""")
            macro_match = match_macro.findall(code)
            for m in macro_match:
                fullfile = m
                outfile = get_file(fullfile)
                filetype = get_extension(format, "png", html="png", latex="pdf")
                src = outfile + '.' + filetype
                if not os.path.isfile(src):
                    picture2image(code, filetype, outfile)
                    sys.stderr.write('Created image ' + src + '\n')
                return Image(['', [], []], [], [src, ""])

def overlay(key, value, fmt, meta):
    "From https://andrewgoldstone.com/blog/2014/12/24/slides/"
    if key == 'RawInline' and value[0] == 'tex':
        m = ov_pat.match(value[1])
        if m:
            c = m.group(1)
            c += re.sub(r'^\{|}$', "", m.group(2))
            c += m.group(3)
            return RawInline("tex", c)

                
def octave(key, val, fmt, meta):
    """Write an octave block to a new file."""
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
    """Convert a tikz file to an image for inclusion."""
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

