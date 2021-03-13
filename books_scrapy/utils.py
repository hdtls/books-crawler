import re
import json


def fmt_label(label):
    return label.strip() if isinstance(label, str) else ""

def fmt_url_domain(domain):
    if not isinstance(domain, str):
        return None
    return domain[:-1] if domain.endswith("/") else domain

def fmt_url_path(path):
    if not isinstance(path, str):
        return None
    return path if path.startswith("/") else path[1:]


def fmt_meta(arg):
    return {"__meta_key": arg}


def revert_fmt_meta(arg):
    return arg["__meta_key"]


def get_img_store(settings, rt, mid, last=None):
    assert rt and mid

    fragments = [settings["IMAGES_STORE"], rt]
    if mid is not None:
        fragments.append(mid)

    if last is not None:
        fragments.append(last)

    return "/".join(fragments)


def eval_js_variable(label, text):
    match = re.findall(r"var %s=(.*);" % (label), text)
    if not match:
        return None
    return json.loads(match[0])