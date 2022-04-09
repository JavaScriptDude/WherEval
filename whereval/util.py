import os, re, fnmatch, time
from datetime import datetime, date as dt_date, time as dt_time
from enum import EnumMeta, Enum, IntEnum, unique

class C_():
    RE_ALPHA_NUM_USCORE=re.compile("^[0-9a-zA-Z_]*$")
    ANSI_SQL_DATE = "%Y-%m-%d"
    ANSI_SQL_DATETIME = "%Y-%m-%d %H:%M:%S"
    ANSI_SQL_TIME = "%H:%M:%S"
    LEGAL_FINAL_EXPR = {'(', ')', 'or', 'and', 'True', 'False'}
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
    def getMember(cls, o):
        a = [m for m in cls if m.value == o]
        return a[0] if len(a) == 1 else None

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
    def getMember(cls, o):
        a = [m for m in cls if m.value == o]
        return a[0] if len(a) == 1 else None

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