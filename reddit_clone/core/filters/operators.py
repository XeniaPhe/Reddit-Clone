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

BOOLEAN_OPERATORS = (
    EXACT,
    IS_NULL
)

NUMERIC_OPERATORS = (
    EXACT,
    IN,
    GT,
    GTE,
    LT,
    LTE,
    RANGE,
    IS_NULL,
)

STRING_OPERATORS = (
    CONTAINS,
    ICONTAINS,
    ENDS_WITH,
    IENDS_WITH,
    EXACT,
    IEXACT,
    IN,
    GT,
    GTE,
    LT,
    LTE,
    RANGE,
    REGEX,
    IREGEX,
    STARTS_WITH,
    ISTARTS_WITH,
    IS_NULL,
)

ID_OPERATORS = (
    EXACT,
    IN,
    IS_NULL,
)

LIST_OPERATORS = (
    EXACT,
    IS_NULL,
)

DATE_OPERATORS = (
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
    IS_NULL,
)

TIME_OPERATORS = (
    HOUR,
    MINUTE,
    SECOND,
    IS_NULL,
)

DATETIME_OPERATORS = tuple(set(DATE_OPERATORS) | set(TIME_OPERATORS)) + (DATE, TIME)

BOOLEAN_TAKING_OPERATORS = (IS_NULL,)

STRING_TAKING_OPERATORS = (
    CONTAINS,
    ICONTAINS,
    ENDS_WITH,
    IENDS_WITH,
    IEXACT,
    REGEX,
    IREGEX,
    STARTS_WITH,
    ISTARTS_WITH,
)

#values in the dictionary represent the allowed range for the filter, both are inclusive
INTEGER_TAKING_OPERATORS = {
    SECOND: (0, 59),
    MINUTE: (0, 59),
    HOUR: (0, 23),
    DAY: (1, 31),
    WEEK_DAY: (1, 7),
    ISO_WEEK_DAY: (1, 7),
    WEEK: (1, 53),
    MONTH: (1, 12),
    QUARTER: (1, 4),
    YEAR: (0, 9999),
    ISO_YEAR: (0, 9999),
}

DATE_TAKING_OPERATORS = (DATE,)
TIME_TAKING_OPERATORS = (TIME,)
DATETIME_TAKING_OPERATORS = ()

COMPARISON_OPERATORS = (
    EXACT,
    GT,
    GTE,
    LT,
    LTE,
)

SPECIAL_OPERATORS = (
    IN,
    RANGE,
)

ALL_OPERATORS = (
    BOOLEAN_TAKING_OPERATORS +
    STRING_TAKING_OPERATORS +
    tuple(INTEGER_TAKING_OPERATORS.keys()) +
    DATE_TAKING_OPERATORS +
    TIME_TAKING_OPERATORS +
    DATETIME_TAKING_OPERATORS +
    COMPARISON_OPERATORS +
    SPECIAL_OPERATORS
)