import os
import re
import shutil
import sys
from subprocess import check_output, CalledProcessError
from tempfile import mkdtemp
from pandocfilters import toJSONFilters, Para,RawBlock, RawInline, Plain, Image, get_filename4code, get_extension, walk, CodeBlock, Link, Str, Table, Math
from caps import caps
import pypandoc as pd
import json
from pathlib import Path
import pdb

from os.path import expanduser
home = expanduser("~")
path = os.path.dirname(os.path.realpath(__file__))
filters = [os.path.join(path, 'myfilter.py')]#, 'pandoc-citeproc']
pdoc_args = ['--mathjax', '--smart', '--parse-raw', '--atx-headers']


def run_external_process(args):
    try:
        check_output(args) #, stdout=sys.stderr)
    except CalledProcessError:
        tb = traceback.format_exc()
        tb = tb.replace(passwd, "******")
        syst.stderr.write(tb)
        exit(1)

def dir_directory(home=home):
    dir = os.getcwd()

def isblock(type):
    """Check if the input type is a block type."""
    if type in ['Plain', 'Para', 'CodeBlock', 'RawBlock','BlockQuote',
                'OrderedList','BulletList','DefinitionList','Header',
                'HorizontalRule','Table','Div','Null']:
        return True
    elif type in ['Str','Emph','Strong','Strikeout','Superscript',
                  'Subscript','SmallCaps','Quoted','Cite','Code','Space',
                  'LineBreak','Math','RawInline','Link','Image','Note',
                  'SoftBreak','Span']:
        return False
    else:
        raise StandardError('Unknown Type')



def latex(x):
    return RawBlock('latex', x)

def include(file):
    """gpp include instruction"""
    return RawInline('tex', '#include ' + file)

def html(x):
    return RawBlock('html', x)

def decamel(name):
    """Remove camel case from a string"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
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

# def only2file(only_body, outfile):
#     """Write given code to an octave file."""
#     #tmpdir = mkdtemp()
#     #olddir = os.getcwd()
#     #os.chdir(tmpdir)
#     f = open(outfile, 'w')
#     f.write(only_body)
#     f.close()

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
    run_external_process(["pdflatex", 'tikz.tex'])
        
    os.chdir(olddir)
    if filetype == 'pdf':
        shutil.copyfile(tmpdir + '/tikz.pdf', outfile + '.pdf')
    else:
        run_external_process(["convert", tmpdir + '/tikz.pdf', outfile + '.' + filetype])
    shutil.rmtree(tmpdir)

def latex2animation(tex_list, outfile, fps=24, tmpdir=None):
    """Create an animation from a series of latex files."""
    remove_temp = False
    if tmpdir is None:
        remove_temp=True
        tmpdir = mkdtemp()
    olddir = os.getcwd()
    os.chdir(tmpdir)
    if not os.path.isfile(outfile):
        in_arg = []
        for i, body in enumerate(tex_list):
            interfile = 'animate' + str(i).zfill(4)
            picture2image(body, 'png', os.path.join(tmpdir,interfile), tmpdir=tmpdir)
            in_arg.append('-delay')
            in_arg.append(str(1000/fps))
            in_arg.append(os.path.join(tmpdir,interfile) + '.png')
        run_external_process(['convert'] + in_arg + ['-loop', '0', os.path.join(olddir,outfile)])
        sys.stderr.write('Created image ' + outfile + '\n')
    if remove_temp:
        shutil.rmtree(tmpdir)
    os.chdir(olddir)
                    
def picture2image(picture_src, filetype, outfile, tmpdir=None):
    """Create an image from latex code that defines a picture."""
    tmpdir = '.'
    remove_temp = False
    if tmpdir is None:
        remove_temp = True
        tmpdir = mkdtemp()
    olddir = os.getcwd()
    os.chdir(tmpdir)
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
    run_external_process(["pdflatex", 'picture.tex'])
    os.chdir(olddir)
    if filetype == 'pdf':
        shutil.copyfile(os.path.join(tmpdir, 'picture.pdf'), outfile + '.pdf')
    else:
        run_external_process(["convert", '-density', '150', os.path.join(tmpdir,'picture.pdf'), '-quality', '100', '-flatten', '-sharpen', '0x1.0', outfile + '.' + filetype])
        run_external_process(["convert", '-negate', outfile + '.' + filetype, outfile + '_neg.' + filetype])
        sys.stderr.write(outfile + filetype)
        
    #if remove_temp:
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
        meta = extract_json_info(meta)
        if key == 'RawInline':
            [fmt, code] = val
            if fmt == "latex" and re.match(r"\\{name}".format(name=name), code):
                macro_pattern = re.compile(r"\\{name}{{(.*)}}".format(name=name))
                m = macro_pattern.match(code)
                if m:
                    body = m.group(1)
                    #sys.stderr.write(body)
                    f, e = os.path.splitext(body)
                    if e == '':
                        body += ext
                    f = get_file(f)
                    outputfile = f + '.md'
                    if body[0] != '#':
                        # Only write if it's not been written before!
                        if not os.path.isfile(outputfile):
                            # Call pandoc again on the included file
                            olddir = os.getcwd()
                            d = os.path.dirname(outputfile)
                            os.chdir(d)
                            fname = os.path.basename(outputfile)
                            extra_args = pdoc_args + conv2meta_arg(meta)
                            output=pd.convert_file(fname,
                                                   to='markdown',
                                                   format='latex',
                                                   extra_args=extra_args,
                                                   filters=filters)
                            f = open(fname, 'w')
                            f.write(output)
                            f.close()
                            os.chdir(olddir)
                        return include(outputfile)
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
        meta = extract_json_info(meta)
        assert(isinstance(meta,dict))
        if key == 'RawBlock':
            [fmt, code] = val
            if fmt == "latex":
                if re.match(r"\\begin{{{name}}}".format(name=name), code):
                    macro_pattern = re.compile(r"""\\begin{{{name}}}(.*)\\end{{{name}}}""".format(name=name), re.DOTALL)
                    m = macro_pattern.match(code)
                    if m:
                        body = m.group(1)
                        out = parse_to_json(body, preamble, format=fmt, meta=meta)
                        return [html('<!--{name} start-->'.format(name=name))] +out + [html('<!--{name} end-->'.format(name=name))]
                    
                    
    fun.__name__ = name
    if docstr is not None:
        fun.__doc__ = docstr
    else:
        fun.__doc__ = "Process the " + name + " environment."
    return fun

def meta_data(key, val, fmt, meta):
    """Write down a key from the meta information as a json str. Mainly for debugging"""
    meta = extract_json_info(meta)
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\metaData", code):
                macro_pattern = re.compile(r"""\\metaData{(.*)}""", re.DOTALL)
                m = macro_pattern.match(code)
                if m:
                    if m.group(1) in meta:
                        return Str('metadata:' + m.group(1) + '=' + json.dumps(meta[m.group(1)]))
                    else: 
                        return Str('metadata: ' + m.group(1) + ' not found. Keys are ' + str(meta.keys()))

def command_replace(name, replace='{name} {body}', docstr=None):
    """Process a latex command."""
    def fun(key, val, fmt, meta):
        meta = extract_json_info(meta)
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

# def only(key, val, fmt, meta):
#     """Deal with beamer's \only command"""
#     if key == 'RawInline':
#         [fmt, code] = val
#         if fmt == "latex":
#             if re.match(r"\\only", code):
#                 macro_pattern = re.compile(r"""\\only{?<(.*)>}?{(.*)}""", re.DOTALL)
#                 m = macro_pattern.match(code)
#                 if m:
#                     sys.stderr.write(str(m.group(2)))
#                     body = m.group(2)
#                     number = m.group(1)
#                     environment_text = '\input{{notation_def}}\n\n{body}'.format(body=body)
#                     sys.stderr.write(environment_text)
#                     f = open('tmp.tmp', 'w')
#                     f.write(environment_text)
#                     f.close()
#                     output=pd.convert_text(source=environment_text,
#                                            to='json',
#                                            format='latex',
#                                            extra_args=pdoc_args,
#                                            filters=filters)
#                     f = open('tmp2.tmp', 'w')
#                     f.write(output)
#                     f.close()
#                     out = json.loads(output)['blocks']
#                     pre = [html('only sildeno={number}'.format(number=number))]
#                     f = open('tmp3.tmp', 'w')
#                     f.write(json.dumps(pre+out))
#                     f.close()
                    
#                     if isinstance(out, list):
#                         return  RawInline('latex', Para(pre + out))
#                     else:
#                         return RawInline('latex', Para(pre + [out]))
            

def animateinline(key, val, fmt, meta):
    """Handle the animateinline environment making a gif file"""
    meta = extract_json_info(meta)
    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{animateinline}", code):
                macro_pattern = re.compile(r"""\\begin{animateinline}\[?([^\]]*)\]?{?([^}]*)}?(.*)\\end{animateinline}""", re.DOTALL)
                m = macro_pattern.match(code)
                if m:
                    body_parts = m.group(3).split('\\newframe')
                    outfile = 'cat.gif'
                    if os.path.isdir('../diagrams'):
                        outfile = os.path.join('../diagrams', outfile)
                    latex2animation(body_parts, outfile)
                    return Para([Image(['', [], []], [], [outfile, ""])])

def columns(key, val, fmt, meta={}):
    """Replace Beamer columns with an html table"""
    meta = extract_json_info(meta)
    def get_align(val):
        if val is None:
            return 'AlignLeft'
        elif val == 'c':
            return 'AlignCenter'
        elif val == 't':
            return 'AlignLeft'
        elif val == 'r':
            return 'AlignRight'

    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{columns}", code):
                macro_pattern = re.compile(r"""\\begin{columns}(.*)\\end{columns}""", re.DOTALL)
                m = macro_pattern.match(code)
                def_align = get_align(None)
                width = None
                if m:
                    body = m.group(1)
                    macro_pattern = re.compile(r"""^\[([^\]]*)\](.*)""", re.DOTALL)
                    m = macro_pattern.match(body)
                    if m:
                        body = m.group(2)
                        def_align = get_align(m.group(1))

                    macro_pattern = re.compile(r"""^{([^}]*)}(.*)""", re.DOTALL)
                    m = macro_pattern.match(body)
                    if m:
                        body = m.group(2)
                        width = m.group(1)
                            
                    preamble = '\\input{notation_def.tex}\n'
                    out = parse_to_json(body, preamble, format=fmt, meta=meta)
                    cols = []
                    widths = []
                    col = []
                    def extract_col(ent, col, cols):
                        key = ent['t']
                        if 'c' in ent:
                            val = ent['c']
                        if key == 'Para':
                            for e in val:
                                col, cols = extract_col(e, col, cols)
                            return col, cols
                        elif key == 'RawInline':
                            [fmt, code] = val
                            if fmt == "latex":
                                if re.match(r"\\column", code):
                                    macro_pattern = re.compile(r"""\[([^\]]*)\]""", re.DOTALL)
                                    m = macro_pattern.match(code)
                                    if m:
                                        align = get_align(m.group(1))
                                    else:
                                        align = def_align
                                    macro_pattern = re.compile(r"""{([^}]*)}""", re.DOTALL)
                                    m = macro_pattern.match(code)
                                    if m:
                                        width = m.group(1)
                                    else:
                                        width = None

                                    cols.append([{'c': col, 't': 'Plain'}])
                                    col = []
                                    return col, cols

                        elif key == 'RawBlock':
                            [fmt, code] = val
                            if fmt == "latex":
                                if re.match(r"\\begin{column}", code):
                                    macro_pattern = re.compile(r"""\\begin{column}(.*)\\end{column}""", re.DOTALL)
                                    m = macro_pattern.match(code)
                                    align = def_align
                                    if m:
                                        body = m.group(1)
                                        macro_pattern = re.compile(r"""^\[([^\]]*)\](.*)""", re.DOTALL)
                                        m = macro_pattern.match(body)
                                        if m:
                                            body = m.group(2)
                                            align = get_align(m.group(1))

                                        macro_pattern = re.compile(r"""^{([^}]*)}(.*)""", re.DOTALL)
                                        m = macro_pattern.match(body)
                                        if m:
                                            body = m.group(2)
                                            width = m.group(1)
                                        preamble = '\\input{notation_def.tex}\n'
                                        out = parse_to_json(body, preamble, format=fmt, meta=meta)
                                        cols.append(out)
                                        col = []
                                        return col, cols
                                                    

                        col.append(ent)
                        return col, cols
                                
                    for ent in out:
                        col, cols = extract_col(ent, col, cols)
                    cols.append([{'c': col, 't': 'Plain'}])
                    
                    num_cols = len(cols)
                    align = [{'t': 'AlignCenter'}]*num_cols
                    maybe_width = widths
                    cor = [[]]*num_cols
                    return Table([],align,[],cor,[cols])
                
def conv2metajson_arg(meta):
    """Convert meta cell information to a single json argument for passing as meta information."""
    json_str = json.dumps(meta)
    json_arg = ['--metadata=metajson:' + json_str]
    return json_arg

def extract_json_info(meta):
    """Extract meta information structure from metajson argument."""
    return meta
    assert(meta is None or isinstance(meta, dict))
    if 'metajson' in meta:
        if meta['metajson']['t'] == 'MetaString':
            json_info = json.loads(meta['metajson']['c'])
            if isinstance(json_info, dict):
                #del(meta['metajson'])
                for key, val in json_info.items():
                    meta[key] = val
                return meta
            else:
                raise TypeError("Error metajson is not a dict, metajson:" + str(json_info))
        else:
            raise TypeError("Incorrect format for metajson")
    else:
        return meta

def parse_to_json(body, preamble=None, format='latex', meta={}):
    """Parse text of body to a json representation"""
    environment_text = '{preamble}{body}'.format(preamble=preamble, body=body)
    if not isinstance(meta, dict):
        raise TypeError('meta information should be a dict')
    
    extra_args = pdoc_args + conv2metajson_arg(meta)
    output=pd.convert_text(source=environment_text,
                           to='json',
                           format=format,
                           extra_args=extra_args,
                           filters=filters)
    return json.loads(output)['blocks']

def json_to_output(obj, to='markdown', meta={}):
    """Convert json structure to a given output."""
    extra_args = pdoc_args
    source = {'blocks': obj, "pandoc-api-version":[1,17,0,5], 'meta': meta}
    return pd.convert_text(source=json.dumps(source),
                           to=to,
                           format='json',
                           extra_args=extra_args,
                           filters=filters)

def frame(key, val, fmt, meta):
    """Replace Beamer frame with reveal frame"""
    meta = extract_json_info(meta)
    if key == 'RawBlock':
        [fmt, code] = val
        if fmt == "latex":
            if re.match(r"\\begin{frame}", code):
                macro_pattern = re.compile(r"""\\begin{frame}\[?([^\]]*)\]?(.*)\\end{frame}""", re.DOTALL)
                m = macro_pattern.match(code)
                if m:
                    body = m.group(2)
                    preamble = '\\input{notation_def.tex}\n'
                    out = parse_to_json(body, preamble, format=fmt, meta=meta)
                    pre = [html('<!-- begin frame -->')]
                    post = [html('<!-- end frame -->')]
                    if isinstance(out, list):
                        return  pre + out + post
                    else:
                        return pre + [out] + post


# def column(key, val, fmt, meta):
#     """Convert column command into relevant table command."""
#     meta = extract_json_info(meta)
#     if key == 'RawInline':
#         [fmt, code] = val
#         if fmt == "latex":
#             if re.match(r"\\column", code):
#                 macro_pattern = re.compile(r"""\\column{(.*)}""", re.DOTALL)
#                 m = macro_pattern.match(code)
#                 if m:
#                     width = m.group(1)
#                     return RawInline('html', '<td width="{width}">'.format(width=width))
#                 else:
#                     return RawInline('html', '<td>')

#column = command_replace('column', replace='<td width={body}>')
only = command_replace('only', replace='{{{name} width={body}}}')
onslide = command_replace('onslide', replace='{{{name} slideno={body}}}')

env_replace = []
env_replace.append({'name': 'overprint',
                    'docstr': "Replace the overprint environment"})
                    
overprint = environment_replace('overprint', docstr="Replace the overprint environment")

frame = environment_replace('frame', docstr="Replace the frame environment")
widelist = environment_replace('widelist', template='\\begin{{description}}\n{body}\\end{{description}}')

includetalkfile = include_file('includetalkfile')
includecvfile = include_file('includecvfile')

def makeuppercase(key, val, fmt, meta):
    """Replace the MakeUppercase macro with the upper case text."""
    meta = extract_json_info(meta)
    if key == 'Math':
        sys.stderr.write(str(val))
        [fmt, code] = val
        if re.match(r"\\MakeUppercase", code):
            match_pattern = re.compile(r"""\\MakeUppercase{([^}]*)}""")
            macro_match = match_pattern.findall(code)
            for m in macro_match:
                sys
                M = m.upper()
                code=code.replace('\\MakeUppercase{'+m+'}', '{' + M + '}')
            return Math(fmt, code)

def inputdiagram(key, val, fmt, meta):
    """Convert an inputdiagram section to a image file for inclusion."""
    meta = extract_json_info(meta)
    if key == 'RawInline':
        [fmt, code] = val
        if fmt == "latex" and re.match(r"\\inputdiagram", code):
            #outfile = get_filename4code("inputdiagram", code)
            match_macro = re.compile(r"""\\inputdiagram{(.*)}""")
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
    meta = extract_json_info(meta)
    if key == 'RawInline' and value[0] == 'tex':
        m = ov_pat.match(value[1])
        if m:
            c = m.group(1)
            c += re.sub(r'^\{|}$', "", m.group(2))
            c += m.group(3)
            return RawInline("tex", c)

                
def octave(key, val, fmt, meta):
    """Write an octave block to a new file."""
    meta = extract_json_info(meta)
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
    meta = extract_json_info(meta)
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


def write_notation():
    """Load in notation and write it out as a latex file."""
    import yaml
    import collections
    # Require an ordered dict for the yaml file https://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
    _mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

    def dict_representer(dumper, data):
        return dumper.represent_dict(data.items())

    def dict_constructor(loader, node):
        return collections.OrderedDict(loader.construct_pairs(node))

    yaml.add_representer(collections.OrderedDict, dict_representer)
    yaml.add_constructor(_mapping_tag, dict_constructor)

    f = open('notation_def.yml', 'r')
    notation = yaml.load(f)
    f.close()
    f = open('notation_def.tex', 'w')
    for key, val in notation.items():
        i = 1
        num = 0
        while(val['latex'].find('#'+str(i))>0):
            num+=1
            i+=1
        if num>0:
            f.write('\\newcommand{{\\{key}}}[{num}]{{{latex}}}\n'.format(num=num, key=key, latex=val['latex']))
        else:
            f.write('\\newcommand{{\\{key}}}{{{latex}}}\n'.format(key=key, latex=val['latex']))
    f.close()
    
