[![Build Status](https://travis-ci.org/edgeware/structprop.svg?branch=master)](https://travis-ci.org/edgeware/structprop)

Configuration file parser for a somewhat structures properties file
format. (The syntax borrows a lot from [1])

The parser is designed to be as small and simple as possible.

The syntax of the config files should resemble standard properties
(prop = value) with the additional functionality for structuring the
data.  A "structprop" file is an UTF-8 file.

Comments start with `#` and continue until the end of the line.

Line feeds, spaces and tabs are all treated as white space. There are
three special characters; `=`, `{` and `}`.  `=` is used to assign a
value to a property.  `{` and `}` are used to encapsulate structured
data.

Arrays are made up out of simple values enclosed inside a `{}`-pair.
For example (array with values 1, 2 and "abc").

    key = { 1 2 abc }

Since linefeed is like any other whitespace character, the value can
be broken up onto several lines:

    key = {
      1
      2
      abc
    }

The data can be structued into objects (think of it as a hash-map) by
adding a `{}`-pair after the key.  The content of the object is key-value
pairs or other objects.

    name {
      key = value
      what = foo
    }

Keys and values are regular strings that can contain any characters
except the ones mentioned earlier (linefeed, space, tab, #, {, }, =)
provided that the string is not double-quoted.

    key = "a value with a space in it"

The python module contains two functions: `loads` and `dumps`. `loads"
parses a string into a python dictionary. `dumps` writes a structprop
representation of a python dictionary as a string.

`loads` will try to parse values as regular JSON values (the string
`"1"` will become an integer with value `1`).  If it fails, it will leave
the value as a string.

Example:

    # This is a simple example config file
    database {
      hostname = localhost
      username = dbuser
      password = secret
      port = 12361
      database = TheDatabase
    }

    tables = { Table1 Table2 }


[1] https://github.com/matjam/StructuredProperties
