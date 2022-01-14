_DELIMITER = '+'


def build_collect_key(name: str, tags: list):
    return name + _DELIMITER + tags_to_string(tags)


def tags_to_string(tags: list):
    tags.sort()
    return '|'.join(tags)


def parse_name_and_tags(src: str):
    index = src.find(_DELIMITER)
    if index == -1:
        return
    return src[:index], src[index + len(_DELIMITER):]


def recover_tags(tag_string: str) -> dict:
    tags = {}
    for tag in tag_string.split('|'):
        kv = tag.split(':')
        if len(kv) != 2:
            continue
        tags[kv[0]] = kv[1]
    return tags
