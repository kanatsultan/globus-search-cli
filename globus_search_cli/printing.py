import json
import sys

import six


def safeprint(s):
    try:
        print(s)
        sys.stdout.flush()
    except IOError:
        pass


def format_output(dataobject):
    if isinstance(dataobject, six.string_types):
        safeprint(dataobject)
    else:
        safeprint(json.dumps(dataobject, indent=2, separators=(",", ": ")))
