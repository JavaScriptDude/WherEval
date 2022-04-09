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


import sqlparse, os
from datetime import datetime, date as dt_date, time as dt_time, timedelta
import util as util



pc = util.pc

C_ = util.C_


class Where():

    def __init__(self, **kwargs):
        self.children = []

        cls = self.__class__.__name__
    
        if cls == 'Where':
            self.query = kwargs.get('query', "").strip()
            assert self.query != "", f"query cannot be blank"
            self.data_tmpl = kwargs.get('data_tmpl', None)
            assert isinstance(self.data_tmpl, dict), f"data_tmpl must be a dict. got: {type(self.data_tmpl)}"
            # do not sort these!
            self.d_vars = []
            self.d_dtypes = []
            for k, v in self.data_tmpl.items():
                assert util.isAlphaNumUscore(k), f"dict keys must be a variable syntax (alpha/num/uscore) only. Got: {k}"
                self.d_vars.append(k)
                self.d_dtypes.append(type(v))

            self._query_vars = []

            # Check that there is only one statement
            aStmt = sqlparse.split(self.query)
            assert len(aStmt) == 1,"Only one query statement is allowed!"

            self.query = self.query.strip()
            # pc(f"Raw Query:\n{sqlparse.format(self.query, reindent=True, keyword_case='upper')}")

            self._sqlp = sqlparse.parse(self.query)[0]

            __parse(self)

            # Lock in after parse
            self.d_vars = tuple(self.d_vars)
            self.d_dtypes = tuple(self.d_dtypes)


    def addClause(self, var:str, oper:'Operator', val):
        wher = self._get_top()
        assert var in wher.d_vars, f"Illegal column in query: {var}"
        wher._reg_query_var(var)
        c = Clause(var, oper, val, self)
        self.children.append(c)
        return c

    def addCond(self, cond:'Condition'):
        assert Condition.hasMember(cond, strict=False), f"Invalid condition: {cond}"
        cond = Condition.getMember(cond)
        self.children.append(cond)
        return cond

    def addGroup(self, parent:'Where'):
        w = Group(parent=self)
        self.children.append(w)
        return w

    def _get_top(self) -> 'Where':
        o_c = self
        while True:
            if not hasattr(o_c, 'parent'): return o_c
            o_c = o_c.parent

    def _reg_query_var(self, var):
        if var in self._query_vars: return
        self._query_vars.append(var)


    def evaluate(self, data:dict) -> bool:
        global C_
        assert isinstance(data, dict), f"data must be a dict"
        
        # verify that data provides all the needed fields
        missing = list(set(self._query_vars) - set(data.keys()))
        assert len(missing) == 0, f"data passed is missing the following keys: {', '.join(missing)}"

        expr=[]
        for i, o in enumerate(Where.walk(self)):
            if o == self: continue
            if o in ('(',')'):
                expr.append(o)

            elif isinstance(o, Condition):
                expr.append(o.value.lower())

            else: # must be Clause
                assert isinstance(o, Clause), f"FATAL - Object should be a clause. Got: {type(o)}"
                b = o.evaluate(data)
                expr.append(str(b))

        # Convert Expr to String
        sExpr = ' '.join(expr)

        # analyze expr:
        expr_unique = list(dict.fromkeys(expr))
        missing = list(set(expr_unique) - C_.LEGAL_FINAL_EXPR)

        assert len(missing) == 0, f"ILLEGAL Token{'s' if len(missing) > 1 else ''} found in Expression: {', '.join(missing)}. Full Expression: {sExpr}."

        
        # pc(f"Before eval. sExpr: {sExpr}")

        bRet = None
        try:
            bRet = eval(sExpr)
        except Exception as ex:
            raise Exception(f"Evaluation of expression failed: '{sExpr}'. Error: {ex.args[0]}")

        return bRet


    @classmethod
    def walk(cls, cur, depth:int=-1):
        if isinstance(cur, Where):
            if cur.__class__.__name__ == 'Where': depth = 0
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
    _tt_last = _v_last = None
    _parens_count = 0
    _expr = []
    
    def _build_expr(_ttype_c, _val_c):
        nonlocal _expr, wher_cur
        assert isinstance(_expr, list),f"_expr must be list {type(_expr)}"
        assert len(_expr) == 4, f"_expr must be length of 4 but got {len(_expr)}"
        (_var, _oper, _val, _val_t) = _expr

        if _oper == 'like':
            assert _val_t == 'Single', f"like statements must be followed with a 'Single'. Got: {_val_t}"

        elif _oper == '<>':
            _oper = '!='

        _expr = []

        wher_cur.addClause(_var, _oper, _val)


    for i, tkn in enumerate(self._sqlp.flatten()):
        if tkn.is_whitespace: continue
        (_,_ttype) = os.path.splitext(str(tkn.ttype))
        _ttype = _ttype[1:]
        _val = tkn.normalized
        _val_lc = _val.lower()

        if i == 0:
            assert _ttype == 'Punctuation' and _val == '(',\
                f"Fist element in query must be a '('"
        else:
            if _ttype == 'Operator':
                if _val == '+':
                    _ttype = 'Keyword'
                    _val = 'AND'; _val_lc = _val.lower()
                elif _val == '|':
                    _ttype = 'Keyword'
                    _val = 'OR'; _val_lc = _val.lower()

        _val_use = _val
        if not _tt_last is None: # do some checks
            if _tt_last == _ttype and _v_last.lower() in 'null' and not (_val == '(' and _v_last == _val):
                raise AssertionError(f"FATAL - Last TType is same as current TType: {_ttype}")

        if _ttype == 'Name': # Variable
            assert i == 0 \
                  or (_tt_last == 'Punctuation' and _v_last == '(') \
                  or (_tt_last == 'Keyword'), \
                f"Name fields can only be the first in expression or following a '(' -or- keyword (and, or)."
            assert _val in (self.d_vars),\
                f"Invalid variable: {_val}. Valid variables: {self.d_vars}"

            _expr.append(_val); _val_use = None

        elif _ttype == 'Comparison':
            assert _tt_last == 'Name', f"Comparisions must follow a Name. Last entry: {_tt_last}-{_v_last}"
            if _val == '<>': _val = '!='
            if _val == '~': _val = 'like'
            assert Operator.hasMember(_val, strict=False), f"Invalid Condition '{_val}'. Allowed: {Operator.values()}."
            _expr.append(_val); _val_use = None


        elif _ttype in ('Float', 'Integer', 'Boolean'):
            _expr.append(_val_use); _expr.append(_ttype); _val_use = None


        elif _ttype == 'Single':
            _val_use = _val_use[1:][:-1]
            _expr.append(_val_use); _expr.append(_ttype); _val_use = None


        elif _ttype == 'Keyword':
            if _val_lc == 'null':
                assert len(_expr) == 2 or _expr[-1:] in ('=', '!='), f"null keyword can only follow a condition = or !="
                _expr.append(_val_lc); _expr.append(_ttype); _val_use = None

            else:

                assert _val in ('AND', 'OR'), f"Invalid keyword: {_val}"
                _val_use = _val.lower()
                if _v_last != ')':
                    _build_expr(_val, _ttype)

                wher_cur.addCond(_val)


        elif _ttype == 'Punctuation':
            assert _val in ('(',')'),\
                f"FATA - Illegal punctuation: {_val}"
            
            if _v_last and _val == '(' and _v_last == ')':
                raise AssertionError("Empty parenthesis are not allowed '()' ")

            if _val == '(':
                _parens_count += 1
                if i > 0 and not _v_last in ('(', 'AND', 'OR'):
                    raise AssertionError(f"Open Parems '(' Can only follow '(', 'AND', or 'OR'.")
                wher_cur = wher_cur.addGroup(parent=wher_cur)
                

            else: # ')'
                _parens_count -= 1
                if not _v_last == ')':
                    _build_expr(_val, _ttype)
                wher_cur = wher_cur.parent if hasattr(wher_cur, 'parent') else wher_cur

        elif _ttype == 'Symbol':
            raise Exception(f"Symbols are not allowed: {_ttype}, {_val}")


        _tt_last = _ttype 
        _v_last = _val 
    

    assert _parens_count == 0, "Unbalanced braces in query: {self.query}"


class Group(Where):
    parent:'Where'
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parent = kwargs.get('parent', None)
        assert self.parent, f"parent must be defined"
        pcls = self.parent.__class__.__name__
        assert pcls in ('Where', 'Group'), \
            f"parent must be an instance of Where or Group. Got: {pcls}"


class Clause():
    parent:'Where'
    def __init__(self, var:str, oper:'Operator', val, parent:Where):
        global C_
        assert util.isAlphaNumUscore(var), f"col must be a variable syntax (alpha/num/uscore) only. Got: {var}"
        assert Operator.hasMember(oper, strict=False), f"Invalid operator: {oper}"
        self.parent = parent
        self.var = var
        self.oper = Operator.getMember(oper)
        self.val = val
        # Normalize val as per datatype from template dict
        wher = self._get_top()
        d_vars = wher.d_vars
        iF = d_vars.index(var)
        assert iF > -1, f"FATAL - var {var} not found in Where d_vars: {d_vars}"
        
        self.dtype = wher.d_dtypes[iF]
        def _ers_h(): return f"Column {var} requires {self.dtype.__name__}"
        def _ers(s): return f"{_ers_h()} but value in query could not be parsed.{s}"

        if C_.break_init:
            pc()

        if self.oper == Operator.Like:
            assert self.dtype == str,_ers(f"{_ers_h()} but like clauses require a string.")
            assert val.find('%') > -1, f"Value in expression for column {var} must contain one or more % characters."

        

        if self.dtype == int:
            try:
                try:
                    self.val = int(val)
                except ValueError as ex1:
                    try:
                        self.val = float(val)
                    except ValueError as ex2:
                        raise ex1

            except ValueError as ex: raise ValueError(_ers(f" {ex.args[0]}"))

        elif self.dtype == float:
            try:
                self.val = float(val)

            except ValueError as ex: raise ValueError(_ers(f" {ex.args[0]}"))

        elif self.dtype == bool:
            assert self.oper == Operator.Equals, f"{_ers_h()}, only the operator '=' is allowed. Current operator is '{self.oper.value}'."

            try:
                v = int(val)
                if v not in (0,1):
                    raise ValueError("Must be either 0 or 1")
                self.val = v

            except ValueError as ex: raise ValueError(_ers(f" {ex.args[0]}"))

        elif self.dtype == dt_date:
            try:
                self.val = util.s2Date(val)

            except ValueError as ex: 
                raise ValueError(f"{_ers_h()} but value passed ({val}) is not a date format. Please use '{C_.ANSI_SQL_DATE}'")

        elif self.dtype == dt_time:
            try:
                self.val = util.s2Time(val)

            except ValueError as ex: raise ValueError(_ers(f" {ex.args[0]}"))

        elif self.dtype == datetime:
            try:
                try:
                    self.val = util.s2Datetime(val)
                except ValueError as ex:
                    try:
                        self.val = util.s2Date(val)
                        # switch to using date instead
                        wher.d_dtypes[iF] = self.dtype = dt_date
                    except ValueError as ex2:
                        raise ValueError(f"Date / Datetime is expected but could not be parsed : '{val}'")

            except ValueError as ex: raise ValueError(_ers(f" {ex.args[0]}"))
        

    def evaluate(self, data):
        v=None
        try:
            v = data[self.var]
        except Exception as ex:
            raise Exception(f"Variable {self.var} could not be retrieved from data provided: {data}")
        
        dtype_c = type(v)
        self_val_use = self.val

        if C_.break_eval:
            pc()

        try:

            # Be explicit with booleans
            if dtype_c == bool and self.dtype != bool:
                raise TypeError(f"Data type expected is {self.dtype.__name__} but got a boolean ({v}).")

            if self.dtype == dt_time and dtype_c != dt_time:
                raise TypeError(f"Data type expected is datetime.time but got '({dtype_c}) {v}'.")

            if self.dtype == dt_date:
                if not dtype_c in (dt_date, datetime):
                    raise TypeError(f"Data type expected is date or datetime but got '({dtype_c}) {v}'.")
                if dtype_c == datetime:
                    v = dt_date(v.year, v.month, v.day)

            elif self.dtype == datetime:
                if not dtype_c in (dt_date, datetime):
                    raise TypeError(f"Data type expected is datetime or date but got '({dtype_c}) {v}'.")
                if dtype_c == dt_date:
                    self_val_use = dt_date(self_val_use.year, self_val_use.month, self_val_use.day)


            if   self.oper == Operator.Equals:
                if self.dtype == bool:
                    assert v in (True, False), f"Variable {self.var} must be a boolean. Got '({util.getClassName(v)}) {v}'"
                return v == self_val_use

            elif self.oper == Operator.NotEquals:
                return v != self_val_use

            elif self.oper == Operator.LessThan:
                return v < self_val_use

            elif self.oper == Operator.LessThanOrEqual:
                return v <= self_val_use

            elif self.oper == Operator.GreaterThan:
                return v > self_val_use

            elif self.oper == Operator.GreaterThanOrEqual:
                return v >= self_val_use

            elif self.oper == Operator.Like:
                assert isinstance(self_val_use, str), f"Variable {self.var} must be a string. Got '({util.getClassName(v)}) {v}'"
                return util.sql_like_match(v, self_val_use)
            
            else:
                raise CondEvalError(f"Unexpected operator: {self.oper}")

        except TypeError as ex:
            raise CondEvalError(f"Evaluation of expression failed for '{self.__str__()}' with of '({util.getClassName(v)}) {v}'. Reason: {ex.args[0]}")


    def _get_top(self) -> 'Where':
        o_c = self.parent
        while True:
            if not hasattr(o_c, 'parent'): return o_c
            o_c = o_c.parent



    def __str__(self):
        _oper = self.oper.value if util.isEnumMember(self.oper) else self.oper
        _val = f"'{self.val}'" if self.dtype == str else self.val
        return f"{self.var} {_oper} {_val}"


class CondEvalError(Exception):
    pass



class Operator(util.SEnum):
    Equals = '='
    NotEquals = '!='
    LessThan = '<'
    LessThanOrEqual = '<='
    GreaterThan = '>'
    GreaterThanOrEqual = '>='
    Like = 'like'

class Condition(util.SEnum):
    AND = 'AND'
    OR = 'OR'
