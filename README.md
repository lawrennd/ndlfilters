# ndlfliters

This repository contains pandoc filters in python for processing of talks and other latex files into markdown for later use e.g. in reveal slides.

The repository was originally part of `https://github.com/lawrennd/mlprojects`, and was found at `/lawrennd/mlprojects/pandoc`. 

# Test Code

Test code can be run via `nosetests -v filter_tests.py` in the `testing` subfolder.


Filters for processing latex talks. Go to `tex/gpss` and run 
```
pandoc -R -f latex test.tex -F ../../../ndlfilters/myfilter.py -t markdown -o test.md
```

for a test.
