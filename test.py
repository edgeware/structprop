import unittest
from structprop import loads


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

if __name__ == '__main__':
    unittest.main()
