import unittest
import json
import pandocfilters as pf
import ndlfilters
import pypandoc as pd
import os

path = os.path.dirname(os.path.realpath(__file__))
filters = [os.path.join(path, '..', 'myfilter.py')]#, 'pandoc-citeproc']

filter_test = [{'name': 'animateinline',
                'function': ndlfilters.animateinline,
                'test_text': '''\\begin{{animateinline}}[autoplay,loop]{{10}}
$\\int_{{0}}^x z^2 dx = \\frac{{z^3}}{{3}} +c$
\\newframe
$a=2$
\\newframe
$a=3$
\\newframe
$a=4$
\\end{{animateinline}}'''.format(path=path)},
               {'name': 'columns_one',
                'function' : ndlfilters.columns,
                'test_text': '''\\begin{columns}
<!-- begin frame -->
There was a cat, I like it.
\\column
Dogly
<!-- end frame -->\\end{columns}'''},
               {'name': 'columns_two',
                'function' : ndlfilters.columns,
                'test_text': '''\\begin{columns}
<!-- begin frame -->
\\begin{verbatim}
dogly
\\end{verbatim}
\\begin{column}
There was a cat, I like it.
\\end{column}
<!-- end frame -->\\end{columns}'''},
               {'name': 'columns_three',
                'function' : ndlfilters.columns,
                'test_text': '''\\begin{columns}[c]\\begin{verbatim}
Column2
\\end{verbatim}\\column{8cm}cat\\end{columns}'''},
               {'name': 'columns_four',
                'function' : ndlfilters.columns,
                'test_text': '''\\begin{columns}[c]Cat\\column{8cm}Dog\\column[c]Mouse\\end{columns}'''},
               {'name': 'frame',
                'function' : ndlfilters.frame,
                'test_text': '''\\begin{frame}
\\frametitle{Frame Title}
\\begin{itemize}
\\item This is a bullet.
\\end{itemize}
\\end{frame}'''},
               {'name': 'MakeUppercase',
                'function' : ndlfilters.makeuppercase,
                'test_text': '''$A - 3 \\MakeUppercase{{k}}$'''},
               {'name': 'includetalkfile',
                'function' : ndlfilters.includetalkfile,
                'test_text': '''\\includetalkfile{{{path}/test_talk.tex}}'''.format(path=path)
                },
               {'name': 'includecvfile',
                'function' : ndlfilters.includecvfile,
                'test_text': '''\\includecvfile{{{path}/test_cv.tex}}'''.format(path=path)
                },
               {'name': 'inputdiagram',
                'function' : ndlfilters.inputdiagram,
                'test_text': '''\\inputdiagram{{{path}/test_diagram.tex}}'''.format(path=path)
                },
               {'name': 'only',
                'function' : ndlfilters.only,                
                'test_text': '''\\begin{frame}
\\only<1>{This is the first frame}
\\only<2-3>{This is the second and third frame}
\\only<4-5>{Fourth and fifth}
\\only<3>{Only 3}
\\end{frame}'''}]

def gtf_(name, function,  test_text, arg=None, format='latex', extra_args=['-R'], filters=filters):
    def test_function(self):
        if arg is None:
            tester = FilterTester(function, test_text, format, extra_args, filters)
        else:
            tester = FilterTester(function, test_text, format, extra_args, filters, arg)
    
    test_function.__name__ = 'test_' + name
    test_function.__doc__ = 'filters_tests: Test function filters ' + name
    return test_function

def populate_filters(cls, filter_test):
    """populate_filter: Auto create filter test functions."""
    for filter in filter_test:
        base_funcname = 'test_' + filter['name']
        funcname = base_funcname
        i = 1
        while(funcname in cls.__dict__.keys()):
            funcname = base_funcname +str(i)
            i += 1
        _method = gtf_(**filter)
        setattr(cls, _method.__name__, _method)


class FilterTester(unittest.TestCase):
    """This class is the base class for testing the filters."""
    def __init__(self, filter, text, format='latex', extra_args=['-R'], meta={}, **kwargs):
        self.kwargs = kwargs
        self.a = json.loads(pd.convert_text(text,
                                            extra_args=extra_args,
                                            format=format,
                                            to='json'))['blocks']
        pf.walk(self.a, filter, format, meta)
        # pd.convert_text(text, format='json', to='html')
        # self.a = json.loads(pd.convert_text(text,
        #                                format=format,
        #                                to='json',
        #                                extra_args=extra_args,
        #                                filters=filters))


class FiltersTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(FiltersTests, self).__init__(*args, **kwargs)


populate_filters(FiltersTests, filter_test)
