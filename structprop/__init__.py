# Copyright (C) 2011 by Edgeware AB.
# Written by Johan Rydberg <johan.rydberg@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN

from collections import OrderedDict
import json

import six

NEWLINE = (u'NEWLINE',)
EQ = (u'EQ',)
OPEN = (u'OPEN',)
CLOSE = (u'CLOSE',)
EOF = (u'EOF',)


class Lexer:
    """Simple lexer that yields tokens."""

    def __init__(self):
        self.line = 0

    def tokenize(self, s):
        state = 'whitespace'
        self.line = 1
        term = []
        for ch in s:
            if state == 'whitespace':
                if ch == '#':
                    state = 'comment'
                elif ch == '"':
                    state = 'quoted'
                elif ch == ' ' or ch == '\t':
                    pass
                elif ch == '\n':
                    self.line = self.line + 1
                elif ch == '=':
                    yield EQ
                elif ch == '{':
                    yield OPEN
                elif ch == '}':
                    yield CLOSE
                else:
                    term.append(ch)
                    state = 'term'
            elif state == 'quoted':
                if ch == '"':
                    yield ''.join(term)
                    del term[:]
                    state = 'whitespace'
                    continue
                term.append(ch)
            elif state == 'comment':
                if ch == '\n':
                    self.line = self.line + 1
                    state = 'whitespace'
            elif state == 'term':
                if ch in ('#', '\n', ' ', '\t'):
                    yield ''.join(term).strip()
                    del term[:]
                    if ch == '#':
                        state = 'comment'
                    else:
                        state = 'whitespace'
                        if ch == '\n':
                            self.line = self.line + 1
                elif ch in ('=', '{', '}'):
                    yield ''.join(term).strip()
                    del term[:]
                    if ch == '=':
                        yield EQ
                    elif ch == '{':
                        yield OPEN
                    elif ch == '}':
                        yield CLOSE
                    state = 'whitespace'
                else:
                    term.append(ch)
        if state == 'term':
            yield ''.join(term).strip()
        yield EOF


class ParserError(Exception):
    """Parser error."""


def _parse(s, handler):
    """Simple configuration parser."""
    # Our syntax:
    #
    # program: stmts
    #
    # stmts: assignlist
    #
    # assign: STRING '=' value
    #   | STRING '{' assignlist '}'
    #
    # assignlist: assignlist prop
    #   | assign
    #
    # value: STRING
    #   | '{' STRING* '}'
    #
    def stmts(obj, next, token):
        """Process statements until EOF."""
        while token is not EOF:
            token = assignlist(obj, next, token)

    def assign(obj, next, token):
        if not isinstance(token, six.string_types):
            raise ParserError("term expected, got '%s'" % token)
        _key = token
        token = next()
        if _key.startswith('!') and token is not EQ \
                and token is not OPEN \
                and token is not CLOSE:
            if handler:
                obj.update(handler(_key, token, 'object'))
        elif token is EQ:
            token = next()
            obj[_key] = value(obj, next, token)
        elif token is OPEN:
            token = next()
            subobj = OrderedDict()
            while token is not CLOSE:
                token = assignlist(subobj, next, token)
            obj[_key] = subobj
        else:
            raise ParserError("expected '=' or '{' got '%s'" % token)
        return token

    def assignlist(obj, next, token):
        while True:
            assign(obj, next, token)
            token = next()
            if type(token) != str:
                return token

    def value(obj, next, token):
        if token is OPEN:
            token = next()
            _value = []
            while token is not CLOSE:
                if token is OPEN:
                    obj = {}
                    while True:
                        token = next()
                        if token is CLOSE:
                            break
                        assign(obj, next, token)
                    _value.append(obj)
                elif token.startswith('!'):
                    key = token
                    token = next()
                    if token is CLOSE:
                        raise ParserError(
                            "expected token, got '}'")
                    _value.extend(handler(key, token,
                                          'value'))
                else:
                    _value.append(token)
                token = next()
            return _value
        if not isinstance(token, six.string_types):
            raise ParserError("expected string token, got %r" % token)
        try:
            return json.loads(token)
        except ValueError:
            return token

    lexer = Lexer()
    tokenizer = lexer.tokenize(s)

    def pop_token():
        return next(tokenizer)

    token = pop_token()
    result = OrderedDict()

    stmts(result, pop_token, token)
    return result


def loads(data, handler=None):
    """Load configuration data from C{data}.

    @param handler: callable or C{None} that will be invoked for
       augmenting an object.  The handler will be passed a term
       that was provided.  The handler must return a C{dict}.

    @return: The configuration data
    @rtype: C{dict}
    """
    if not isinstance(data, six.text_type):
        data = six.text_type(data, 'utf-8')
    return _parse(data, handler)


_ESCAPE_CHARACTERS = ' \t'


def _escape(k):
    for ch in _ESCAPE_CHARACTERS:
        if ch in k:
            return '"%s"' % (k,)
    return k


def dumps(data):
    """Dump configuration data to a string.

    @rtype: C{str}
    """
    def _dump(d, indent=0):
        for key, value in six.iteritems(d):
            if isinstance(value, dict):
                yield '%s%s {\n' % (' ' * indent, _escape(key))
                for subs in _dump(value, indent + 2):
                    yield subs
                yield '%s}\n' % (' ' * indent)
            elif isinstance(value, list):
                yield '%s%s = {\n' % (' ' * indent, _escape(key))
                for subvalue in value:
                    if type(subvalue) == dict:
                        yield '%s{\n' % (' ' * (indent + 2))
                        for subs in _dump(subvalue, indent + 4):
                            yield subs
                        yield '%s}\n' % (' ' * (indent + 2))
                    else:
                        yield '%s%s\n' % (' ' * (indent + 2),
                                          _escape(subvalue))

                yield '%s}\n' % (' ' * indent)
            elif type(value) == bool:
                yield '%s%s = %s\n' % (' ' * indent, _escape(key),
                                       _escape(str(value).lower()))
            else:
                yield '%s%s = %s\n' % (' ' * indent, _escape(key),
                                       _escape(str(value)))
    return ''.join(list(_dump(data)))
