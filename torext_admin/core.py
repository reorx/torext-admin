#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import functools
import logging
import datetime
import urllib
from torext import errors, params, settings
from torext.utils import ObjectDict, _json
from torext.handlers import BaseHandler


PRIVILEGES = {}


str_abbr = lambda x: '..' + str(x)[-5:]


class AdminHandler(BaseHandler):
    """
    Construct project's own base handler class
    """
    EXCEPTION_HANDLERS = {
        errors.AuthenticationNotPass: 'redirect_login',
        (errors.OperationNotAllowed, errors.ParamsInvalidError): 'render_error',
        errors.ObjectNotFound: '_handle_404'
    }

    AUTH_REQUIRED = True

    def prepare(self):
        """
        Because every page requires strict authority of privileges,
        we do authentication using `prepare` method instead of `authenticate` decorator,
        """
        context = {}
        context.setdefault('blackbox', ObjectDict())
        context.setdefault('notice', None)
        context.setdefault('notice_class', 'info')
        context.setdefault('user', getattr(self, 'user', None))
        self.context = context

        if self.AUTH_REQUIRED:
            # currently only `/login` not required
            self.authenticate()
            uri = self.request.uri
            if not self.user.has_access(uri):
                raise errors.OperationNotAllowed('User group has no access to this page')

    def get_template_namespace(self):
        ns = super(BaseHandler, self).get_template_namespace()
        ns.update(
            str_abbr=str_abbr,
            to_json=_json
        )
        return ns

    def redirect_login(self, e):
        self.redirect('/users/login?%s' % urllib.urlencode(dict(next=self.request.uri)))

    def page_redirect(self, notice, notice_class='info', status=None, uri=None):
        if status:
            self.set_status(status)
        self.context.update(
            notice=notice,
            notice_class=notice_class,
            redirect=uri or self.request.uri)
        self.render('redirect.html')

    def error_redirect_back(self, e):
        self.page_redirect(str(e), 'error', 401)

    def render_error(self, e):
        self.context.update(
            notice=str(e),
            notice_class='error')
        if hasattr(self, 'render_page'):
            self.render_page()
        else:
            self.render('base-layout.html')

    def render(self, *args, **kwargs):
        self.context.update(kwargs)
        super(BaseHandler, self).render(*args, **self.context)

    def _handle_404(self, e):
        self.set_status(404)
        self.context.update(
            notice='Not Found',
            notice_class='error')
        self.render('base-layout.html')


class ResourceHandler(BaseHandler):
    @property
    def Model(self):
        raise NotImplementedError

    @property
    def Table(self):
        raise NotImplementedError

    def prepare(self):
        super(ResourceHandler, self).prepare()

        self.parse_arguments()

        cursor = self.get_cursor()

        self.context.update(
            pagi=self.get_pagination(cursor),
            count=cursor.count(),
            items=list(cursor),
            query=self._query,
            sort_query=self._sort_query,
            resource=self.Model.__name__.lower(),
            id_to_update=True,
            Model=self.Model,
            Table=self.Table,
            Form=self.Form)

    def parse_arguments(self):
        current = self.get_argument('p', 1)
        try:
            current = int(current)
            assert current > 0
        except ValueError:
            raise errors.ParamsInvalidError('`p` should be int')
        except AssertionError:
            raise errors.ParamsInvalidError('`p` should be bigger than 0')
        self.current_page = current

        # print 'arguments', self.request.arguments
        self.params = self.Form.Params(**self.request.arguments)
        if self.params.errors:
            raise errors.ParamsInvalidError(self.params)

        self._query = {}
        self._sort_query = {}

        for name, field in self.Form.Params._fields.iteritems():
            if field.key in self.request.arguments:
                v = self.request.arguments[field.key]
                if isinstance(field, params.ListField):
                    self._query[field.key] = v
                else:
                    self._query[field.key] = v[0]

            if field.key + '_sort' in self.request.arguments:
                v = self.request.arguments[field.key + '_sort'][0]
                if not v in ('asc', 'desc'):
                    raise errors.ParamsInvalidError(
                        '%s_sort value should be one of `asc`, `desc`' % field.key)
                self._sort_query[field.key] = v

        # print 'query', self._query
        # print 'sort_query', self._sort_query

    def get_query_args(self):
        return self.params.data

    def get_sort_query_args(self):
        return [(k, 1 if v == 'asc' else -1) for k, v in self._sort_query.iteritems()]

    def get_pagination(self, cursor):
        pagi = ObjectDict()

        base_uri = re.sub('\?p=\d+(&)?', '', self.request.uri)
        base_uri = re.sub('&p=\d+', '', base_uri)
        # print 'base uri with `p`', base_uri
        if re.search('\?\w+=', base_uri):
            base_uri += '&'
        else:
            base_uri += '?'
        count = cursor.count()
        if count == 0:
            total = 1
        else:
            total = (count / settings['RESOURCE_PAGE_LIMIT']) +\
                (1 if count % settings['RESOURCE_PAGE_LIMIT'] else 0)

        pagi.base_uri = base_uri
        pagi.current = self.current_page
        pagi.total = total
        return pagi

    def get_cursor(self):
        query_args = self.get_query_args()
        logging.info('query args: %s', query_args)
        cursor = self.Model.find(query_args)

        # sort
        if self._sort_query:
            sort_query_args = self.get_sort_query_args()
        else:
            sort_query_args = [('_id', -1)]
        logging.info('sort query args: %s', sort_query_args)
        cursor.sort(sort_query_args)
        # skip
        limit = settings['RESOURCE_PAGE_LIMIT']
        skip = self.current_page - 1
        if skip:
            cursor.skip(skip * limit)

        # limit
        cursor.limit(limit)
        return cursor


class ResourceGetHdr(BaseHandler):
    def get(self, id):
        self.doc = self.Model.by__id_str(id)
        self.context.update(
            resource=self.Model.__name__.lower(),
            doc=self.doc,
            extra_data=self.get_extra_data())
        self.render(self.template_name)


def get_doc(Model):
    def decorate(method):
        @functools.wraps(method)
        def wrapper(handler, *args, **kwgs):
            handler.doc = Model.by__id_str(args[0])
            return method(handler, *args, **kwgs)
        return wrapper
    return decorate


def _int_to_bool(v):
    return True if v == 1 else False


def validate_date_with_range(v):
    _search = lambda x: re.search('^' + x + '$', v)
    _datetime = lambda x: datetime.datetime.strptime(x, '%Y/%m/%d')
    ptn = '(\w{4}/\w{2}/\w{2})'
    match_single = _search(ptn)
    match_gt = _search(ptn + '~')
    match_lt = _search('~' + ptn)
    match_range = _search(ptn + '~' + ptn)

    if match_single:
        return _datetime(match_single.groups()[0])
    elif match_gt:
        return {'$gt': _datetime(match_gt.groups()[0])}
    elif match_lt:
        return {'$lt': _datetime(match_lt.groups()[0])}
    elif match_range:
        gt, lt = match_range.groups()
        return {'$gt': gt, '$lt': lt}
    else:
        raise errors.ValidationError('Invalid date format')
