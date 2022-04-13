## WherEval

Tool for parsing SQL like where expressions and evaluating against live data 

### Installation

```
python3 -m pip install whereval
```

### Inspiration
This tool will scratch an itch I've had for some cli tools where I want to pass complex filter expressions to control output / processing.
For instance with my `histstat` fork, I would like to have better filtering of networking information to be output to sqlite. See: https://github.com/JavaScriptDude/histstat

Another usecase for this is a tool I've wanted to write where I can write a `tail -f` wrapper in python where I can define a filter in cli parameters to limit output to the console. Have not written this yet but its on my todo now that I've got this API.

### API Example

#### (Ex1) Basic Concept:
```python3
from datetime import date
from whereval import Where, util as wutil

print("\n(Ex1) Basic Idea")

sw = wutil.StopWatch()

# Where query (terse example)
qry = "(f0>=2+f1=1+f2='s')|(f3~'foo%')"

# Field and type spec
spec = {'f0': int,'f1': bool,'f2': str,'f3': str, 'f4': dt_date}

# Instantiate Where
#  - Parses query and uses data to form rules for data types and fields
wher = Where(query=qry, spec=spec)


print(f"Query:\n . raw:\t{qry}\n . compiled: {wher}\n\nTests:")

def _print(wher, data, tup): 
	(ok, result, issues) = tup
	if not ok:
		print(f"Eval failed for {wher}. Issues: {issues}")
	else:
		print(f"\t{result}\tw/ data: {data}")

# Evaluate expression against real data
data = {'f0': 2, 'f1': True ,'f2': 's', 'f3': 'foobar'}
_print(wher, data, wher.evaluate(data))

# For different data
data['f3'] = 'bazbar'
_print(wher, data, wher.evaluate(data))

# For different data
data['f0'] = 1
_print(wher, data, wher.evaluate(data))

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
# General:
#  Query must begin with '(' and end with ')'
#  NOT, IN, BETWEEN must be followed by parenthesis '('
# Boolean Operators:
#   AND, OR, NOT
# Equality Operators:
#  =, !=, <, <=, >, >=, like
# Special:
#   !   -->  NOT
#   +   -->  AND
#   |   -->  OR
#   <>  -->  !=
#   ~   -->  like
```