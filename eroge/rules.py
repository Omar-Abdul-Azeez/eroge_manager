from datetime import datetime

format_time = '%Y-%m-%dT%H%M%SZ'
pattern_time = r'\d{4}-\d{2}-\d{2}T\d{6}Z'


def now():
    return datetime.utcnow().strftime(format_time)


def format_save(extra='None'):
    return extra + f'-{now()}'


def pattern_save(extra='None'):
    return extra + f'-{pattern_time}'


pattern_global = r'^(.+)-'f'({pattern_time})$'
