import random
import unittest
from structprop import loads, dumps, ParserError


def handler(stmt, token, context):
    if context == 'value':
        return [token + '.value']
    return {token: 'augmented'}


class ParserTestCase(unittest.TestCase):

    def test_parser_error_on_missing_term(self):
        self.assertRaises(ParserError, loads, '{ = 10')

    def test_key_value(self):
        result = loads('key = value')
        self.assertEquals(result['key'], 'value')

    def test_inline_comment(self):
        result = loads('key = value  #comment')
        self.assertEquals(result['key'], 'value')

    def test_augment_object(self):
        result = loads('!include foo  #comment', handler)
        self.assertTrue('foo' in result)
        self.assertEquals(result['foo'], 'augmented')

    def test_augment_value(self):
        result = loads('a = { !include foo }', handler)
        self.assertTrue(u'foo.value' in result['a'])

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

    def test_nested_objects(self):
        result = loads(u"a = { { b = c } { d = e } def abc }")
        self.assertEquals(len(result), 1)
        self.assertEquals(len(result['a']), 4)
        self.assertEquals(result['a'][2], 'def')
        self.assertEquals(result['a'][3], 'abc')

    def test_true_bool(self):
        result = loads('a = true')
        self.assertTrue(result['a'])

    def test_false_bool(self):
        result = loads('a = false')
        self.assertFalse(result['a'])

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

    def test_dump_true_bool(self):
        data = dumps({'a': True})
        loads(data)
        self.assertEquals(data, """\
a = true
""")

    def test_dump_false_bool(self):
        data = dumps({'a': False})
        loads(data)
        self.assertEquals(data, """\
a = false
""")

    def test_escape_space(self):
        data = dumps({'a b': 1})
        loads(data)
        self.assertEquals(data, """\
"a b" = 1
""")

    def test_object_order_is_kept(self):
        """Verify that the items in objects are kept in order."""
        order = random.sample(range(100), 100)
        string = "\n".join("property%d = %d" % (i, i) for i in order)

        result = loads(string)
        for (key, value), i in zip(result.items(), order):
            self.assertEquals(value, i)

        new_string = dumps(result)
        self.assertEquals(string, str(new_string).rstrip())

if __name__ == '__main__':
    unittest.main()
