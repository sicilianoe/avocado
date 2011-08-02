from exceptions import Exception
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.utils.encoding import force_unicode
from avocado.utils import loader
from avocado.conf import settings
DATA_CHOICES_MAP = settings.DATA_CHOICES_MAP

def noop(k, v, d, p, **x): return v

class Formatter(object):
    """Provides support for the core data formats with sensible defaults
    for handling converting Python datatypes to their formatted equivalent.

    Each core format method must return one of the following:
        Single formatted Value
        OrderedDict/sequence of key-value pairs

        If ta format method is unable to do either of these for the given
        value a FormatException must be raised.

        ``values`` - an OrderedDict containing each value along with the field
        instance it represents.

        ::

            values = OrderedDict({
                'first_name': {
                    'name': 'First Name',
                    'value': 'Bob',
                    'definition': <Definition "First Name">),
                },
                'last_name': {
                    'name': 'Last Name',
                    'value': 'Smith',
                    'definition': <Definition "Last Name">),
                },
            })

    """
    name = ''

    def __call__(self, values, concept, preferred_formats=None, **context):
        preferred_formats = preferred_formats or ['raw']

        if len(values) == 0:
            raise ValueError, 'no values supplied'

        out = values.copy()

        for key, data in values.iteritems():
            name = data['name']
            value = data['value']
            definition = data['definition']

            fdd = data.copy()
            for f in preferred_formats:
                method = getattr(self, 'to_%s' % f, noop)

                if getattr(method, 'process_multiple', False):
                    try:
                        fdata = self.process_multiple_values(method, values,
                                concepts, **context)
                        if not isinstance(fdata, OrderedDict):
                            out.update(fdata)
                        else:
                            out = fdata
                        return out

                    except Exception:
                        continue
                try:
                    fdata = method(name, value, definition, concept, **context)
                    break
                except Exception:
                    continue


            if type(fdata) is dict:
                fdd.update(fdata)
            # assume single value 
            else:
                fdd['value'] = fdata

            out[key] = fdd

        return out

    def __contains__(self, choice):
        return hasattr(self, 'to_%s' % choice)

    def __unicode__(self):
        return u'%s' % self.name

    def process_multiple_values(self, method, values, concept, **context):
        # the output of a method that process multiple values
        # must return an OrderedDict or a sequence of key-value
        # pairs that can be used to create an OrderedDict
        data = method(values, concept, **context)

        if not isinstance(data, OrderedDict):
            out.update(data)
        else:
            out = data
        return out

    def to_string(self, name, value, definition, concept, **context):
        # attempt to coerce non-strings to strings. depending on the data
        # types that are being passed into this, this may not be good
        # enough for certain datatypes or complext data structures
        if value is None:
            return u''
        return force_unicode(value, strings_only=False)

    def to_bool(self, name, value, definition, concept, **context):
        # if value is native True or False value, return it
        # Change value to bool if value is a string of false or true
        if type(value) is bool:
            return value
        elif value == "True":
            value = True
        elif value == "False":
            value = False
        else:
            raise Exception("Can't Convert to bool")
        return value

    def to_number(self, name, value, definition, concept, **context):
        # attempts to convert a number. Starting with ints and floats
        # Eventually create to_decimal using the decimal library.
        if type(value) is int or is float:
            return value
        try: value = int(value)
        except ValueError, TypeError:
            value = float(value)
        return value

    def to_coded(self, name, value, definition, concept, **context):
        # attempts to convert value to its coded representation
        code_dict = dict(definition.coded_values)
        value = code_dict[value]
        return value

    def to_raw(self, name, value, definition, concept, **context):
        # returns raw value
        return value


# initialize the registry that will contain all classes for this type of
# registry
registry = loader.Registry(default=Formatter)

# this will be invoked when it is imported by models.py to use the
# registry choices
loader.autodiscover('formatters')
