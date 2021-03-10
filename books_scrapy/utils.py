def fmt_label(label):
    return label.strip() if isinstance(label, str) else ""

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