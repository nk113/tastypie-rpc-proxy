# -*- coding: utf-8 -*-
import re

def logf(data):
    sequence = []
    if isinstance(data, dict):
        sequence = ['%s="%s"' % (key, value,) for key, value in data.iteritems()]
    else:
        sequence = [data]

    return ' '.join(sequence)
