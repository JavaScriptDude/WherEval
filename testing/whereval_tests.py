from datetime import datetime, date as dt_date, time as dt_time, timedelta
import texttable as tt
from whereval import Where, util

# These tests are hand designed for now
# TODO - Move to more automated testing

pc = util.pc
C_ = util.C_

tblEvals = None
tblQuery = None
tests_run = 0
tests_failed = 0

def main():
    global tblEvals, tblQuery, tests_run, tests_failed

    if True:
        tblQuery = tt.Texttable(max_width=200)
        tblQuery.set_cols_align( ['l', 'l', 'l', 'l', 'l', 'l'] )
        tblQuery.set_cols_dtype( ['t', 't', 't', 't', 't', 't'] )
        tblQuery.set_deco(tblQuery.VLINES)
        tblQuery.header(['test', 'stat', 'query', 'data', 'parsed', 'msg'])


        tblEvals = tt.Texttable(max_width=200)
        tblEvals.set_cols_align( ['l', 'l', 'l', 'l', 'l', 'l', 'l'] )
        tblEvals.set_cols_dtype( ['t', 't', 't', 't', 't', 't', 't'] )
        tblEvals.set_deco(tblEvals.VLINES)
        tblEvals.header(['test', 'stat', 'query', 'data', 'expect', 'ret', 'msg'])

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
        test_datetime_gt2()
        test_datetime_eq()
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
        q = "(f0>=1&f1<>1.1&f2='s')|(f3~'asdf%')"
        # q = "(f0 >= 1 and f1 <> 1.1 and f2 = 's') or (f3 like 'asdf%')"
        # q = """(f0 = NULL and f1 != NULL)"""
        # AST:
        # (or [(and [{f0 >= 1}, {f1 <> 1.1}, {f2 == 's'}]), {f3 like 'asdf%'}] )
        # where: Cond: (and|or [])
        #                   Criterion have 2 or more Data
        #        Data: {col expr val}
        data = {'f0': 0,'f1': 1,'f2': 's','f3': 'asdfA'}


        wher = Where(query=q, data_tmpl=data)

        pc(f"Where: {str(wher)}")

        b = wher.evaluate({'f0': 0,'f1': 1,'f2': 's','f3': '33'})

        pc(f"After eval: {b}")



        pc()



def test_query_syntax():
    d = {'v0': 1, 'v1': 1, 'v2': 2, 'v3':'x'}
    # _tq('syntax-braces1', d=d, q="((v1 > 1)", neg=True)
    # _tq('syntax-braces2', d=d, q="(v1 > 1))", neg=True)
    _tq('syntax-func', d=d, q="(v1 > upper('a'))", neg=True)
    _tq('syntax-inOper', d=d, q="(v1 in (1,2,3))", neg=True)
    _tq('syntax-betwOper', d=d, q="(v1 between (1,3))", neg=True)
    
    _tq('syntax-terse1', d=d, q="(v1>1)", neg=False)
    _tq('syntax-terse2', d=d, q="(v0>=1+v1<>1+v2=2)|(v3~'asdf%')", neg=False)


def test_query_dates():
    d = {'v1': util.s2Date('2021-03-04')}
    _tq('date', d=d, q="(v1 > '2021-03-04 12:33:01')", neg=True)
    _tq('date', d=d, q="(v1 > '12:33:01')", neg=True)
    _tq('date', d=d, q="(v1 > 'abc')", neg=True)
    _tq('date', d=d, q="(v1 > 1)", neg=True)
    _tq('date', d=d, q="(v1 > '2021-03-04')", neg=False)


    d = {'v1': datetime.now()}
    _tq('datetime', d=d, q="(v1 > '2021-03-04')", neg=True)
    _tq('datetime', d=d, q="(v1 > '12:33:01')", neg=True)
    _tq('datetime', d=d, q="(v1 > 1)", neg=True)
    _tq('datetime', d=d, q="(v1 > 'abc')", neg=True)
    _tq('datetime', d=d, q="(v1 > '2021-03-04 12:33:01')", neg=False)


    d = {'v1': util.s2Time('12:00:01')}
    _tq('time', d=d, q="(v1 > '2021-03-04')", neg=True)
    _tq('time', d=d, q="(v1 > '2021-03-04 12:33:01')", neg=True)
    _tq('time', d=d, q="(v1 > 1)", neg=True)
    _tq('time', d=d, q="(v1 > 'abc')", neg=True)
    _tq('time', d=d, q="(v1 > '11:00:34')", neg=False)




def test_str_eq():
    n = 'str_eq'
    q = "(v1 = 'foo')"
    tmpl_data = {'v1': 'x'}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': 's'}, expect=False)
    _te(n, q, w, {'v1': 'foo'}, expect=True)
    _te(n, q, w, {'v1': 'bar'}, expect=False)
    _te(n, q, w, {'v1': False}, neg=True)
    _te(n, q, w, {'v1': True}, neg=True)



def test_int_eq():
    n = 'int_eq'
    q = "(v1 = 1)"
    tmpl_data = {'v1': 99}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': 's'}, expect=False)
    _te(n, q, w, {'v1': 2}, expect=False)
    _te(n, q, w, {'v1': 1}, expect=True)
    _te(n, q, w, {'v1': False}, neg=True)
    _te(n, q, w, {'v1': True}, neg=True)

def test_int_neq():
    n = 'int_neq'
    q = "(v1 != 1)"
    tmpl_data = {'v1': 99}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': 's'}, expect=True)
    _te(n, q, w, {'v1': 2}, expect=True)
    _te(n, q, w, {'v1': 1}, expect=False)
    _te(n, q, w, {'v1': False}, neg=True)
    _te(n, q, w, {'v1': True}, neg=True)


def test_int_gteq():
    n = 'int_gteq'
    q = "(v1 >= 2)"
    tmpl_data = {'v1': 99}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': 4}, expect=True)
    _te(n, q, w, {'v1': 2}, expect=True)
    _te(n, q, w, {'v1': 1}, expect=False)


def test_float_gt():
    n = 'float_gt'

    q = "(v1 >= 2)"
    tmpl_data = {'v1': 2.1}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': 4.4}, expect=True)
    _te(n, q, w, {'v1': 3}, expect=True)
    _te(n, q, w, {'v1': 2}, expect=True)
    _te(n, q, w, {'v1': 1}, expect=False)


    q = "(v1 >= 2.5)"
    tmpl_data = {'v1': 2}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': 4.5}, expect=True)
    _te(n, q, w, {'v1': 3}, expect=True)
    _te(n, q, w, {'v1': 2}, expect=False)
    _te(n, q, w, {'v1': 1}, expect=False)
    

def test_bool():
    n = 'bool'
    q = "(v1 = 1)"
    tmpl_data = {'v1': True}
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': True}, expect=True)
    _te(n, q, w, {'v1': False}, expect=False)
    _te(n, q, w, {'v1': 's'}, neg=True)

def test_date():
    # Note, because format in query is date, it will store as expecting date
    n = 'date'
    q = "(v1 > '2021-03-04')"
    tmpl_data = {'v1': datetime.now()}

    # C_.break_init = True
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': util.s2Date('2021-03-05')}, expect=True)
    _te(n, q, w, {'v1': util.s2Date('2021-03-01')}, expect=False)
    # C_.break_eval = True
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-05 12:00:01')}, expect=True)
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-01 22:00:12')}, expect=False)




def test_datetime_gt():
    n = 'datetime'
    q = "(v1 > '2021-03-04 12:33:01')"
    tmpl_data = {'v1': util.s2Date('2021-03-04')}

    C_.break_init = True
    w = Where(query=q, data_tmpl=tmpl_data)

    # _te(n, q, w, {'v1': util.s2Date('2021-03-05')}, expect=True)
    # _te(n, q, w, {'v1': util.s2Date('2021-03-01')}, expect=False)
    C_.break_eval = True
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-04 12:40:01')}, neg=True)
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-04 12:00:12')}, neg=True)

def test_datetime_gt2():
    n = 'datetime'
    q = "(v1 > '2021-03-04 12:33:01')"
    tmpl_data = {'v1': datetime.now()}

    # C_.break_init = True
    w = Where(query=q, data_tmpl=tmpl_data)

    _te(n, q, w, {'v1': util.s2Date('2021-03-05')}, expect=True)
    _te(n, q, w, {'v1': util.s2Date('2021-03-01')}, expect=False)
    # C_.break_eval = True
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-04 12:40:01')}, expect=True)
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-04 12:00:12')}, expect=False)


def test_datetime_eq():
    n = 'datetime'
    q = "(v1 = '2021-03-04 12:33:01')"
    tmpl_data = {'v1': datetime.now()}

    # C_.break_init = True
    w = Where(query=q, data_tmpl=tmpl_data)

    # C_.break_eval = True
    _te(n, q, w, {'v1': util.s2Date('2021-03-04')}, expect=True)
    _te(n, q, w, {'v1': util.s2Date('2021-03-01')}, expect=False)
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-04 12:33:01')}, expect=True)
    _te(n, q, w, {'v1': util.s2Datetime('2021-03-04 12:00:12')}, expect=False)


def test_like():
    n = 'like'
    q = "(v1 like '%foo%')"
    tmpl_data = {'v1': 'xxx'}

    # C_.break_init = True
    w = Where(query=q, data_tmpl=tmpl_data)

    # C_.break_eval = True
    _te(n, q, w, {'v1': 'foobar'}, expect=True)
    _te(n, q, w, {'v1': 'bazbar'}, expect=False)
    _te(n, q, w, {'v1': 'dofoobar'}, expect=True)




def _fix_dates(d):
    for k, v in d.items():
        if isinstance(v, dt_date):
            d[k] = util.d2Str(v)
        elif isinstance(v, datetime):
            d[k] = util.dt2Str(v)
        elif isinstance(v, dt_time):
            d[k] = util.t2Str(v)


def _tq(n, q, d, neg:bool):
    global tblQuery, tests_run, tests_failed
    err = False
    msg = '-'
    tests_run += 1
    whr = None
    try:
        whr = Where(query=q, data_tmpl=d)
    except Exception as ex:
        err = True
        msg = ex.args[0]
    
    _fix_dates(d)
    row = None
    if err:
        if neg:
            row = [n, 'PASS', q, d, '-', f"NEG - {msg}"]
        else:
            tests_failed += 1
            row = [n, 'ERR', q, d, '-', msg]
    else:
        if neg:
            row = [n, 'FAIL', q, d, whr, '-']
        else:
            row = [n, 'PASS', q, d, whr, '-']

    tblQuery.add_row(row)


def _te(n, q, w, d, expect:bool=None, neg:bool=False):
    global tblEvals, tests_run, tests_failed
    msg = "-"
    err = False
    b = None
    tests_run += 1

    try:
        b = w.evaluate(d)
    except Exception as ex:
        msg = ex.args[0]
        err = True

    _fix_dates(d)
    row = None
    if err:
        if neg:
            row = [n, 'PASS', q, d, '-', 'NEG', msg]
        else:
            tests_failed += 1
            row = [n, 'ERR', q, d, expect, '-', msg]
    else:
        if b == expect:
            row = [n, 'PASS', q, d, expect, b, '-']
        else:
            tests_failed += 1
            row = [n, 'FAIL', q, d, expect, b, '-']

    tblEvals.add_row(row)

main()