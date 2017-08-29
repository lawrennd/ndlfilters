import unittest
import json
import pandocfilters
import pypandoc as pd


filter_test = [{'name': 'animateinline',
              'test_text': '''\\begin{animateinline}[autoplay,loop]{10}
\\includegraphics{test1.png}
\\newframe
\\includegraphics{test2.png}
\\end{animateinline}'''},
               {'name': 'columns',
                'test_text': '''\\begin{columns}
<!-- begin frame -->
There was a cat, I like it.
<!-- end frame -->\\end{columns}'''},
               {'name': 'frame',
                'test_text': '''\\begin{frame}
\\frametitle{Frame Title}
\\begin{itemize}
\\item This is a bullet.
\\end{itemize}
\\end{frame}'''},
               {'name': 'includetalkfile',
                'test_text': '''\\includetalkfile{test_talk.tex}'''
                },
               {'name': 'includecvfile',
                'test_text': '''\\includecvfile{test_cv.tex}'''
                },
               {'name': 'inputdiagram',
                'test_text': '''\\inputdiagram{test_diagram.tex}'''
                },
               {'name': 'only',
                'test_text': '''\\begin{frame}
\\only<1>{This is the first frame}
\\only<2-3>{This is the second and third frame}
\\only<4-5>{Fourth and fifth}
\\only<3>{Only 3}
\\end{frame}'''}]

def gtf_(name, test_text, arg=None, format='latex', extra_args=['-R'], filters=['../../../pandoc/python/myfilter.py']):
    def test_function(self):
        if arg is None:
            tester = FilterTester(test_text, format, extra_args, filters)
        else:
            tester = FilterTester(test_text, format, extra_args, filters, arg)
    
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
    def __init__(self, text, format, extra_args, filters, **kwargs):
        self.kwargs = kwargs
        self.a = json.loads(pd.convert_text(text,
                                       format=format,
                                       to='json',
                                       extra_args=extra_args,
                                       filters=filters))


class FiltersTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(FiltersTests, self).__init__(*args, **kwargs)


populate_filters(FiltersTests, filter_test)
