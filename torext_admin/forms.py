#!/usr/bin/env python
# -*- coding: utf-8 -*-


class _Widget(object):
    def __init__(self, field, value=None,
                 tag='input:text', tag_attrs=None,
                 empty_choice=False, choices=None, choices_wrap=None,
                 label_text=None, label_attrs=None):
        self.field = field
        self.value = value
        self.tag_name = tag
        self.tag_attrs = tag_attrs or {}
        self.empty_choice = empty_choice
        self.choices = choices
        self.choices_wrap = choices_wrap
        self.label_text = label_text
        self.label_attrs = label_attrs or {}

        if 'id' in self.tag_attrs:
            self.label_attrs.setdefault('for', tag_attrs['id'])

    @property
    def name(self):
        return self.field.name

    @property
    def key(self):
        return self.field.key

    def _fix_kwargs(self, kwargs):
        if 'class_' in kwargs:
            kwargs['class'] = kwargs.pop('class_')

    def tag(self, **kwargs):
        self._fix_kwargs(kwargs)
        attrs = self.tag_attrs.copy()
        attrs.update(kwargs)
        return self.make_tag(attrs)

    def label(self, text=None, **kwargs):
        self._fix_kwargs(kwargs)
        if text:
            self.label_text = text
        attrs = self.label_attrs.copy()
        attrs.update(kwargs)
        return self.make_label(attrs)

    def make_tag(self, attrs=None):
        value = self.value
        if isinstance(value, unicode):
            value = value.encode('utf8')
        tag = self.tag_name
        choices = self.choices
        choices_wrap = self.choices_wrap
        buf = []
        if not attrs:
            attrs = {}
        attrs.setdefault('name', self.key)

        if tag.startswith('input'):
            # support 'input:text' format; :password :radio :checkbox :hidden
            if tag.find(':'):
                tag, attrs['type'] = tuple(tag.split(':'))

            if attrs['type'] in ('radio', 'checkbox'):
                choices = list(choices)
                for k, v in choices:
                    if choices_wrap:
                        buf.append(self._left(choices_wrap))
                    id_ = 'id_%s_%s' % (self.key, k)
                    buf.append(self._left('label', {'for': id_}))
                    item_attrs = attrs.copy()
                    item_attrs['value'] = v
                    item_attrs['id'] = id_
                    #print 'value and v', value, v, type(value), type(v), value == v
                    if isinstance(value, bool):
                        if value == _int_to_bool(v):
                            item_attrs['checked'] = 'checked'
                    else:
                        if value is not None and value == v:
                            item_attrs['checked'] = 'checked'
                    buf.append(self._left(tag, item_attrs))
                    buf.append(k)
                    buf.append(self._right('label'))
                    if choices_wrap:
                        buf.append(self._left(choices_wrap))
            else:
                # :text, :password, :hidden
                attrs['value'] = str(value) if not value is None else ''
                # print 'attrs', attrs
                buf.append(self._left(tag, attrs))
        elif tag == 'textarea':
            buf.append(''.join([self._left(tag, attrs), value or '', self._right(tag)]))
        elif tag == 'select':
            buf.append(self._left(tag, attrs))
            if isinstance(value, list):
                value_list = value
            else:
                value_list = []
            if self.empty_choice:
                buf += [self._left('option', {'name': attrs['name'], 'value': ''}),
                        'None', self._right('option')]
            for k, v in choices:
                item_attrs = {
                    'name': attrs['name'],
                    'value': v
                }
                # print 'value and v', value, v, type(v)
                if value == v or v in value_list:
                    item_attrs['selected'] = 'selected'
                buf += [self._left('option', item_attrs),
                        k,
                        self._right('option')]
            buf.append(self._right(tag))
        else:
            raise Exception('Not supported tag: %s' % tag)
        return self._join_buf(buf)

    def make_label(self, attrs=None):
        text = self.label_text or self.key
        # print 'text', text
        if not attrs:
            attrs = {}
        buf = [self._left('label', attrs), text, self._right('label')]
        return self._join_buf(buf)

    def _join_buf(self, buf):
        return '\n'.join(buf)

    def _left(self, tag, attrs=None):
        if attrs is None:
            attrs = {}
        return '<' + tag + ' ' +\
               ' '.join(['%s="%s"' % (k, v)
                        for k, v in attrs.iteritems()]) +\
               '>'

    def _right(self, tag):
        return '</' + tag + '>'

    def __str__(self):
        return self.label() + self.tag()

class BaseForm(object):
    """
    Form is used for:
    1. query form
    2. create form
    3. update form
    """
    Params = None

    sequence = None

    def __init__(self, data=None):
        """
        initialize from valid data
        """
        self.data = data

    @property
    def errors(self):
        return self.params.errors

    # @classmethod
    # def parse(cls, received):
    #     """
    #     parse received data
    #     """
    #     p = cls.Params(**received)
    #     form = cls()
    #     form.params = p
    #     return form

    def __getattr__(self, k):
        if k in self.Params._fields:
            field = self.Params._fields[k]
            value = self.get_value(field.key) if self.data else None
            try:
                widget_maker = self.__getattribute__('widget_' + field.name)
            except AttributeError:
                widget_maker = self._widget
            # print 'widget maker', widget_maker
            return widget_maker(field, value)
        else:
            return self.__getattribute__(k)

    def get_value(self, k):
        return self.data.get(k)

    def _widget(self, field, value=None, **kwargs):
        return _Widget(field, value=value, **kwargs)

    def __iter__(self):
        if self.sequence:
            sequence = self.sequence
        else:
            sequence = self.Params._fields.keys()
        for i in sequence:
            field = self.Params._fields[i]
            value = self.get_value(field.key) if self.data else None
            widget_maker = getattr(self, 'widget_' + field.name, self._widget)
            yield widget_maker(field, value)
