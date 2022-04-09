import sys
from datetime import datetime, date, time
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

    # Template for defining data types and fields allowed in query
    d_tmpl = {'f0': 0,'f1': True,'f2': 's','f3': 's', 'f4': date(1970,1,1)}

    # Instantiate Where
    #  - Parses query and uses data to form rules for data types and fields
    wher = Where(query=qry, data_tmpl=d_tmpl)


    print(f"Query:\n . raw:\t{qry}\n . compiled: {wher}\n\nTests:")

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


if __name__ == '__main__':
    main()