
#
# spyne - Copyright (C) Spyne contributors.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#

import decimal
import datetime
import math
from collections import deque

from spyne.model import nillable_string
from spyne.model import nillable_dict
from spyne.model.binary import File
from spyne.model.binary import Attachment
from spyne.error import ValidationError
from spyne.model.primitive import _time_re
from spyne.model.primitive import _duration_re

try:
    from lxml import etree
    from lxml import html
except ImportError:
    etree = None
    html = None

__all__ = [
    'null_to_string', 'null_from_string',
    'any_xml_to_string', 'any_xml_from_string',
    'any_html_to_string', 'any_html_from_string',
    'unicode_to_string', 'unicode_from_string',
    'string_from_string',
    'decimal_to_string', 'decimal_from_string',
    'double_to_string', 'double_from_string',
    'integer_to_string', 'integer_from_string',
    'time_to_string', 'time_from_string',
    'datetime_to_string', 'datetime_from_string',
    'date_from_string',
    'duration_to_string', 'duration_from_string',
    'boolean_to_string', 'boolean_from_string',
    'byte_array_to_string', 'byte_array_from_string',
    'file_from_string',
    'attachment_to_string', 'attachment_from_string',
    'complex_model_base_to_string', 'complex_model_base_from_string', 'complex_model_base_to_dict',
    'fault_to_dict'
]

def null_to_string(cls, value):
    return ""

def null_from_string(cls, value):
    return None


@nillable_string
def any_xml_to_string(cls, value):
    return etree.tostring(value)

@nillable_string
def any_xml_from_string(cls, string):
    try:
        return etree.fromstring(string)
    except etree.XMLSyntaxError, e:
        raise ValidationError(string, "%%r: %r" % e)


@nillable_string
def any_html_to_string(cls, value):
    return html.tostring(value)

@nillable_string
def any_html_from_string(cls, string):
    return html.fromstring(string)


@nillable_string
def unicode_to_string(cls, value):
    retval = value
    if cls.Attributes.encoding is not None and isinstance(value, unicode):
        retval = value.encode(cls.Attributes.encoding)
    if cls.Attributes.format is None:
        return retval
    else:
        return cls.Attributes.format % retval

@nillable_string
def unicode_from_string(cls, value):
    retval = value
    if isinstance(value, str):
        if cls.Attributes.encoding is None:
            retval = unicode(value, errors = cls.Attributes.unicode_errors)
        else:
            retval = unicode(value, cls.Attributes.encoding,
                                    errors = cls.Attributes.unicode_errors)
    return retval


@nillable_string
def string_from_string(cls, value):
    retval = value
    if isinstance(value, unicode):
        if cls.Attributes.encoding is None:
            raise Exception("You need to define an encoding to convert the "
                            "incoming unicode values to.")
        else:
            retval = value.encode(cls.Attributes.encoding)

    return retval


@nillable_string
def decimal_to_string(cls, value):
    decimal.Decimal(value)
    if cls.Attributes.format is None:
        return str(value)
    else:
        return cls.Attributes.format % value

@nillable_string
def decimal_from_string(cls, string):
    if cls.Attributes.max_str_len is not None and len(string) > \
                                                     cls.Attributes.max_str_len:
        raise ValidationError(string, "Decimal %%r longer than %d characters"
                                                   % cls.Attributes.max_str_len)

    try:
        return decimal.Decimal(string)
    except decimal.InvalidOperation, e:
        raise ValidationError(string, "%%r: %r" % e)


@nillable_string
def double_to_string(cls, value):
    float(value)
    if cls.Attributes.format is None:
        return repr(value)
    else:
        return cls.Attributes.format % value

@nillable_string
def double_from_string(cls, string):
    try:
        return float(string)
    except ValueError, e:
        raise ValidationError(string, "%%r: %r" % e)


@nillable_string
def integer_to_string(cls, value):
    int(value) # sanity check

    return str(value)

@nillable_string
def integer_from_string(cls, string):
    if cls.Attributes.max_str_len is not None and len(string) > \
                                                     cls.Attributes.max_str_len:
        raise ValidationError(string, "Integer %%r longer than %d characters"
                                                   % cls.Attributes.max_str_len)

    try:
        return int(string)
    except ValueError:
        raise ValidationError(string, "Could not cast %r to integer")


@nillable_string
def time_to_string(cls, value):
    """Returns ISO formatted dates."""

    return value.isoformat()

@nillable_string
def time_from_string(cls, string):
    """Expects ISO formatted times."""

    match = _time_re.match(string)
    if match is None:
        raise ValidationError(string, "%%r does not match regex %r " %
                                                               _time_re.pattern)

    fields = match.groupdict(0)
    microsec = fields.get('sec_frac')
    if microsec is None or microsec == 0:
        microsec = 0
    else:
        microsec = int(microsec[1:])

    return datetime.time(int(fields['hr']), int(fields['min']),
                                                   int(fields['sec']), microsec)


@nillable_string
def datetime_to_string(cls, value):
    if cls.Attributes.as_time_zone is not None and value.tzinfo is not None:
        value = value.astimezone(cls.Attributes.as_time_zone) \
                                                    .replace(tzinfo=None)

    format = cls.Attributes.format
    if format is None:
        ret_str = value.isoformat()
    else:
        ret_str = datetime.datetime.strftime(value, format)

    string_format = cls.Attributes.string_format
    if string_format is None:
        return ret_str
    else:
        return string_format % ret_str

@nillable_string
def datetime_from_string(cls, string):
    format = cls.Attributes.format

    if format is None:
        retval = cls.default_parse(string)
    else:
        retval = datetime.datetime.strptime(string, format)

    if cls.Attributes.as_time_zone is not None and retval.tzinfo is not None:
        retval = retval.astimezone(cls.Attributes.as_time_zone) \
                                                    .replace(tzinfo=None)

    return retval


@nillable_string
def date_from_string(cls, string):
    try:
        d = datetime.datetime.strptime(string, cls.Attributes.format)
        return datetime.date(d.year, d.month, d.day)
    except ValueError, e:
        raise ValidationError(string, "%%r: %r" % e)


def duration_to_string(cls, value):
    if value.days < 0:
        value = -value
        negative = True
    else:
        negative = False

    seconds = value.seconds % 60
    minutes = value.seconds / 60
    hours = minutes / 60
    minutes = minutes % 60
    seconds = float(seconds) + value.microseconds / 1e6

    retval = deque()
    if negative:
        retval.append("-")

    retval = ['P']
    if value.days > 0:
        retval.extend([
            "%iD" % value.days,
            ])

    if hours > 0 and minutes > 0 and seconds > 0:
        retval.extend([
            "T",
            "%iH" % hours,
            "%iM" % minutes,
            "%fS" % seconds,
            ])

    else:
        retval.extend([
            "0S",
            ])

    return ''.join(retval)

@nillable_string
def duration_from_string(cls, string):
    duration = _duration_re.match(string).groupdict(0)
    if duration is None:
        raise ValidationError("time data '%s' does not match regex '%s'" %(string, _duration_re.pattern))

    days = int(duration['days'])
    days += int(duration['months']) * 30
    days += int(duration['years']) * 365
    hours = int(duration['hours'])
    minutes = int(duration['minutes'])
    seconds = float(duration['seconds'])
    f, i = math.modf(seconds)
    seconds = i
    microseconds = int(1e6 * f)

    delta = datetime.timedelta(days=days, hours=hours, minutes=minutes,
        seconds=seconds, microseconds=microseconds)

    if duration['sign'] == "-":
        delta *= -1

    return delta


@nillable_string
def boolean_to_string(cls, value):
    return str(bool(value)).lower()

@nillable_string
def boolean_from_string(cls, string):
    return (string.lower() in ['true', '1'])


@nillable_string
def byte_array_to_string(cls, value):
    return cls._encoding_handlers[cls.Attributes.encoding](value)

@nillable_string
def byte_array_from_string(cls, value):
    return cls._decoding_handlers[cls.Attributes.encoding](value)


@nillable_string
def file_from_string(cls, value):
    return File.Value(data=[value])


@nillable_string
def attachment_to_string(cls, value):
    if not (value.data is None):
        # the data has already been loaded, just encode
        # and return the element
        data = value.data

    elif not (value.file_name is None):
        # the data hasn't been loaded, but a file has been
        # specified
        data = open(value.file_name, 'rb').read()
    else:
        raise ValueError("Neither data nor a file_name has been specified")

    return data

@nillable_string
def attachment_from_string(cls, value):
    return Attachment(data=value)


@nillable_string
def complex_model_base_to_string(cls, value):
    raise TypeError("Only primitives can be serialized to string.")

@nillable_string
def complex_model_base_from_string(cls, string):
    raise TypeError("Only primitives can be deserialized from string.")

@nillable_dict
def complex_model_base_to_dict(cls, value):
    inst = cls.get_serialization_instance(value)
    return dict(cls.get_members_pairs(inst))


def fault_to_dict(cls, value):
    return {cls.get_type_name(): {
        "faultcode": value.faultcode,
        "faultstring": value.faultstring,
        "detail": value.detail,
    }}
