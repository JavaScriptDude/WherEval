import sys, unittest2
from datetime import datetime, time as dt_time, date as dt_date
import texttable as tt
from whereval import Where, util, EvalExcept, EvalIssue, QueryIssue, SpecIssue

# Note - These tests are still WIP

# TESTING TODO:
# [.] Make detailed tests for query parsing
#     [.] Unmatched bracing
#     [.] Functions
#     [.] in/between value syntax
#         [.] 'Between' requires 2 tuple
#         [.] 'In' requires 2+ tuple
#     [.] like 
#     [.] Terse query formatting: (v0>=1+v1<>1+v2=2)|(v3~'asdf%')
#     [.] NOT 
# [.] Analize all error code paths and ensure tests are written for reach.
# [.] Write tests for each data type
# [.] Verify all int / float tests including comparing int to float
# [.] Review hand_tests.py to find good tests to pull in
# [.] Write all positive and negative tests for Null values
#     [.] Null when allowed
#     [.] Null when disallowed
#     [.] Null in between values 
#     [.] Null in 'in' values
#     [.] Null weird location in query


pc = util.pc
C_ = util.C_

tblEvals = None
tblEvals = None
tests_run = 0
tests_failed = 0
break_on_exc = False
break_assert = False

table_show_Pass = False

def _tn(s):
    return f"( {s} )"

class DateTests(unittest2.TestCase):

    # DateTests.test_query_date
    def test_query_date(self):
        global break_on_exc, break_assert

        spec = {'v1': dt_date}
        data={'v1': util.s2Date('2021-03-05')}
        
        # Positive Tests
        name = 'q_date 1'; 
        self._test_eval(name, spec=spec, query="(v1 > '2021-03-04')", data=data, expect=True)

        name = 'q_date 2'; 
        self._test_eval(name, spec=spec, query="(v1 < '2021-03-06')", data=data, expect=True)

        name = 'q_date 3'; 
        self._test_eval(name, spec=spec, query="(v1 < '2021-03-05 12:00:00')", data=data, expect=False)

        name = 'q_date 4'; 
        self._test_eval(name, spec=spec, query="(v1 = '2021-03-05 12:00:00')", data=data, expect=True)

        name = 'q_date 5'; 
        self._test_eval(name, spec=spec, query="(v1 in ('2021-03-05', '2021-03-06'))", data=data, expect=True)

        name = 'q_date 5'; 
        self._test_eval(name, spec=spec, query="(v1 in ('2021-03-04', '2021-03-06'))", data=data, expect=False)

        name = 'q_date 6'; 
        self._test_eval(name, spec=spec, query="(v1 between ('2021-03-04', '2021-03-06'))", data=data, expect=True)

        name = 'q_date 7'; 
        self._test_eval(name, spec=spec, query="(v1 between ('2021-03-06', '2021-03-09'))", data=data, expect=False)




    def test_data_date(self):
        global break_on_exc, break_assert

        spec = {'v1': dt_date}
        query="(v1 > '2021-03-04')"
        # Positive Tests
        name = 'date 1'; 
        self._test_eval(name, spec=spec, query=query, data={'v1': util.s2Date('2021-03-05')}, expect=True)

        name = 'date 2'; 
        self._test_eval(name, spec=spec, query=query, data={'v1': util.s2Date('2021-03-03')}, expect=False)


        name = 'date 3';
        self._test_eval(name, spec=spec, query=query, data={'v1': util.s2Datetime('2021-03-04 13:01:02')}, expect=False)

        name = 'date 4'; 
        self._test_eval(name, spec=spec, query=query, data={'v1': util.s2Datetime('2021-03-04 01:01:02')}, expect=False)

        # Negative Tests
        name = 'date n1'; 
        self._test_eval(name, spec=spec, query=query, data={'v1': 1}, neg_expect=[102])
        
        name = 'date n2'; 
        self._test_eval(name, spec=spec, query=query, data={'v1': False}, neg_expect=[102])

        name = 'date n3'; 
        self._test_eval(name, spec=spec, query=query, data={'v2': False}, exc_expect=203)
        


    def test_query_datetime(self):
        global break_on_exc, break_assert

        spec = {'v1': datetime}
        data={'v1': util.s2Datetime('2021-03-04 13:00:00')}
        
        # Positive Tests
        name = 'q_datetime 1'; 
        self._test_eval(name, spec=spec, query="(v1 > '2021-03-04 10:00:00')", data=data, expect=True)

        name = 'q_datetime 2'; 
        self._test_eval(name, spec=spec, query="(v1 < '2021-03-05 00:00:00')", data=data, expect=True)

        name = 'q_datetime 3'; 
        self._test_eval(name, spec=spec, query="(v1 = '2021-03-04 13:00:00')", data=data, expect=True)

        name = 'q_datetime 4'; 
        self._test_eval(name, spec=spec, query="(v1 != '2021-03-04 13:00:00')", data=data, expect=False)

        name = 'q_datetime 5'; 
        self._test_eval(name, spec=spec, query="(v1 <> '2021-03-04 13:00:00')", data=data, expect=False)

        name = 'q_datetime 6'; 
        self._test_eval(name, spec=spec, query="(v1 >= '2021-03-04 10:00:00')", data=data, expect=True)

        name = 'q_datetime 7'; 
        self._test_eval(name, spec=spec, query="(v1 <= '2021-03-05 00:00:00')", data=data, expect=True)

        name = 'q_datetime 8'; 
        self._test_eval(name, spec=spec, query="(v1 != '2021-03-05 10:00:00')", data=data, expect=True)

        name = 'q_datetime 9'; 
        self._test_eval(name, spec=spec, query="(v1 <> '2021-03-05 10:00:00')", data=data, expect=True)

        name = 'q_datetime 10'; 
        self._test_eval(name, spec=spec, query="(v1 in ('2021-03-04 10:00:00', '2021-03-04 13:00:00'))", data=data, expect=True)

        name = 'q_datetime 11'; 
        self._test_eval(name, spec=spec, query="(v1 in ('2021-03-04 14:00:00', '2021-03-04 15:00:00'))", data=data, expect=False)

        name = 'q_datetime 12'; 
        self._test_eval(name, spec=spec, query="(v1 between ('2021-03-04 10:00:00', '2021-03-04 13:10:00'))", data=data, expect=True)

        name = 'q_datetime 13'; 
        self._test_eval(name, spec=spec, query="(v1 between ('2021-03-04 13:10:00', '2021-03-04 15:00:00'))", data=data, expect=False)


    def test_query_datetime_to_date(self):
        global break_on_exc, break_assert

        spec = {'v1': datetime}
        data={'v1': util.s2Datetime('2021-03-04 13:00:00')}
        
        # Positive Tests
        name = 'q_datetime 1'; 
        # C_.break_init = True
        # C_.break_eval = True
        self._test_eval(name, spec=spec, query="(v1 > '2021-03-04')", data=data, expect=False)

        name = 'q_datetime 2'; 
        self._test_eval(name, spec=spec, query="(v1 > '2021-03-03')", data=data, expect=True)

        name = 'q_datetime 3'; 
        self._test_eval(name, spec=spec, query="(v1 = '2021-03-04')", data=data, expect=True)

        name = 'q_datetime 4'; 
        self._test_eval(name, spec=spec, query="(v1 = '2021-03-03')", data=data, expect=False)

        name = 'q_datetime 5'; 
        self._test_eval(name, spec=spec, query="(v1 <= '2021-03-04')", data=data, expect=True)

        name = 'q_datetime 6'; 
        self._test_eval(name, spec=spec, query="(v1 >= '2021-03-04')", data=data, expect=True)

        name = 'q_datetime 7'; 
        self._test_eval(name, spec=spec, query="(v1 >= '2021-03-05')", data=data, expect=False)

        name = 'q_datetime 8'; 
        self._test_eval(name, spec=spec, query="(v1 != '2021-03-04')", data=data, expect=False)

        name = 'q_datetime 9'; 
        self._test_eval(name, spec=spec, query="(v1 != '2021-03-05')", data=data, expect=True)

        name = 'q_datetime 10'; 
        self._test_eval(name, spec=spec, query="(v1 in ('2021-03-04', '2021-03-05'))", data=data, expect=True)

        name = 'q_datetime 11'; 
        self._test_eval(name, spec=spec, query="(v1 in ('2021-03-03', '2021-03-06'))", data=data, expect=False)

        name = 'q_datetime 12'; 
        self._test_eval(name, spec=spec, query="(v1 between ('2021-03-03', '2021-03-05'))", data=data, expect=True)

        name = 'q_datetime 13'; 
        self._test_eval(name, spec=spec, query="(v1 between ('2021-03-05', '2021-03-06'))", data=data, expect=False)


        # Negative Tests
        name = 'q_datetime n1'; 
        self._test_eval(name, spec=spec, query="(v1 = True)", data=data, exc_expect=310)

        name = 'q_datetime n2'; 
        self._test_eval(name, spec=spec, query="(v1 = 1)", data=data, exc_expect=310)



    @classmethod
    def setUpClass(cls):
        global tblEvals
        tblEvals = tt.Texttable(max_width=200)
        tblEvals.set_cols_align( ['l', 'l', 'l', 'l', 'l'] )
        tblEvals.set_cols_dtype( ['t', 't', 't', 't', 't'] )
        tblEvals.set_deco(tblEvals.VLINES)
        tblEvals.header(['test', 'stat', 'query', 'data', 'msg'])

    @classmethod
    def tearDownClass(cls):
        hd_ft = f"Passed: {tests_run-tests_failed}, Failed: {tests_failed}, Total: {tests_run}"
        pc(f"""
Test Results: {hd_ft}

Query Init Tests:
{tblEvals.draw()}
{'(none)' if len(tblEvals._rows) == 0 else ''}

Test Results: {hd_ft}

UnitTest results:""")


    # neg_expect = tuple(<exc_class>, <exc_code>, [<EvalIssue code>])
    # eg:
    # (ok, result, exc_t, exc_code, ei_codes, data, expect, neg_expect) = \
    #     self._test_eval(name, spec=spec, query=query
    #                 , data={'v1': util.s2Date('2021-03-05')}
    #                 , expect=True)
    def _test_eval(self, name, spec, data, query, expect:bool=False, neg_expect:tuple=None, exc_expect:int=None):
        global tblEvals, tests_run, tests_failed

        tests_run += 1

        wher=exc_str=exc=ok=result=issues=None
        try:
            wher = Where(query=query, spec=spec, debug=True)
        except Exception as ex:
            exc_str = util.dumpCurExcept()
            if break_on_exc:
                pc(exc_str)
            exc = ex

        if not exc:
            
            try:
                (ok, result, issues) = wher.evaluate(data)

            except Exception as ex:
                exc_str = util.dumpCurExcept()
                if break_on_exc:
                    pc(exc_str)
                exc = ex
            

        # Row: 'test', 'stat', 'query', 'data', 'msg'

        _r_ok=_r_result=_r_exc_t=_r_exc_code=ei_codes=ei_summary=row=None
        if exc:
            _r_ok = False
            _r_exc_t = exc.__class__
            _qry = wher.query if wher else query
            if isinstance(exc, (EvalExcept, QueryIssue, SpecIssue)):
                _r_exc_code = exc.code
                if not exc_expect is None:
                    if exc_expect == _r_exc_code:
                        row = [name, 'PASS', _qry, data, f"[NEG]"]
                    else:
                        row = [name, 'FAIL', _qry, data, f"[NEG] - {str(exc)}. Expecting: {exc_expect}"]
                else:
                    row = [name, 'EXCEPT', _qry, data, str(exc)]
            else:
                row = [name, 'EXCEPT', _qry, data, exc_str]


        else: # not exception
            _r_ok = ok
            _r_result = result
            if not ok:
                assert isinstance(issues, list) and len(issues) > 0,\
                    f"Issues must be alist of > = 0 length when result is not ok"
                ei_codes = [issue.code for issue in issues]
                ei_summary = util.join([str(issue) for issue in issues], "\n")

                if ei_codes == neg_expect:
                    row = [name, 'PASS', wher.query, data, f"[NEG] - {ei_summary}"]
                else:
                    row = [name, 'FAIL', wher.query, data, ei_summary]
                    
            else:
                assert issues == None, f"Because eval returned ok, issues must be None. Got: {util.getCNStr(issues)}"

                if neg_expect:
                    row = [name, 'FAIL', wher.query, data, f"Result was ok ({result}) while neg_expect is not None: {util.getCNStr(neg_expect)}"]

                elif exc_expect:
                    row = [name, 'FAIL', wher.query, data, f"Result was ok ({result}) while exc_expect is not None: {util.getCNStr(exc_expect)}"]

                elif result == expect:
                    row = [name, 'PASS', wher.query, data, '-']

                else:
                    row = [name, 'FAIL', wher.query, data, f'Expecting {expect} but got {result}']

        # pc(f"row: {row}")

        msg = util.pre(f"\n{'- '*50}\n( Test: '{name}'\nspec: {spec}\ndata: {data}\nquery: {query}\nexpect: {expect}. result: {result}")
        if break_assert:
            pc()
        
        if exc:
            self.assertIs(result, None, msg=msg + util.pre(f"\nException(s): {exc_str}"))
            if isinstance(exc_expect, int):
                self.assertEquals(exc_expect, _r_exc_code, msg=msg + util.pre(f"\nException(s): {exc_str}"))
            else:
                self.fail("Exception occurred but exc_expect is not specified." + msg + util.pre(f"\nException(s): {exc_str}"))

        else:
            self.assertIs(result, expect, msg=msg)
            self.assertIs(ok, (issues is None), msg=msg + util.pre(f"\nEvalIssues: {ei_codes} - {ei_summary}"))
            if issues:
                self.assertEquals(ei_codes, neg_expect, msg=msg + util.pre(f"\nEvalIssues: {ei_codes} - {ei_summary}"))

        if not table_show_Pass and row[1] == 'PASS':
            pass
        else:
            tblEvals.add_row(row)

        return (
                _r_ok          # Eval processed ok
                ,_r_result      # Result of eval (True, False)
                ,_r_exc_t       # Exc type returned if throw exceptions
                ,_r_exc_code    # Exc code for thrown EvalExcept
                ,ei_codes    # [] of EvalIssue codes
                ,data, expect, neg_expect) # Args passed in


if __name__ == "__main__":
    unittest2.main()
    sys.exit(0)