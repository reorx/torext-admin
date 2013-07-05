#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseTable(object):
    """
    Table is used for:
    1. data showing
    """
    fields = None

    def __init__(self, data):
        self.data = data

    def __iter__(self):
        for i in self.fields:
            if isinstance(i, tuple):
                name, key = i
            else:
                name = key = i
            output_func = getattr(self, 'output_' + name, self.get_value)
            yield name, key, self.format_value(output_func(key))

    def get_value(self, k):
        return self.data.get(k)

    def format_value(self, v):
        if v is None or v is '':
            return '-'
        elif isinstance(v, datetime.datetime):
            return v.strftime('%Y/%m/%d %H:%M:%S')
        elif isinstance(v, list):
            if not v:
                return '-'
            return '\n'.join(['<div class="list_item">%s</div>' % i
                              for i in v])
        else:
            return v

    @classmethod
    def iterfields(cls):
        for i in cls.fields:
            if isinstance(i, tuple):
                name, key = i
            else:
                name = key = i
            yield name, key




