CONTAINS = 'contains'
ICONTAINS = 'icontains'
DATE = 'date'
DAY = 'day'
ENDS_WITH = 'endswith'
IENDS_WITH = 'iendswith'
EXACT = 'exact'
IEXACT = 'iexact'
IN = 'in'
IS_NULL = 'isnull'
GT = 'gt'
GTE = 'gte'
HOUR = 'hour'
LT = 'lt'
LTE = 'lte'
MINUTE = 'minute'
MONTH = 'month'
QUARTER = 'quarter'
RANGE = 'range'
REGEX = 'regex'
IREGEX = 'iregex'
SECOND = 'second'
STARTS_WITH = 'startswith'
ISTARTS_WITH = 'istartswith'
TIME = 'time'
WEEK = 'week'
WEEK_DAY = 'week_day'
ISO_WEEK_DAY = 'iso_week_day'
YEAR = 'year'
ISO_YEAR = 'iso_year'

BOOLEAN_OPERATORS = (EXACT,)

NUMERIC_OPERATORS = (
    EXACT,
    IN,
    GT,
    GTE,
    LT,
    LTE,
    RANGE,
)

STRING_OPERATORS = (
    CONTAINS,
    ICONTAINS,
    ENDS_WITH,
    IENDS_WITH,
    EXACT,
    IEXACT,
    IN,
    IS_NULL,
    GT,
    GTE,
    LT,
    LTE,
    RANGE,
    REGEX,
    IREGEX,
    STARTS_WITH,
    ISTARTS_WITH,
)

DATE_OPERATORS = (
    DATE,
    DAY,
    EXACT,
    IN,
    GT,
    GTE,
    LT,
    LTE,
    MONTH,
    QUARTER,
    RANGE,
    WEEK,
    WEEK_DAY,
    ISO_WEEK_DAY,
    YEAR,
    ISO_YEAR,
)

DATETIME_OPERATORS = DATE_OPERATORS + (
    HOUR,
    MINUTE,
    SECOND,
    TIME,
)

ALL_OPERATORS = tuple(set(BOOLEAN_OPERATORS) | set(NUMERIC_OPERATORS) | set(STRING_OPERATORS) | set(DATE_OPERATORS) | set(DATETIME_OPERATORS))