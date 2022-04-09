## WherEval

Tool for parsing SQL like where expressions and evaluating against live data 

### Installation

```
python3 -m pip install whereval
```

### API Example

#### (Ex1) Basic Concept:
```python3
from datetime import date
from whereval import Where, util as wutil

print("\n(Ex1) Basic Idea")

sw = wutil.StopWatch()

# Where query (terse example)
qry = "(f0>=2+f1=1+f2='s')|(f3~'foo%')"

# Template for defining data types and fields allowed in query
d_tmpl = {'f0': 0,'f1': True,'f2': 's','f3': 's', 'f4': date(1970,1,1)}

# Instantiate Where
#  - Parses query and uses data to form rules for data types and fields
wher = Where(query=qry, data_tmpl=d_tmpl)

print(f"Query:\n . raw:\t{qry}\n . compiled: {wher}\n\nTests:")
print("Note: Query can be written as ((f0 >= 2 AND f1 = 1 AND f2 = 's') OR (f3 like 'foo%'))")

def _print(w, d, b): print(f"\t{b}\tw/ data: {d}")

# Evaluate expression against real data
dct = {'f0': 2, 'f1': True ,'f2': 's', 'f3': 'foobar'}
_print(wher, dct, wher.evaluate(dct))

# For different data
dct['f3'] = 'bazbar'
_print(wher, dct, wher.evaluate(dct))

# For different data
dct['f0'] = 1
_print(wher, dct, wher.evaluate(dct))

print(f"Completed. Elapsed: {sw.elapsed(3)}s")
```

#### Output of print:
```
(Ex1) Basic Idea
Query:
 . raw:	(f0>=2+f1=1+f2='s')|(f3~'foo%')
 . compiled: ( ( f0 >= 2 AND f1 = 1 AND f2 = 's' ) OR ( f3 like 'foo%' ) )

Tests:
	True	w/ data: {'f0': 2, 'f1': True, 'f2': 's', 'f3': 'foobar'}
	True	w/ data: {'f0': 2, 'f1': True, 'f2': 's', 'f3': 'bazbar'}
	False	w/ data: {'f0': 1, 'f1': True, 'f2': 's', 'f3': 'bazbar'}
Completed. Elapsed: 0.003s
```


### Query Syntax:

```
# Conditions:
#   AND / OR
# Special Conditions:
#   + --> AND
#   | --> OR
# Operators:
#  =, !=, <, <=, >, >=, like
# Special Operators:
#   <> --> !=
#    ~ --> like
```