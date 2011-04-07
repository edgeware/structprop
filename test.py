import unittest
from structprop import loads, dumps


class ParserTestCase(unittest.TestCase):

    def test_key_value(self):
        result = loads('key = value')
        self.assertEquals(result['key'], 'value')

    def test_inline_comment(self):
        result = loads('key = value  #comment')
        self.assertEquals(result['key'], 'value')

    def test_quoted_value(self):
        result = loads('key = "a#comment{}=#"')
        self.assertEquals(result['key'], 'a#comment{}=#')

    def test_quoted_key(self):
        result = loads('"key abc" = value')
        self.assertEquals(result['key abc'], 'value')

    def test_empty_object(self):
        result = loads("a {}")
        self.assertEquals(result['a'], {})

    def test_object_key_value(self):
        result = loads("a { key = value }")
        self.assertEquals(result['a']['key'], 'value')

    def test_comment_before_data(self):
        result = loads(u"#xxx\na { key = value }")
        self.assertEquals(result['a']['key'], 'value')

    def test_dump_list(self):
        data = dumps({'a': ['a', 'b', 'c']})
        self.assertEquals(data, """\
a = {
  a
  b
  c
}
""")

    def test_dump_dict(self):
        data = dumps({'a': {'d': 1}})
        loads(data)
        self.assertEquals(data, """\
a {
  d = 1
}
""")

    def test_escape_space(self):
        data = dumps({'a b': 1})
        loads(data)
        self.assertEquals(data, """\
"a b" = 1
""")

if __name__ == '__main__':
    unittest.main()
