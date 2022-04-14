from datetime import datetime, date as dt_date, time as dt_time, timedelta
import texttable as tt
from whereval import Where, util, EvalExcept, QueryIssue, SpecIssue

# This file is hand testing.
# written as a starting point for design work.
# Formal testing is being devloped in test_whereval.py using unittest2

pc = util.pc
C_ = util.C_

tblEvals = None
tblQuery = None
tests_run = 0
tests_failed = 0

table_show_Pass = True

def main():
    global tblEvals, tblQuery, tests_run, tests_failed

    if True:
        _init_tables()


        # Query Compile tests:
        test_query_syntax()
        test_query_dates()



        # Eval tests:
        test_str_eq()
        test_int_neq()
        test_int_eq()
        test_int_gteq()
        test_float_gt()
        test_bool()
        test_date()
        test_datetime_gt()
        test_datetime_eq()
        test_datein()
        test_datebetw()
        test_like()

        hd_ft = f"Passed: {tests_run-tests_failed}, Failed: {tests_failed}, Total: {tests_run}"
        pc(f"""
Test Results: {hd_ft}

Query Init Tests:
{tblQuery.draw()}
{'(none)' if len(tblQuery._rows) == 0 else ''}

Eval Tests:
{tblEvals.draw()}
{'(none)' if len(tblEvals._rows) == 0 else ''}

{hd_ft}
        \n""")

    else:

        
        # q = "(f0 >= 1 & f1 <> 1.1 & f2 = 's') or (f3 ~ 'asdf%')"
        # q = "(f0>=1&f1<>1.1&f2='s')|(f3~'asdf%')"
        # q = "(f0 >= 1 and f1 <> 1.1 and f2 = 's') or (f3 like 'asdf%')"
        # q = """(f0 = NULL and f1 != NULL)"""
        # AST:
        # (or [(and [{f0 >= 1}, {f1 <> 1.1}, {f2 == 's'}]), {f3 like 'asdf%'}] )
        # where: Cond: (and|or [])
        #                   Criterion have 2 or more Data
        #        Data: {col expr val}
        


        # spec = {'f0': (int, None),'f1': int,'f2': str,'f3': (str, None)}

        # in / between test
        # q = "(f0 = null and f1 in (1,2,3))"
        # q = "(f1 in (1,2,3))"


        
        def _t(query, spec, data):
            wher = Where(query=query, spec=spec, debug=True)
            pc(f"spec: {str(wher.spec)}")
            pc(f"query: {str(wher)}")
            pc(f"data: {str(data)}")
            (ok, result, issues) = wher.evaluate(data)
            pc(f"After eval: ok: {ok}, result: {result}, issues: {issues}")


        # C_.break_init = True        
        # spec = {'f0': (int, None)}
        # query = "(f0 in (1, None))"
        # C_.break_eval = True
        # _t(query, spec, {'f0': None})
        # _t(query, spec, {'f0': 2})

        # spec = {'f0': int}
        # query = "(f0 in (1, 3, 9))"
        # _t(query, spec, {'f0': 9})

        # Bewteen test
        # spec = {'f0': int}
        # query = "(f0 between (1, 9))"
        # _t(query, spec, {'f0': 3})
        
        # Terse test
        # spec = {'v0':int, 'v1': int, 'v2': int, 'v3': str}
        # query = "(v0>=1+v1<>1+v2=2)|(v3~'asdf%')"
        # _t(query, spec, {'v0': 0, 'v1': 1, 'v2': 3, 'v3': "asdfasdf"})

        # NOT
        # C_.break_eval = True
        # spec = {'v1':int}
        # query = "(not(not(not(not(v1=0)))))"
        # _t(query, spec, {'v1': 0})


        # field: 'source'
        C_.break_eval = True
        spec = {'source':int}
        query = "(not(not(not(not(source=0)))))"
        _t(query, spec, {'source': 0})



        

        # Str test with wrong data
        # C_.break_init = True
        # C_.break_eval = True
        # spec = {'f0': str}
        # query = "(f0 = 'foobar')"
        # _t(query, spec, data={'f0': "foobar"})

        # spec = {'f0': (int, None),'f1': int,'f2': str,'f3': (str, None)}
        # _t({'f0': None, 'f1': 5, 'f2': 's', 'f3': '33'})

        pc()



def test_query_syntax():
    spec = {'v0': int, 'v1': int, 'v2': int, 'v3': str}
    # _tq('q_syntax-braces1', spec=spec, q="((v1 > 1)", exc_expect=302)
    # _tq('q_syntax-braces2', spec=spec, q="(v1 > 1))", exc_expect=302)
    # _tq('q_syntax-func', spec=spec, q="(v1 > upper('a'))", exc_expect=302)
    
    # _tq('q_syntax-betwOper', spec=spec, q="(v1 between (1,3))")
    # _tq('q_syntax-inOper', spec=spec, q="(v1 in (1,2,3))")
    # _tq('q_syntax-terse1', spec=spec, q="(v1>1)")
    # _tq('q_syntax-terse2', spec=spec, q="(v0>=1+v1<>1+v2=2)|(v3~'asdf%')")


def test_query_dates():
    spec = {'v1': dt_date}
    # _tq('q_date1', spec=spec, q="(v1 > '2021-03-04 12:33:01')")
    # _tq('q_date2', spec=spec, q="(v1 > '12:33:01')", exc_expect=999)
    # _tq('q_date3', spec=spec, q="(v1 > 'abc')", exc_expect=999)
    _tq('q_date4', spec=spec, q="(v1 > 1)", exc_expect=310)
    _tq('q_date5', spec=spec, q="(v1 > '2021-03-04')")


    spec = {'v1': datetime}
    _tq('q_datetime1', spec=spec, q="(v1 > '2021-03-04')")
    _tq('q_datetime2', spec=spec, q="(v1 > '12:33:01')", exc_expect=305)
    _tq('q_datetime3', spec=spec, q="(v1 > 1)", exc_expect=310)
    _tq('q_datetime4', spec=spec, q="(v1 > 'abc')", exc_expect=305)
    _tq('q_datetime5', spec=spec, q="(v1 > '2021-03-04 12:33:01')")


    spec = {'v1': dt_time}
    _tq('q_time1', spec=spec, q="(v1 > '2021-03-04')", exc_expect=305)
    _tq('q_time2', spec=spec, q="(v1 > '2021-03-04 12:33:01')", exc_expect=305)
    _tq('q_time3', spec=spec, q="(v1 > 1)", exc_expect=310)
    _tq('q_time4', spec=spec, q="(v1 > 'abc')", exc_expect=305)
    _tq('q_time5', spec=spec, q="(v1 > '11:00:34')")




def test_str_eq():
    q = "(v1 = 'foo')"
    spec = {'v1': str}
    wher = Where(query=q, spec=spec, debug=True)

    _te('str_eq1', q, wher, {'v1': 'bar'}, expect=False)
    _te('str_eq2', q, wher, {'v1': 'foo'}, expect=True)
    _te('str_eq3', q, wher, {'v1': 'baz'}, expect=False)
    _te('str_eq4', q, wher, {'v1': 1}, neg_expect=[102])
    _te('str_eq5', q, wher, {'v1': True}, neg_expect=[102])


def test_int_eq():
    q = "(v1 = 1)"
    spec = {'v1': int}
    wher = Where(query=q, spec=spec, debug=True)

    _te('int_eq1', q, wher, {'v1': 'foo'}, neg_expect=[102])
    _te('int_eq2', q, wher, {'v1': 2}, expect=False)
    _te('int_eq3', q, wher, {'v1': 1}, expect=True)
    _te('int_eq4', q, wher, {'v1': True}, neg_expect=[102])
    _te('int_eq5', q, wher, {'v1': False}, neg_expect=[102])

def test_int_neq():
    q = "(v1 != 1)"
    spec = {'v1': int}
    wher = Where(query=q, spec=spec, debug=True)

    _te('int_neq1', q, wher, {'v1': "foo"}, neg_expect=[102])
    _te('int_neq2', q, wher, {'v1': 2}, expect=True)
    _te('int_neq3', q, wher, {'v1': 1}, expect=False)
    _te('int_neq4', q, wher, {'v1': True}, neg_expect=[102])
    _te('int_neq5', q, wher, {'v1': False}, neg_expect=[102])


def test_int_gteq():
    q = "(v1 >= 2)"
    spec = {'v1': int}
    wher = Where(query=q, spec=spec, debug=True)

    _te('int_neq1', q, wher, {'v1': 3}, expect=True)
    _te('int_neq2', q, wher, {'v1': 5}, expect=True)
    _te('int_neq3', q, wher, {'v1': 1}, expect=False)


def test_float_gt():
    q = "(v1 >= 2.1)"
    spec = {'v1': float}
    wher = Where(query=q, spec=spec, debug=True)

    _te('float_gt1', q, wher, {'v1': 2.4}, expect=True)
    _te('float_gt2', q, wher, {'v1': 3}, expect=True)
    _te('float_gt3', q, wher, {'v1': 4}, expect=True)
    _te('float_gt4', q, wher, {'v1': 2}, expect=False)


    q = "(v1 >= 2.5)"
    spec = {'v1': int}
    wher = Where(query=q, spec=spec, debug=True)

    _te('float_gtb1', q, wher, {'v1': 2.6}, expect=True)
    _te('float_gtb2', q, wher, {'v1': 3}, expect=True)
    _te('float_gtb3', q, wher, {'v1': 2}, expect=False)
    _te('float_gtb4', q, wher, {'v1': 1}, expect=False)
    

def test_bool():
    q = "(v1 = 1)"
    spec = {'v1': bool}
    wher = Where(query=q, spec=spec, debug=True)

    _te('bool1', q, wher, {'v1': True}, expect=True)
    _te('bool2', q, wher, {'v1': False}, expect=False)
    _te('bool3', q, wher, {'v1': 'foo'}, neg_expect=[102])

# MIGRATED
def test_date():
    # Note, because format in query is date, it will store as expecting date
    q = "(v1 > '2021-03-04')"
    spec = {'v1': dt_date}

    # C_.break_init = True
    wher = Where(query=q, spec=spec, debug=True)

    _te('date1', q, wher, {'v1': util.s2Date('2021-03-05')}, expect=True)
    _te('date2', q, wher, {'v1': util.s2Date('2021-03-04')}, expect=False)
    # C_.break_eval = True
    _te('date3', q, wher, {'v1': util.s2Datetime('2021-03-05 02:01:02')}, expect=True)
    _te('date4', q, wher, {'v1': util.s2Datetime('2021-03-04 02:01:02')}, expect=False)


def test_datetime_gt():
    q = "(v1 > '2021-03-04 12:33:01')"
    spec = {'v1': datetime}

    # C_.break_init = True
    wher = Where(query=q, spec=spec)

    _te('datetime_gt2.1', q, wher, {'v1': util.s2Date('2021-03-05')}, expect=True)
    _te('datetime_gt2.2', q, wher, {'v1': util.s2Date('2021-03-04')}, expect=False)
    # C_.break_eval = True
    _te('datetime_gt2.3', q, wher, {'v1': util.s2Datetime('2021-03-04 13:01:02')}, expect=True)
    _te('datetime_gt2.4', q, wher, {'v1': util.s2Datetime('2021-03-04 01:01:02')}, expect=False)


def test_datetime_eq():
    q = "(v1 = '2021-03-04 12:33:01')"
    spec = {'v1': datetime}

    # C_.break_init = True
    wher = Where(query=q, spec=spec)

    # C_.break_eval = True
    _te('datetime_eq1', q, wher, {'v1': util.s2Date('2021-03-04')}, expect=False)
    _te('datetime_eq2', q, wher, {'v1': util.s2Date('2021-03-05')}, expect=False)
    _te('datetime_eq3', q, wher, {'v1': util.s2Datetime('2021-03-04 12:33:01')}, expect=True)
    _te('datetime_eq4', q, wher, {'v1': util.s2Datetime('2021-03-04 12:33:05')}, expect=False)


def test_datein():
    # Note, because format in query is date, it will store as expecting date
    q = "(v1 in ('2021-03-04', '2021-03-06'))"
    spec = {'v1': dt_date}

    # C_.break_init = True
    wher = Where(query=q, spec=spec, debug=True)
    # C_.break_eval = True
    _te('date1', q, wher, {'v1': util.s2Date('2021-03-04')}, expect=True)
    _te('date2', q, wher, {'v1': util.s2Date('2021-03-03')}, expect=False)


def test_datebetw():
    # Note, because format in query is date, it will store as expecting date
    q = "(v1 in ('2021-03-04', '2021-03-06'))"
    spec = {'v1': dt_date}

    # C_.break_init = True
    wher = Where(query=q, spec=spec, debug=True)
    # C_.break_eval = True
    _te('datebetw1', q, wher, {'v1': util.s2Date('2021-03-04')}, expect=True)
    _te('datebetw2', q, wher, {'v1': util.s2Date('2021-03-06')}, expect=True)
    _te('datebetw3', q, wher, {'v1': util.s2Date('2021-03-07')}, expect=False)


def test_like():
    q = "(v1 like '%foo%')"
    spec = {'v1': str}

    # C_.break_init = True
    wher = Where(query=q, spec=spec)

    # C_.break_eval = True
    _te('like1', q, wher, {'v1': 'foobar'}, expect=True)
    _te('like2', q, wher, {'v1': 'bazbar'}, expect=False)
    _te('like3', q, wher, {'v1': 'foobaz'}, expect=True)



def _spec_str(wher, spec):
    if not wher is None:
        assert isinstance(wher, Where),\
            f"spec is not a dict! Got : {util.getCNStr(dict)}"
        return str(wher.spec)
    else:
        assert isinstance(spec, dict),\
            f"spec is not a dict! Got : {util.getCNStr(dict)}"
        sb=['{']
        for i, (k, v) in enumerate(spec.items()):
            if i > 0: sb.append(", ")
            sb.append(k)
            sb.append(': ')
            if isinstance(v, tuple):
                v= f"({util.join( (None if v2 is None else v2.__name__ for v2 in v), ', ')})"
            else:
                v = None if v is None else v.__name__
            sb.append(v)
        sb.append('}')

        return util.join(sb, '')

def _tq(name, q, spec, exc_expect:int=None):
    global tblQuery, tests_run, tests_failed
    err = False
    msg = '-'
    tests_run += 1
    wher = exc = None
    try:
        wher = Where(query=q, spec=spec)
        spec = wher.spec
    except Exception as ex:
        exc_str = util.dumpCurExcept()
        exc = ex

    spec = _spec_str(wher, spec)
    
    row = None
    if exc:
        if isinstance(exc, (QueryIssue, SpecIssue)):
            if not exc_expect is None:
                if exc_expect == exc.code:
                    row = [name, 'PASS', q, spec, '-', f"[NEG]"]
                else:
                    tests_failed += 1
                    row = [name, 'FAIL', q, spec, '-', f"[NEG] - {str(exc)} - Expecting {exc_expect} got: {exc.code}"]
            else:
                tests_failed += 1
                row = [name, 'EXCEPT', q, spec, '-', f"[NEG] - {str(exc)}"]
        else:
            tests_failed += 1
            row = [name, 'EXCEPT', q, spec, '-', exc_str]

    else:
        if exc_expect:
            row = [name, 'FAIL', q, spec, str(wher), f"No error while exc_expect is not None: {util.getCNStr(exc_expect)}"]
            tests_failed += 1
        else:
            row = [name, 'PASS', q, spec, str(wher), '-']

    if not table_show_Pass and row[1] == 'PASS':
        pass
    else:
        tblQuery.add_row(row)


def _te(name, q, wher, data, expect:bool=None, neg_expect:tuple=None, exc_expect:int=None):
    global tblEvals, tests_run, tests_failed
    msg = "-"
    err = False
    b = None
    tests_run += 1
    
    exc_str=exc=None
    try:
        (ok, result, issues) = wher.evaluate(data)
    except Exception as ex:
        exc_str = util.dumpCurExcept()
        exc = ex

    if exc:
        if isinstance(exc, EvalExcept):
            if not exc_expect is None:
                if exc_expect == exc.code:
                    row = [name, 'PASS', wher.query, data, f"[NEG]"]
                else:
                    tests_failed += 1
                    row = [name, 'FAIL', wher.query, data, f"[NEG] - {str(exc)}. Expecting: {exc_expect}"]
            else:
                tests_failed += 1
                row = [name, 'EXCEPT', wher.query, data, f"[NEG] - {str(exc)}"]
        else:
            tests_failed += 1
            row = [name, 'EXCEPT', wher.query, data, exc_str]


    else: # not exception
        if not ok:
            assert isinstance(issues, list) and len(issues) > 0,\
                f"Issues must be alist of > = 0 length when result is not ok"
            ei_codes = [issue.code for issue in issues]
            ei_summary = util.join([str(issue) for issue in issues], "\n")

            if ei_codes == neg_expect:
                row = [name, 'PASS', wher.query, data, f"[NEG] - {ei_summary}"]
            else:
                tests_failed += 1
                row = [name, 'FAIL', wher.query, data, ei_summary]
                
        else:
            assert issues == None, f"Because eval returned ok, issues must be None. Got: {util.getCNStr(issues)}"

            if neg_expect:
                tests_failed += 1
                row = [name, 'FAIL', wher.query, data, f"Result was ok ({result}) while neg_expect is not None. neg_expect: {util.getCNStr(neg_expect)}"]

            elif exc_expect:
                tests_failed += 1
                row = [name, 'FAIL', wher.query, data, f"Result was ok ({result}) while exc_expect is not None. exc_expect: {util.getCNStr(exc_expect)}"]

            elif result == expect:
                row = [name, 'PASS', wher.query, data, '-']
            else:
                tests_failed += 1
                row = [name, 'FAIL', wher.query, data, f'Expecting {expect} but got {result}']

    if not table_show_Pass and row[1] == 'PASS':
        pass
    else:
        tblEvals.add_row(row)

def _init_tables():
    global tblQuery, tblEvals
    tblQuery = tt.Texttable(max_width=200)
    tblQuery.set_cols_align( ['l', 'l', 'l', 'l', 'l', 'l'] )
    tblQuery.set_cols_dtype( ['t', 't', 't', 't', 't', 't'] )
    tblQuery.set_deco(tblQuery.VLINES)
    tblQuery.header(['test', 'stat', 'query', 'spec', 'parsed', 'msg'])


    tblEvals = tt.Texttable(max_width=200)
    tblEvals.set_cols_align( ['l', 'l', 'l', 'l', 'l'] )
    tblEvals.set_cols_dtype( ['t', 't', 't', 't', 't'] )
    tblEvals.set_deco(tblEvals.VLINES)
    tblEvals.header(['test', 'stat', 'query', 'data', 'msg'])

main()