import sys
from datetime import datetime, date as dt_date, time as dt_time
from whereval import Where, util as wutil

C_ = wutil.C_

# Examples provided from README.md
def main():
    example_1()


def example_1():
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


if __name__ == '__main__':
    main()