# Copyright (C) 2011 by Edgeware AB.
# Written by Johan Rydberg <johan.rydberg@gmail.com>,
#            Mikael Langer <mikael.langer@gmail.com>
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


import json


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
        escape = False
        for ch in s:
            if state == 'whitespace':
                if ch == '#':
                    state = 'comment'
                elif ch == '"':
                    escape = False
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
                    #print "YIELD", term
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
    # document: named [document]
    #
    # named: STRING ['='] collection | STRING '=' STRING
    #
    # collection: '{' named* '}' | '{' simple* '}'
    #
    # simple: STRING | collection
    #
    def document(obj, next, token):
        named_list = []
        while token is not EOF:
            named(named_list, next, token)
            obj.update(named_list)
            token = next()

    def value(token):
        try:
            return json.loads(token)
        except ValueError:
            return token

    def named(obj, next, token):
        if not isinstance(token, basestring):
            raise ParserError("term expected, got '%s'" % token)

        _key = token
        token = next()
        if isinstance(token, basestring) and _key.startswith('!'):
            if handler:
                obj.extend(handler(_key, token, 'object').items())
            return token
        elif token is EQ:
            token = next()
            if isinstance(token, basestring):
                obj.append((_key, value(token)))
                return token
        subobj = []
        token = collection(subobj, next, token)

        # If subobj consists of (k, v) tuples, it's translated into a dict
        if all(isinstance(item, tuple) for item in subobj):
            obj.append((_key, dict(subobj)))
        else:
            obj.append((_key, subobj))
        return token

    def collection(obj, next, token):
        if token is not OPEN:
            raise ParserError("'{' expected, got %s" % token)
        token = next()
        if token is CLOSE:
            return token

        lookahead_token = None
        collection_item = named
        if token is OPEN:
            collection_item = simple
        elif not isinstance(token, basestring):
            raise ParserError("term expected, got '%s'" % token)
        if collection_item is named:
            lookahead_token = next()
            if (isinstance(lookahead_token, basestring)):
                collection_item = simple

        def next_token():
            if lookahead_token is not None:
                yield lookahead_token
            while True:
                yield next()

        next_token = next_token().next
        while token != CLOSE:
            collection_item(obj, next_token, token)
            token = next_token()
        return token

    def simple(obj, next, token):
        if isinstance(token, basestring):
            if token.startswith('!'):
                _key = token
                token = next()
                if token is CLOSE:
                    raise ParserError(
                        "expected token, got '}'")
                obj.extend(handler(_key, token, 'value'))
            else:
                obj.append(value(token))
            return token
        subobj = []
        token = collection(subobj, next, token)
        obj.append(subobj)
        return token

    lexer = Lexer()
    tokenizer = lexer.tokenize(s)
    next = tokenizer.next
    token = next()
    result = {}
    document(result, next, token)

    return result


def loads(data, handler=None):
    """Load configuration data from C{data}.

    @param handler: callable or C{None} that will be invoked for
       augmenting an object.  The handler will be passed a term
       that was provided.  The handler must return a C{dict}.

    @return: The configuration data
    @rtype: C{dict}
    """
    if not isinstance(data, unicode):
        data = unicode(data, 'utf-8')
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
        for key, value in d.iteritems():
            if type(value) == dict:
                yield '%s%s {\n' % (' ' * indent, _escape(key))
                for subs in _dump(value, indent + 2):
                    yield subs
                yield '%s}\n' % (' ' * indent)
            elif type(value) == list:
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
