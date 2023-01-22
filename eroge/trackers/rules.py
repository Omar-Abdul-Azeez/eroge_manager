from datetime import datetime


def now():
    return datetime.utcnow().strftime(FORMAT_TIME)


FORMAT_TIME = '%Y-%m-%dT%H%M%SZ'
PATTERN_TIME = r'\d{4}-\d{2}-\d{2}T\d{6}Z'
_FORMAT_SAVE = '{tracker}{extra}-{TIME}'
_PATTERN_SAVE = '{tracker}{extra}-'f'{PATTERN_TIME}'
PATTERN_GLOBAL = r'^(.+?)-(.+-)?'f'({PATTERN_TIME})$'
