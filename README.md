# pandoc

Filters for processing latex talks. Go to `tex/gpss` and run 
```
pandoc -R -f latex test.tex -F ../../../pandoc/python/myfilter.py -t markdown -o test.md
```

for a test.
