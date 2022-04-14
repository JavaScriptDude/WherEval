#########################################
# .: whereval.py :.
# Tool for parsing SQL like where expressions and evaluating against live data 
# .: Other :.
# Author: Timothy C. Quinn
# Home: https://pypi.org/project/whereval
# Licence: https://github.com/JavaScriptDude/WherEval
#########################################
# SQL Like Where Clause Parsing and Evaluation Against Live Data
# Conditions:
#   AND / OR
# Special Conditions:
#   + : AND
#   | : OR
# Operators:
#  =, !=, <, <=, >, >=, like
# Special Operators:
#   <> : !=
#    ~ : like
# TODO:
# [.] Add support for in (1,2,3) clause
# [.] Add support for between (1, 3) clause
__package__ = __name__

from sqlite3 import Date
import sqlparse, os
from datetime import datetime, date as dt_date, time as dt_time
import whereval.util as util

pc = util.pc

C_ = util.C_

class Spec():
    def __init__(self, spec:dict):
        if not isinstance(spec, dict):
            raise SpecIssue(400,f"spec must be a dict. got: {type(spec)}")

        self.raw_spec = spec

        
        # do not sort these!
        self.sp_vars = []
        self.sp_dtypes = []
        self.sp_allow_null = []
        _legal_types = (bool, int, float, str, dt_time, dt_date, datetime, None)
        def _te(_v): return f"Illegal type passed in spec: {_v}. Legal types are: {_legal_types}"

        for fld, v in spec.items():
            if not util.isAlphaNumUscore(fld):
                raise SpecIssue(401, f"dict keys must be a variable syntax (alpha/num/uscore) only. Got: {fld}")
            
            type_c = None
            allow_null = False
            if isinstance(v, tuple):
                if len(v) != 2:
                    raise SpecIssue(402, "tuple must have two values only <T> and None.")
                
                extra_t = list(set(v) - set( (None,) ) )

                if len(extra_t) != 1:
                    raise SpecIssue(402, f"types tuple must only have one type and None")

                type_c = extra_t[0]
                
                if not type_c in _legal_types:
                    raise SpecIssue(403, _te(type_c))

                allow_null = True

            else:
                if not v in _legal_types:
                    raise SpecIssue(403, _te(v))
                type_c = v

            self.sp_vars.append(fld)
            self.sp_dtypes.append(type_c)
            self.sp_allow_null.append(allow_null)

        # Lock up data
        self.sp_vars = tuple(self.sp_vars)
        self.sp_dtypes = tuple(self.sp_dtypes)
        self.sp_allow_null = tuple(self.sp_allow_null)


    def getInfo(self, var:str) -> tuple:
        iF = self.sp_vars.index(var)
        if iF == -1:
            raise SpecIssue(401, f"FATAL - field '{var}' not found in Where spec fields: {self.sp_vars}")
        return (self.sp_dtypes[iF], self.sp_allow_null[iF])

    def hasVar(self, var):
        return var in self.sp_vars

    def __str__(self):
        sb=['{']
        for i, (k, v) in enumerate(self.raw_spec.items()):
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

    def __repr__(self):
        return "<Spec>" & self.__str__()


class Where():

    def __init__(self, **kwargs):
        self.children = []

        cls = self.__class__.__name__
    
        if cls == 'Where':
            self.query = kwargs.get('query', "").strip()
            assert self.query != "", f"query cannot be blank"

            spec = kwargs.get('spec', None)
            debug = kwargs.get('debug', False)
            if isinstance(debug, bool): self.debug = debug

            self.spec = Spec(spec)



            self._query_vars = []

            # duck punch in simplified regexp
            sqlparse.engine.filter_stack.lexer.SQL_REGEX = util.get_sqlparse_regex()

            # Check that there is only one statement
            aStmt = sqlparse.split(self.query)
            assert len(aStmt) == 1,"Only one query statement is allowed!"

            self.query = self.query.strip()
            # pc(f"Raw Query:\n{sqlparse.format(self.query, reindent=True, keyword_case='upper')}")

            self._sqlp = sqlparse.parse(self.query)[0]

            __parse(self)



    def hasVar(self, var):
        return self._get_wher().spec.hasVar(var)

    def addClause(self, var:str, oper:'Operator', val, val_t:'VType'=None):
        wher = self._get_wher()
        assert self.hasVar(var), f"Illegal column in query: {var}"
        wher._reg_query_var(var)
        c = Clause(var, oper, val, self, val_t=val_t)
        self.children.append(c)
        return c

    def addCond(self, cond:'Condition'):
        assert Condition.hasMember(cond, strict=False), f"Invalid condition: {cond}"
        cond = Condition.getMember(cond)
        self.children.append(cond)
        return cond

    def addGroup(self, parent:'Where', is_not:bool=False):
        w = Group(parent=self, is_not=is_not)
        self.children.append(w)
        return w

    def _get_wher(self) -> 'Where':
        o_c = self
        while True:
            if not hasattr(o_c, 'parent'): return o_c
            o_c = o_c.parent

    def _reg_query_var(self, var):
        if var in self._query_vars: return
        self._query_vars.append(var)

    # Returns 3 tuple: (<ok>, <result>, <issues>)
    #   where:
    #      <ok> is boolean. True if no issues detected.
    #      <result> Output of eval. If ok is false, this cannot be trusted
    #      <issues> List( of tuple(<condition>, <EvalIssue>))
    def evaluate(self, data:dict) -> bool:
        global C_
        if not isinstance(data, dict):
            raise EvalExcept(202, f"data must be a dict")

        aIssues = None
        
        # verify that data provides all the needed fields
        missing = list(set(self._query_vars) - set(data.keys()))
        if len(missing) > 0:
            raise EvalExcept(203, f"data passed is missing the following keys: {', '.join(missing)}")

        expr=[]
        for i, o in enumerate(Where.walk(self)):
            if o == self: continue
            if o in ('(',')','not'):
                expr.append(o)

            elif isinstance(o, Condition):
                expr.append(o.value.lower())

            else: # must be Clause
                if not isinstance(o, Clause):
                    raise EvalExcept(201, f"FATAL - Object should be a clause. Got: {type(o)}")
                _ret = o._eval(data)

                if _ret in (True, False):
                    result_use = _ret
                else:
                    (_bOk, _issue) = _ret
                    if aIssues is None: aIssues = []
                    aIssues.append(_issue)
                    result_use = False
                    
                expr.append(str(result_use))

        # Convert Expr to String
        sExpr = ' '.join(expr)

        # analyze expr:
        expr_unique = list(dict.fromkeys(expr))
        missing = list(set(expr_unique) - C_.LEGAL_FINAL_EXPR)

        if len(missing) != 0:
            raise EvalExcept(201, f"FATAL - ILLEGAL Token{'s' if len(missing) > 1 else ''} found in Expression: {', '.join(missing)}. Full Expression: {sExpr}.")

        
        # pc(f"Before eval. sExpr: {sExpr}")

        result = None
        try:
            result = eval(sExpr)
        except Exception as ex:
            raise EvalExcept(201, f"FATAO - Evaluation of expression failed: '{sExpr}'. Error: {ex.args[0]}")

        ok = aIssues is None 

        return (ok, result, aIssues)


    @classmethod
    def walk(cls, cur, depth:int=-1):
        if isinstance(cur, Where):
            if cur.__class__.__name__ == 'Where': depth = 0
            if hasattr(cur, 'is_not') and cur.is_not: yield "not"
            yield "("
            for child in cur.children:
                if isinstance(child, Group):
                    for child2 in cls.walk(child, depth=depth+1):
                        yield child2
                else:
                    yield child

            yield ")"
  
        else:
            yield

        
    def __str__(self):
        sb = []
        for i, o in enumerate(Where.walk(self)):
            if i > 0: sb.append(' ')
            if isinstance(o, Condition): o = o.value
            sb.append(str(o))
        return ''.join(sb)


# Where private methods
__parse = None
def _Where__parse(self):

    wher_cur = self
    _clause_dtype = _clause_allow_null = _ttype_last = _val_last =_val_last_lc = None
    _parens_count = 0
    _clause_tk = []
    _clause_count = 0

    # vars for tracking 'in' or 'between blocks
    # _in_bet_watch: 
    #   -1: off
    #    0: Wait for '('
    #    1: inside / vals only or ')' to close
    _in_bet_watch = -1 
    _in_bet_type = None
    _in_bet_vals = None

    # True if 'not' detected and waiting for '('
    _not_wait = False 
    
    
    def _add_clause(_ttype_c, _val_c, inbet_type:Operator=None):
        nonlocal _clause_tk, wher_cur, _clause_count, _in_bet_type, _in_bet_watch, _in_bet_vals
        if not isinstance(_clause_tk, list):
            raise Exception(f"FATAL - _clause_tk must be list {type(_clause_tk)}")

        if inbet_type: # 'in' or 'between' Clause
            if not inbet_type in (Operator.In, Operator.Between):
                raise Exception(f"FATAL - illegal inbet_type: ({util.getCNStr(inbet_type)}){inbet_type}")
            
            if len(_clause_tk) != 2:
                raise Exception(f"FATAL - _clause_tk length is invalid: ({len(_clause_tk)}. Expecting only two items. _clause_tk: {_clause_tk}")
            (_var, _oper) = _clause_tk

            wher_cur.addClause(_var, inbet_type, _in_bet_vals)
            _in_bet_watch = -1
            _in_bet_type = None
            _in_bet_vals = None

        else:
            if len(_clause_tk) != 4:
                raise Exception(f"FATAL - _clause_tk length is invalid: ({len(_clause_tk)}. Expecting only 4 items. _clause_tk: {_clause_tk}")
            (_var, _oper, _val, _val_t) = _clause_tk

            if _oper == 'like':
                if _val_t != VType.String:
                    raise QueryIssue(306, f"like statements must be followed with a 'String'. Got: {_val_t}")

            elif _oper == '<>':
                _oper = '!='

            _oper_use = Operator.getMember(_oper.lower() if isinstance(_oper, str) else _oper, asrt=True)

            wher_cur.addClause(_var, _oper_use, _val, _val_t)

        _clause_tk = []

        



    for i, tkn in enumerate(self._sqlp.flatten()):

        if tkn.is_whitespace: continue
        (_,_ttype) = os.path.splitext(str(tkn.ttype))
        _ttype = _ttype[1:]
        _val = tkn.normalized
        _val_lc = _val.lower()

        # pc(f"_ttype: {_ttype}, _val: '{_val}'")


        if _in_bet_watch > -1:
            pc()

        if _clause_count >= C_.break_at_clause:
            pc()


        # Normalize
        if _ttype == 'Operator':
            if _val == '+':
                _ttype = 'Keyword'
                _val = 'AND'
            elif _val == '|':
                _ttype = 'Keyword'
                _val = 'OR'

        elif _val_lc in ('not', '!'):
            _val = 'NOT'
            _val_lc = 'not'

        elif _ttype == 'Single': 
            _ttype = 'String'


        if i == 0:
            if not (_ttype == 'Punctuation' and _val == '('):
                raise QueryIssue(302, f"Fist element in query must be a '('")

        else:
            if _not_wait:
                if _val != '(': raise QueryIssue(302, f"'(' must follow a NOT but got: '{_val}'")

            elif _val in ('NULL', 'NONE'):
                _ttype = VType.Null
                _val == VType.Null

            if _in_bet_watch == -1:
                if _val_lc in ('in', 'between'):
                    _in_bet_type = _val_lc
                    _in_bet_watch = 0
                    _in_bet_vals = []

            elif _in_bet_watch == 0:
                if _val != '(': raise QueryIssue(303, f"Only token allowed after {_in_bet_type} is '('. Got: '{_val}'")

            elif _in_bet_watch == 1:
                if _ttype == 'Punctuation' and _val == ',': continue
                if not VType.hasMember(_ttype, strict=False) and _val not in (',', ')'):
                    raise QueryIssue(303, f"Only token allowed after {_in_bet_type} follwoing '(' are values, Null, ',' or ')'. Got: '{_ttype}-{_val}'")

            else:
                raise Exception(f"FATAL - Illegal _in_bet_watch value: '({util.getCNStr(_in_bet_watch)}'")

        # End Normalize


        _val_use = _val
        if not _ttype_last is None: # do some checks
            if _in_bet_watch == -1 and _ttype_last == _ttype and _val_last != VType.Null and not (_val in ('(',')') and _val_last == _val):
                raise QueryIssue(302, f"FATAL - Last TType is same as current TType: {_ttype}")
        if _val_lc == 'not':
            _not_wait = True

        elif _ttype == 'Name': # Variable
            if i > 0 and not _val_last_lc in ('(', 'and', 'or'):
                raise QueryIssue(302, f"Name fields can only be the first in expression or following a '(' -or- keyword (and, or).")

            if not self.hasVar(_val):
                raise QueryIssue(301, f"Invalid variable: {_val}. Valid variables: {self.spec.sp_vars}")

            try:
                (_clause_dtype, _clause_allow_null) = self.spec.getInfo(_val)
            except SpecIssue as ex:
                raise QueryIssue(301, f"Field ({_val}) not found in spec. Error: {ex.args[0]}")

            _clause_tk.append(_val)


        elif _ttype == 'Comparison':
            if _ttype_last != 'Name':
                raise QueryIssue(302, f"Comparisions must follow a Name. Last entry: {_ttype_last}-{_val_last}")
            if _val == '<>': _val = '!='
            if _val == '~': _val = 'like'
            if not Operator.hasMember(_val, strict=False): 
                raise QueryIssue(304, f"Invalid Condition '{_val}'. Allowed: {Operator.values()}.")
            _clause_tk.append(_val)


        elif _ttype == VType.String.value: # String value
            _val_use = _val_use[1:][:-1]
            _ttype_use = VType.String
            if not _clause_dtype in (str, dt_time, dt_date, datetime):
                raise QueryIssue(310, f"Datatype provided is invalid. Expecting {_clause_dtype.__name__} but got String")

            elif _clause_dtype == dt_time:
                try:
                    _val_use = util.s2Time(_val_use)
                    _ttype_use = VType.Date
                except Exception as ex: 
                    raise QueryIssue(305, (f"Invalid time '{_val_use}'. Expecting format of HH:MM:SS"))

            elif _clause_dtype == dt_date:
                try:
                    try:
                        _val_use = util.s2Date(_val_use)
                        _ttype_use = VType.Date
                    except ValueError as ex:
                        _t = util.s2Datetime(_val_use)
                        _val_use = dt_date(_t.year, _t.month, _t.day)
                        _ttype_use = VType.Date
                except Exception as ex: 
                    raise QueryIssue(305, f"Invalid date string passed ({_val_use}). Please use format '{C_.ANSI_SQL_DATE}'")

            elif _clause_dtype == datetime:
                try:

                    try:
                        _val_use = util.s2Datetime(_val_use)
                        _ttype_use = VType.DateTime
                    except ValueError as ex:
                        _val_use = util.s2Date(_val_use)
                        _ttype_use = VType.Date

                except Exception as ex: 
                    raise QueryIssue(305, f"Invalid date string passed ({_val_use}). Please use format '{C_.ANSI_SQL_DATETIME}'")

            if _in_bet_watch == 1:
                _in_bet_vals.append( (_val_use, _ttype_use,) )
            else:
                _clause_tk.append(_val_use); _clause_tk.append(_ttype_use)


        elif VType.hasMember(_ttype, strict=False): # int, Float value
            _ttype_use = _ttype if VType.hasMember(_ttype) else VType.getMember(_ttype, asrt=True)

            if _clause_dtype == bool:
                if not _ttype_use == VType.Integer or not _val_use in ('0', '1'):
                    raise QueryIssue(310, f"Datatype provided is invalid. Expecting boolean 0, or 1 but got {_ttype} - {_val_use}")
            else:
                if not _clause_dtype in (int, float):
                    raise QueryIssue(310, f"Datatype provided is invalid. Expecting {_clause_dtype.__name__} but got {_ttype} - {_val_use}")


            # parse value
            if _ttype_use == VType.Integer:
                try:
                    _val_use = int(_val_use)
                except ValueError as ex:
                    raise QueryIssue(305, f"FATAL - value could not be parsed as int ({_val_use}): {ex.args[0]}")

            elif _ttype_use == VType.Float:
                try:
                    _val_use = float(_val_use)
                except ValueError as ex:
                    raise QueryIssue(305, f"FATAL - value could not be parsed as float ({_val_use}): {ex.args[0]}")


            if _in_bet_watch == 1:
                _in_bet_vals.append( ((VType.Null if _ttype_use == VType.Null else _val_use), _ttype_use,) )
            else:
                _clause_tk.append(_val_use); _clause_tk.append(_ttype_use)


        elif _ttype == 'Keyword':
            if _val_lc == 'between':
                _clause_tk.append(Operator.Between)
                
            elif _val_lc == 'in':
                _clause_tk.append(Operator.In)

            elif _val_lc == 'like':
                _clause_tk.append(Operator.Like)

            elif _val == VType.Null:
                if not (len(_clause_tk) == 2 or _clause_tk[-1:] in ('=', '!=')):
                    raise QueryIssue(302, f"null keyword can only follow a condition = or !=")
                _clause_tk.append(VType.Null); _clause_tk.append(VType.Null); _val_use = VType.Null

            elif _val_lc in ('true', 'false'):
                if _clause_dtype != bool:
                    raise QueryIssue(310, f"Value for clause ({_val_lc}) is not allowed. Required data type is {_clause_dtype}")

                _clause_tk.append(1 if _val_lc == 'true' else 0); _clause_tk.append(VType.Boolean)

            else:

                if not _val in ('AND', 'OR'): raise QueryIssue(302, f"Invalid keyword: {_val}")
                _val_use = _val.lower()
                if _val_last != ')':
                    _add_clause(_val, _ttype)

                wher_cur.addCond(_val)


        elif _ttype == 'Punctuation': 
            if not _val in ('(',')'): raise QueryIssue(302, f"FATAL - Illegal punctuation: {_val}")

            if _in_bet_watch > -1: # Inside 'in' or 'between' clause
                if _val == '(':
                    if _in_bet_watch != 0:
                        raise QueryIssue(303, f"Illegal token. {_val} for '{_in_bet_type}' block. Only tokens allowed within 'tuple' block is values.")
                    _in_bet_watch = 1

                elif _val == ')':
                    if _in_bet_watch != 1:
                        raise Exception(f"FATAL - _in_bet_watch ({_in_bet_watch}) should be 1 but is {_in_bet_watch} at ')' for '{_in_bet_type}' condition.")
                    if not len(_in_bet_vals) > 0: 
                        raise QueryIssue(303, f"A '{_in_bet_type}' must contain one or more values before ')'")

                    _add_clause(_val, _ttype, inbet_type=Operator.getMember(_in_bet_type, asrt=True))
                    

                else:
                    raise QueryIssue(303, f"Illegal punctuation inside '{_in_bet_type}' block: '{_val}'")

            elif _not_wait:
                wher_cur = wher_cur.addGroup(parent=wher_cur, is_not=True)
                _not_wait = False
                _parens_count += 1

            else:
            
                if _val_last and _val == '(' and _val_last == ')':
                    raise QueryIssue(302, "Empty parenthesis are not allowed '()' ")

                if _val == '(':
                    _parens_count += 1
                    if i > 0 and not _val_last in ('(', 'and', 'or'):
                        raise QueryIssue(302, f"Open Parems '(' Can only follow '(', 'AND', or 'OR'.")
                    wher_cur = wher_cur.addGroup(parent=wher_cur)
                    

                else: # ')'
                    _parens_count -= 1
                    if not _val_last == ')':
                        _add_clause(_val, _ttype)
                    wher_cur = wher_cur.parent if hasattr(wher_cur, 'parent') else wher_cur

        elif _ttype == 'Symbol':
            raise QueryIssue(302, f"Symbols are not allowed: {_ttype}, {_val}")


        _ttype_last = _ttype 
        _val_last = _val_use 
        _val_last_lc = _val_last.lower() if isinstance(_val_last, str) else _val_last
    
    if _parens_count != 0: raise QueryIssue(302, f"Unbalanced braces in query: {self.query}. _parens_count = {_parens_count}")


class Group(Where):
    parent:'Where'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parent = kwargs.get('parent', None)
        if not self.parent: 
            raise Exception(f"FATAL - parent must be defined")
        pcls = self.parent.__class__.__name__
        if not pcls in ('Where', 'Group'):
            raise Exception(f"FATAL = parent must be an instance of Where or Group. Got: {pcls}")

        _tmp = kwargs.get('is_not', None)
        if _tmp == True: self.is_not = True


class Clause():
    parent:'Where'
    comp_as_date:bool=False
    def __init__(self, var:str, oper:'Operator', val, parent:Where, val_t:'VType'=None):
        global C_
        if not Operator.hasMember(oper, strict=True):
            raise QueryIssue(309, f"Invalid operator: '{util.getCNStr(oper)}'")

        _legal_vt = (int, float, str, list, dt_time, dt_date, datetime, VType)
        if not isinstance(val, _legal_vt):
            raise QueryIssue(308, f"val param must be one of {_legal_vt}. Got '{util.getCNStr(val)}'")

        self.parent = parent
        self.var = var
        self.oper = oper

        # Get Spec info
        try:
            (_sp_dtype, _sp_allow_null) = self._get_wher().spec.getInfo(var)
        except SpecIssue as ex:
            raise QueryIssue(301, f"Field ({var}) not found in spec. Error: {ex.args[0]}")
            
        self.sp_dtype = _sp_dtype
        self.allow_null = _sp_allow_null

        if C_.break_init:
            pc()

        if val == VType.Null:
            pc()


        b_is_between_in = False
        if oper in (Operator.In, Operator.Between): # in/between: Has tuple of two or more values
            b_is_between_in = True
            if not isinstance(val, list):
                raise QueryIssue(303, f"Fatal - Val must be a list for {oper}. Got: {util.getCNStr(val)}")

            if oper == Operator.Between:
                if len(val) != 2: raise QueryIssue(303, f"'Between' values must have only 2 values: {util.getCNStr(val)}")
                if VType.Null in val: raise QueryIssue(303, f"Null cannot be used for between values")

            _tmp = [None] * len(val)
            for i, (_v_c, _dt_c) in enumerate(val):
                if _v_c == VType.Null:
                    if not self.allow_null:
                        raise QueryIssue(307, f"Values provided ({val}) contains a Null which is not allowed for this field. Please only specify a '{self.sp_dtype}'")
                else:
                    if (self.sp_dtype in (int, float,) and not _dt_c in (VType.Integer, VType.Float)):
                            raise QueryIssue(308, f"Values provided ({val}) contains a {_dt_c} which is not allowed for this field. Please only specify a '{self.sp_dtype}'")

                _tmp[i] = _v_c

            self.values = _tmp

        else:
            self.val = val
            if val == VType.Null and not self.allow_null:
                raise QueryIssue(307, f"VType given is Null which is not allowed for this field. Please only specify a '{self.sp_dtype}'")

        def _ers_h(): return f"Column {var} requires {self.sp_dtype.__name__}"
        def _ers(s): return f"{_ers_h()} but value in query could not be parsed.{s}"

        if self.allow_null and val == VType.Null:
            self.val = val
            pc()

        elif self.oper == Operator.Like:
            if self.sp_dtype != str:
                raise QueryIssue(306, _ers(f"{_ers_h()} but like clauses require a string."))
            if val.find('%') == -1: 
                raise QueryIssue(306, f"VType in expression for column {var} must contain one or more % characters.")


    # if Ok, returns <bool>, If not ok returns 2 tuple: (<ok>, <msg>)

    def _eval(self, data):
        d_val=None

        wher = self._get_wher()
        try:
            d_val = data[self.var]
        except Exception as ex:
            return EvalExcept(201, f"Variable {self.var} could not be retrieved from data provided: {data}")
        
        d_dtype = type(d_val)

        if self.oper in (Operator.In, Operator.Between):
            _val_use = self.values
        else:
            _val_use = self.val

        if C_.break_eval:
            pc()

        try:

            # Check data and return if False if not matching spec
            if d_val == None and not self.allow_null:
                return (False, EvalIssue(101, f"WARNING - Specified dtype for field {self.var} does not allow None, but got None in data."))

            if self.comp_as_date: 
                # Datetime value in data to be converted to date for comparison
                #  because the expression had a date instead of datetime
                d_val = dt_date(d_val.year, d_val.month, d_val.day)
                d_dtype = dt_date

            elif d_dtype != self.sp_dtype:
                if d_dtype in (dt_date, datetime) and self.sp_dtype in (dt_date, datetime):
                    if self.sp_dtype == datetime:
                        d_val = datetime(d_val.year, d_val.month, d_val.day, 0, 0, 0)
                        d_dtype = datetime
                    else:
                        d_val = dt_date(d_val.year, d_val.month, d_val.day)
                        d_dtype = dt_date

                elif (d_dtype in (int, float) and self.sp_dtype in (int, float)):
                    pass # Be flexible here

                else:
                    return (False, EvalIssue(102, f"WARNING - Specified dtype for field {self.var} is {self.sp_dtype} but got '({d_dtype}) {d_val}' in data."))

            # Actual evaluations

            def _fixDate(l, r):
                dt_l = type(l); dt_r = type(r)
                if dt_l == dt_date and dt_r == datetime:
                    r = dt_date(r.year, r.month, r.day)

                elif dt_l == datetime and dt_r == dt_date:
                    l = dt_date(l.year, l.month, l.day)
                return (l,r)

            
            if self.oper == Operator.In:
                # _val_use is a 2+ tuple
                if d_val is None: return (VType.Null in _val_use)
                for v_r in _val_use:
                    (v_l, v_r) = _fixDate(d_val, v_r)
                    if v_l == v_r: return True

                return False


            elif self.oper == Operator.Between:
                # _val_use is a 2 tuple
                (v_l, v_r) = _fixDate(d_val, _val_use[0])
                b1 = v_l >= v_r
                (v_l, v_r) = _fixDate(d_val, _val_use[1])
                b2 = v_l <= v_r
                return (b1 and b2)

            else:

                (v_l, v_r) = _fixDate(d_val, _val_use)

                if   self.oper == Operator.Equals:
                    if self.sp_dtype == bool:
                        if not v_l in (True, False):
                            return (False, EvalIssue(103, f"Variable {self.var} must be a boolean. Got '{util.getCNStr(v_l)}'"))

                    if v_r == VType.Null:
                        return v_l is None
                    return v_l == v_r

                elif self.oper == Operator.NotEquals:
                    return v_l != v_r

                elif self.oper == Operator.LessThan:
                    return v_l < v_r

                elif self.oper == Operator.LessThanOrEqual:
                    return v_l <= v_r

                elif self.oper == Operator.GreaterThan:
                    return v_l > v_r

                elif self.oper == Operator.GreaterThanOrEqual:
                    return v_l >= v_r

                elif self.oper == Operator.Like:
                    if not isinstance(v_r, str):
                        return (False, EvalIssue(104, f"Variable {self.var} must be a string. Got '{util.getCNStr(v_l)}'"))
                    return util.sql_like_match(v_l, v_r)

    
                else:
                    raise Exception(f"FATAL - Unexpected operator: {self.oper}")

        except TypeError as ex:
            raise EvalExcept(201, f"ERROR - Evaluation of expression failed for '{self.__str__()}' with of '{util.getCNStr(d_val)}'. Reason: {ex.args[0]}")


    def _get_wher(self) -> 'Where':
        o_c = self.parent
        while True:
            if not hasattr(o_c, 'parent'): return o_c
            o_c = o_c.parent


    def __str__(self):
        _oper = self.oper.value if util.isEnumMember(self.oper) else self.oper
        if _oper in ('in', 'between'):
            _val = '(' + util.join([('null' if _v == VType.Null else _v) for _v in self.values], ', ') + ')'
        else:
            _val = f"'{self.val}'" if self.sp_dtype == str else self.val
        return f"{self.var} {_oper} {_val}"

class WVExceptBase(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.message = msg
        self.code = code


# EvalIssue codes:
# 101 = None detected but not allowed in spec
# 102 = dtype passed does not match spec dtype
# 103 = Bool expected
# 104 = String expected
class EvalIssue(WVExceptBase):
    def __str__(self):
        return self._repr__()
    def _repr__(self):
        return f"<EvalIssue> code: {self.code}, msg: {self.message}"

# EvalExcept codes:
# 201 = Core Issue
# 202 = Data is not a dict
# 203 = Field Missing In Data
class EvalExcept(WVExceptBase):
    def __str__(self):
        return self._repr__()
    def _repr__(self):
        return f"<EvalExcept> code: {self.code}, msg: {self.message}"


# QueryIssue codes:
# 300 = Core Error
# 301 = Invalid Field
# 302 = Syntax
# 303 = In/Betw Value Tuple Issue
# 304 = Invalid Condition
# 305 = Value Parse Issue
# 306 = Invalid Like Syntax
# 307 = Null / None not allowed
# 308 = Invalid Compare Value Type
# 309 = Invalid Operator
# 310 = Invalid Data Type
class QueryIssue(WVExceptBase):
    def __str__(self):
        return self._repr__()
    def _repr__(self):
        return f"<QueryIssue> code: {self.code}, msg: {self.message}"

# SpecIssue codes:
# 400 = Spec not a Dict
# 401 = Invalid field
# 402 = Invalid Value tuple
# 403 = Invalid type
# 404 = 
# 405 = 
# 406 = 
class SpecIssue(WVExceptBase):
    def __str__(self):
        return self._repr__()
    def _repr__(self):
        return f"<SpecIssue> code: {self.code}, msg: {self.message}"


class Operator(util.SEnum):
    Equals = '='
    NotEquals = '!='
    LessThan = '<'
    LessThanOrEqual = '<='
    GreaterThan = '>'
    GreaterThanOrEqual = '>='
    Like = 'like'
    In = 'in'
    Between = 'between'


class Condition(util.SEnum):
    AND = 'AND'
    OR = 'OR'

class VType(util.SEnum):
    Float = 'Float'
    Integer = 'Integer'
    Boolean = 'Boolean'
    String = 'String'
    Null = 'Null'
    Time = 'Time'
    Date = 'Date'
    DateTime = 'DateTime'

