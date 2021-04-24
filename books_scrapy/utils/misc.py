import json
import re


def fmt_label(label):
    return label.strip() if isinstance(label, str) else ""


def eval_js_variable(label, text):
    match = re.findall(r"var %s ?= ?(.*?);" % (label), text)
    if not match:
        return None
    return json.loads(match[0])


def list_extend(lhs, rhs):
    lhs = lhs or []
    rhs = rhs or []
    return list(set(lhs + rhs)) or None


def fmt_url_domain(domain):
    if not isinstance(domain, str):
        return None
    return domain[:-1] if domain.endswith("/") else domain


def fmt_url_path(path):
    if not isinstance(path, str):
        return None
    return path if path.startswith("/") else path[1:]


def format_meta(arg):
    return {"__user_info__": arg}


def revert_formatted_meta(arg):
    return arg["__user_info__"]
