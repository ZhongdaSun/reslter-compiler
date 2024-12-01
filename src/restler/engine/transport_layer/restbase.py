class BaseResult:
    __slots__ = ['_code', '_message', '_method', '_value']
    _code: int
    _message: str
    _method: int
    _value: str

    def __init__(self):
        self._code = 200
        self._message = ''
        self._method = 20
        self._value = ''
"""
1. 读配置
2. 对返回值的判断

1. jason + excel 数据拼凑
2. return， json + expected result()
值，
数据库
"""