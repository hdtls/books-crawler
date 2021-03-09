def fmt_label(label):
    return label if label is not None else ""

def get_img_store(settings, rt, mid, last=None):
    assert rt and mid is not None

    fragments = [settings["IMAGES_STORE"], rt]
    if mid is not None:
        fragments.append(mid)

    if last is not None:
        fragments.append(last)

    return "/".join(fragments)