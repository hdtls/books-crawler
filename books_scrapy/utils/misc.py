import json
import re


def eval_js_variable(label, text):
    match = re.findall(r"var %s ?= ?(.*?);" % (label), text)
    if not match:
        return None
    return json.loads(match[0])


def list_extend(lhs, rhs):
    lhs = lhs or []
    rhs = rhs or []
    return list(set(lhs + rhs)) or None


def formatted_meta(arg):
    return {"__meta__": arg}


def revert_formatted_meta(arg):
    return arg["__meta__"]
