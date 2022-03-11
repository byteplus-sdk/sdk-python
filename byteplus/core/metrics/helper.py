from constant import *
import collector as mc
import time


"""
Parameters:
  key - metrics name
  value - metrics value
  tag_kvs - tag_key and tag_value list, 
    should be formatted as ["tag_key_1:tag_value_1","tag_key_2:tag_value_2",...]
Example:
  counter("request.qp", 1, ["method:user", "type:upload"])
"""
def counter(key: str, value: float, tag_kvs: list):
    mc.emit_counter(key, value, tag_kvs)


"""
Parameters:
  key - metrics name
  value - metrics value
  tag_kvs - tag_key and tag_value list, 
    should be formatted as ["tag_key_1:tag_value_1","tag_key_2:tag_value_2",...]
Example:
  timer("request.cost", 100, ["method:user", "type:upload"])
"""
def timer(key: str, value: float, tag_kvs: list):
    mc.emit_timer(key, value, tag_kvs)


# Latency report time cost for execution
# tagKvs should be formatted as "key:value"
# example: metrics.Latency("request.latency", startTime, "method:user", "type:upload")
"""
Parameters:
  key - metrics name
  begin - the unit of `begin` is milliseconds
  tag_kvs - tag_key and tag_value list, 
    should be formatted as ["tag_key_1:tag_value_1","tag_key_2:tag_value_2",...]
Example:
  latency("request.latency", start_time_ms, ["method:user", "type:upload"])
"""
def latency(key: str, begin: float, tag_kvs: list):
    mc.emit_timer(key, time.time_ns() / 1e6 - begin, tag_kvs)


"""
Parameters:
  key - metrics name
  value - metrics value
  tag_kvs - tag_key and tag_value list, 
    should be formatted as ["tag_key_1:tag_value_1","tag_key_2:tag_value_2",...]
Example:
  store("goroutine.count", 400, ["ip:127.0.0.1"])
"""
def store(key: str, value: float, tag_kvs: list):
    mc.emit_store(key, value, tag_kvs)


def build_collect_key(name: str, tags: list):
    return name + DELIMITER + tags_to_string(tags)


def tags_to_string(tags: list):
    tags.sort()
    return '|'.join(tags)


def parse_name_and_tags(src: str):
    index = src.find(DELIMITER)
    if index == -1:
        return None, None, False
    return src[:index], recover_tags(src[index + len(DELIMITER):]), True


def recover_tags(tag_string: str) -> dict:
    tags = {}
    for tag in tag_string.split('|'):
        kv = tag.split(':')
        if len(kv) != 2:
            continue
        tags[kv[0]] = kv[1]
    return tags
