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
                    if not escape:
                        yield ''.join(term)
                        del term[:]
                        state = 'whitespace'
                        continue
                elif ch == '\\':
                    escape = True
                else:
                    if escape:
                        if ch == 'n':
                            term.append('\n')
                        elif ch == 'r':
                            term.append('\r')
                        elif ch == 't':
                            term.append('\t')
                    else:
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


def _parse(s):
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
        if not isinstance(token, basestring):
            raise SyntaxError("term expected", token)
        _key = token
        token = next()
        if token is EQ:
            token = next()
            obj[_key] = value(obj, next, token)
        elif token is OPEN:
            token = next()
            subobj = {}
            while token is not CLOSE:
                token = assignlist(subobj, next, token)
            obj[_key] = subobj
        else:
            raise ParserError("expected '=' or '{' got %r" % token)
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
                _value.append(token)
                token = next()
            return _value
        if not isinstance(token, basestring):
            raise ParserError("expected string token, got %r" % token)
        try:
            return json.loads(token)
        except ValueError:
            return token

    lexer = Lexer()
    tokenizer = lexer.tokenize(s)
    next = tokenizer.next
    token = next()
    result = {}

    stmts(result, next, token)
    return result


def loads(data):
    """Load configuration data from C{data}.

    @return: The configuration data
    @rtype: C{dict}
    """
    if not isinstance(data, unicode):
        data = unicode(data, 'utf-8')
    return _parse(data)


def dumps(data):
    """Dump configuration data to a string.

    @rtype: C{str}
    """
    raise NotImplementedError
