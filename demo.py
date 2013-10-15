#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Resource(core.m.Model):
    name = CharField()
    is_open = BooleanField()
    created = DatetimeField()


# Configs

## Search

class ResourceSearch(core.s.Search):
    __pagi_name__ = 'p'

    name = core.s.CharField()  # No require, all fields are optional
    is_open = core.s.BooleanField()
    created = core.s.DatetimeField(format='%Y-%m-%d')

    def check_created(self, v):
        if v > datetime.datetime.now():
            raise core.s.ValidationError


s = ResourceSearch('/res?p=2&name=a')
s._pagi_num
# 2
s._query
# {'name': 'a'}

cursor = s.search()

## Table

class ResourceTable(core.t.Table):
    fields = [
        ('name', u'名字'),
        ('is_open', u'是否公开'),
        ('created', u'创建时间')
    ]

    def output_name(self, v):
        if len(v) > 10:
            return v[:10] + '...'
        return v

## Final register

core.register(Resource,
              search=ResourceSearch,
              table=ResourceTable,
              create=ResourceCreateForm,
              update=ResourceUpdateForm,
              create_and_update=ResourceForm)

# Or

class ResourceAdmin(core.Admin):
    create_form = ResourceCreateForm
    update_form = ResourceUpdateForm
    create_and_update = ResourceForm
