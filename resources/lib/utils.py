import re
from collections import namedtuple

SortedDisplay = namedtuple('SortedDisplay', ['sort', 'display'])

def natural_sort(string, naturalsortresplit=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(naturalsortresplit, string)]
