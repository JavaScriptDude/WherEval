import os, sys, re, fnmatch, time, typing, traceback
from datetime import datetime, date as dt_date, time as dt_time
from enum import EnumMeta, Enum, IntEnum, unique

class C_():
    RE_ALPHA_NUM_USCORE=re.compile("^[0-9a-zA-Z_]*$")
    ANSI_SQL_DATE = "%Y-%m-%d"
    ANSI_SQL_DATETIME = "%Y-%m-%d %H:%M:%S"
    ANSI_SQL_TIME = "%H:%M:%S"
    LEGAL_FINAL_EXPR = {'(', ')', 'or', 'and', 'True', 'False', 'not'}
    break_at_clause = -1
    break_init = False
    break_eval = False
   
def pc(*args):
    if len(args) == 0: return
    if len(args) == 1: print(args[0]); return
    a = []
    for i, v in enumerate(args): a.append( ( v if i == 0 or isinstance(v, (int, float, complex, str)) else str(v) ) )
    print( a[0].format(*a[1:]) )

# x-platform date parsing / formatting
def _fixDateFmt(s) -> str:
    return s.replace('%-', '%#') if os.name == 'nt' else s

def dateToStr(d: datetime, fmt: str) -> str:
    return d.strftime(_fixDateFmt(fmt))

def t2Str(d: dt_time) -> str:
    return d.strftime(_fixDateFmt(C_.ANSI_SQL_TIME))

def d2Str(d: dt_date) -> str:
    return d.strftime(_fixDateFmt(C_.ANSI_SQL_DATE))

def dt2Str(d: datetime) -> str:
    return d.strftime(_fixDateFmt(C_.ANSI_SQL_DATETIME))

def s2Time(s:str) -> dt_time:
    dt = datetime.strptime(s, _fixDateFmt(C_.ANSI_SQL_TIME))
    return dt_time(dt.hour, dt.minute, dt.second, dt.microsecond)

def s2Date(s:str) -> dt_date:
    dt = datetime.strptime(s, _fixDateFmt(C_.ANSI_SQL_DATE))
    return dt_date(dt.year, dt.month, dt.day)

def s2Datetime(s:str) -> datetime:
    return datetime.strptime(s, _fixDateFmt(C_.ANSI_SQL_DATETIME))


def isAlphaNumUscore(s:str) -> bool:
    if not isinstance(s, str) or s.strip() == '': return False
    return False if C_.RE_ALPHA_NUM_USCORE.fullmatch(s) is None else True

def sql_like_match(v, patrn) -> bool:
    patrn = patrn.replace('%', '*')
    return fnmatch.fnmatch(v, patrn)

def isEnumClass(o) -> bool:
    return type(o) == EnumMeta

def isEnumMember(o) -> bool:
    return type(o).__class__ == EnumMeta

def getClassName(o):
    if o == None: return None
    return type(o).__name__




# String Enum
class SEnum(Enum):
    @classmethod
    def hasMember(cls, o, strict:bool=True) -> bool:
        if type(o) == str:
            if strict: return False
            return len([m.value for m in cls if m.value == o]) == 1
        else:
            return not o is None and o.__class__ == cls
            
    @classmethod
    def getMember(cls, o, asrt:bool=False):
        a = [m for m in cls if o in (m, m.value) ]
        ret = a[0] if len(a) == 1 else None
        if asrt and ret is None:
            raise AssertionError(f"Value '{o}' not found in Enums - {cls.__name__}")
        return ret

    @classmethod
    def validate(cls, alias:str, o, strict:bool=True):
        assert cls.hasMember(o, strict),\
            f"Argument '{alias}' is not a member of QEnum {cls.__module__}.{type(cls).__name__}. Got: {type(o)}"
        
        return o

    @classmethod
    def values(cls):
        """Returns a list of all the enum values."""
        return list(cls._value2member_map_.keys())

#Int Enum
class IEnum(IntEnum):
    @classmethod
    def hasMember(cls, o, strict:bool=True) -> bool:
        if type(o) == int:
            if strict: return False
            return len([m.value for m in cls if m.value == o]) == 1
        else:
            return not o is None and o.__class__ == cls

    @classmethod
    def getMember(cls, o, asrt:bool=False):
        a = [m for m in cls if o in (m, m.value) ]
        ret = a[0] if len(a) == 1 else None
        if asrt and ret is None:
            raise AssertionError(f"Value '{o}' not found in Enums - {cls.__name__}")
        return ret

    @classmethod
    def validate(cls, alias:str, o, strict:bool=True):
        assert cls.hasMember(o, strict),\
            f"Argument '{alias}' is not a member of QEnum {cls.__module__}.{type(cls).__name__}. Got: {type(o)}"
        
        return o

    @classmethod
    def values(cls):
        """Returns a list of all the enum values."""
        return list(cls._value2member_map_.keys())


class StopWatch:
    def __init__(self):
        self.start()
    def start(self):
        self._startTime = time.time()
    def getStartTime(self):
        return self._startTime
    def elapsed(self, prec=3):
        prec = 3 if prec is None or not isinstance(prec, int) else prec
        diff= time.time() - self._startTime
        return round(diff, prec)

def getCNStr(o):
    return f"({getClassName(o)}) - {str(o)}"


# Universal Join - Works on any types and list or tuples. Calls str() for values
def join(l:typing.Union[list, tuple], s: str) -> str:
    return s.join([str(v) for v in l])

def dumpCurExcept(chain:bool=True):
    ety, ev, etr = sys.exc_info()
    s = ''.join(traceback.format_exception(ety, ev, etr, chain=chain))
    iF = s.find('\n')
    return s[iF+1:] if iF > -1 else s


def pre(s, iChars=2):
    sPad = ' ' * iChars
    iF = s.find('\n')
    if iF == -1:
        return sPad + s
    sb = []
    iFL = 0
    while iF > -1:
        sb.append(sPad + s[iFL:iF])
        iFL = iF + 1
        iF = s.find('\n', iF + 1)
    sb.append('' if iF == len(s) else sPad + s[iFL:])
    return '\n'.join(sb)


# For duckpunching in more simplified keywords
from sqlparse import tokens
def get_sqlparse_regex():

    # All keywords supported by whereval
    KEYWORDS = {
         'AND': tokens.Keyword
        ,'OR': tokens.Keyword
        ,'TRUE': tokens.Keyword
        ,'FALSE': tokens.Keyword
        ,'BETWEEN': tokens.Keyword
        ,'IN': tokens.Keyword
        ,'NULL': tokens.Keyword
        ,'LIKE': tokens.Keyword
    }

    def is_keyword(value):
        val = value.upper()
        return (KEYWORDS.get(val, tokens.Name)), value

    # Source: sqlparse.keywords.py
    # Blocks commented out as needed
    SQL_REGEX = {
        'root': [
            (r'(--|# )\+.*?(\r\n|\r|\n|$)', tokens.Comment.Single.Hint),
            (r'/\*\+[\s\S]*?\*/', tokens.Comment.Multiline.Hint),
            (r'(--|# ).*?(\r\n|\r|\n|$)', tokens.Comment.Single),
            (r'/\*[\s\S]*?\*/', tokens.Comment.Multiline),
            (r'(\r\n|\r|\n)', tokens.Newline),
            (r'\s+?', tokens.Whitespace),
            (r':=', tokens.Assignment),
            (r'::', tokens.Punctuation),
            (r'\*', tokens.Wildcard),
            (r"`(``|[^`])*`", tokens.Name),
            (r"´(´´|[^´])*´", tokens.Name),
            (r'((?<!\S)\$(?:[_A-ZÀ-Ü]\w*)?\$)[\s\S]*?\1', tokens.Literal),
            (r'\?', tokens.Name.Placeholder),
            (r'%(\(\w+\))?s', tokens.Name.Placeholder),
            (r'(?<!\w)[$:?]\w+', tokens.Name.Placeholder),
            (r'\\\w+', tokens.Command),
            (r'(@|##|#)[A-ZÀ-Ü]\w+', tokens.Name),
            (r'[A-ZÀ-Ü]\w*(?=\s*\.)', tokens.Name),  # 'Name'   .
            (r'(?<=\.)[A-ZÀ-Ü]\w*', tokens.Name),  # .'Name'
            (r'[A-ZÀ-Ü]\w*(?=\()', tokens.Name),  # side effect: change kw to func
            (r'-?0x[\dA-F]+', tokens.Number.Hexadecimal),
            (r'-?\d+(\.\d+)?E-?\d+', tokens.Number.Float),
            (r'(?![_A-ZÀ-Ü])-?(\d+(\.\d*)|\.\d+)(?![_A-ZÀ-Ü])',tokens.Number.Float),
            (r'(?![_A-ZÀ-Ü])-?\d+(?![_A-ZÀ-Ü])', tokens.Number.Integer),
            (r"'(''|\\\\|\\'|[^'])*'", tokens.String.Single),
            (r'"(""|\\\\|\\"|[^"])*"', tokens.String.Symbol),
            (r'(""|".*?[^\\]")', tokens.String.Symbol),
            (r'(?<![\w\])])(\[[^\]\[]+\])', tokens.Name),
            (r'[0-9_A-ZÀ-Ü][_$#\w]*', is_keyword),
            (r'[;:()\[\],\.]', tokens.Punctuation),
            (r'[<>=~!]+', tokens.Operator.Comparison),
            (r'[+/@#%^&|^-]+', tokens.Operator),
        ]}

    FLAGS = re.IGNORECASE | re.UNICODE
    SQL_REGEX = [(re.compile(rx, FLAGS).match, tt) for rx, tt in SQL_REGEX['root']]
    return SQL_REGEX
