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
              form=ResourceForm,
              create_form=ResourceCreateForm,
              update_form=ResourceUpdateForm)

# Or

class ResourceAdmin(core.Admin):
    form = ResourceForm
    create_form = ResourceCreateForm
    update_form = ResourceUpdateForm
    table = ResourceTable


## Form

class ResourceForm(core.f.Form):
    Model = Resource

    fields = ['name', 'is_open']
    exclude_fields = ['created']
    required_fields = ['name']

    def process(self, id, params):
        if id is None:
            self.process_create(params)
        else:
            self.process_update(id, params)

    def process_create(self, params):
        ins = self.Model(**params)
        ins.save()

    def process_update(self, id, params):
        self.object_setter(self.object_getter(id), params)

    def object_getter(self, id):
        return self.Model.get(id)

    def object_setter(self, ins, params):
        for k, v in params.iteritems():
            setattr(ins, key, value)
        ins.save()


class ResourceCreateForm(ResourceForm):
    def process_create(self, params):
        ins = self.Model(**params)
        ins.save()


class ResourceUpdateForm(ResourceForm):

    def process_update(self, id, params):
        ins = self.object_getter(id)
        self.object_setter(ins, params)
