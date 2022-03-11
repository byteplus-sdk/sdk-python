import threading

from metrics_option import *
from constant import *
import helper
from sample import *
from metrics_pb2 import *
import requests
import time
import logging
import sys
from byteplus.core.exception import NetException, BizException

log = logging.getLogger(__name__)

initialed = False  # init func should exec once
metrics_cfg = MetricsCfg()
metrics_collector: map = {}
metrics_locks: map = {}
timer_stat_metrics = ["max", "min", "avg", "pct75", "pct90", "pct95", "pct99", "pct999"]


class MetricValue(object):
    def __init__(self, value: object, flushed_value=None):
        self.value = value
        self.flushed_value = flushed_value
        self.updated = False
        self.lock = threading.Lock()


# As long as the init function is called, the metrics are enabled
def init(metrics_opts: tuple):
    for opt in metrics_opts:
        opt.fill(metrics_cfg)

    metrics_collector[MetricsType.metrics_type_store] = {}
    metrics_collector[MetricsType.metrics_type_counter] = {}
    metrics_collector[MetricsType.metrics_type_timer] = {}

    metrics_locks[MetricsType.metrics_type_store] = threading.Lock()
    metrics_locks[MetricsType.metrics_type_counter] = threading.Lock()
    metrics_locks[MetricsType.metrics_type_timer] = threading.Lock()

    global initialed
    if not initialed:
        initialed = True
        threading.Thread(target=report()).start()


def report():
    if not is_enable_metrics():
        return
    flushTimer()
    flushCounter()
    flushStore()

    # a timer only execute once after spec duration
    threading.Timer(metrics_cfg.flush_interval_ms / 1000, report).start()
    return


def flushStore():
    metrics_requests = []
    with metrics_locks.get(MetricsType.metrics_type_store):
        for collect_key, metric in metrics_collector.get(MetricsType.metrics_type_store).items():
            if metric.updated:
                metric.updated = False
                name, tag_kvs, ok = helper.parse_name_and_tags(collect_key)
                if not ok:
                    continue
                metrics_request: Metric = Metric()
                metrics_request.metric = metrics_cfg.prefix + "." + name
                metrics_request.tags.update(tag_kvs)
                metrics_request.value = metric.value
                metrics_request.timestamp = int(time.time())
                metrics_requests.append(metrics_request)
    if len(metrics_requests) > 0:
        url = OTHER_URL_FORMAT.replace("{}", metrics_cfg.domain)
        metric_message: MetricMessage = MetricMessage()
        metric_message.metrics.extend(metrics_requests)
        try:
            send(metric_message, url)
            if enable_print_log():
                # print("[Metrics] exec store success, url:{}, metrics_requests:{}".format(url, metrics_requests))
                log.debug("[Metrics] exec store success, url:{}, metrics_requests:{}".format(url, metrics_requests))
        except BaseException as e:
            if enable_print_log():
                print("[Metrics] exec store exception, msg:{}, url:{}, metricsRequests:{}".format(str(e), url,
                                                                                                  metrics_requests))
                log.error("[Metrics] exec store exception, msg:{}, url:{}, metricsRequests:{}".format(str(e), url,
                                                                                                      metrics_requests))


def flushCounter():
    metrics_requests = []
    with metrics_locks.get(MetricsType.metrics_type_counter):
        for collect_key, metric in metrics_collector.get(MetricsType.metrics_type_counter).items():
            if metric.updated:
                metric.updated = False
                name, tag_kvs, ok = helper.parse_name_and_tags(collect_key)
                if not ok:
                    continue
                # metric.value may not be the latest, the case is acceptable
                value_copy = metric.value
                metrics_request: Metric = Metric()
                metrics_request.metric = metrics_cfg.prefix + "." + name
                metrics_request.tags.update(tag_kvs)
                metrics_request.value = value_copy - metric.flushed_value
                metrics_request.timestamp = int(time.time())
                metrics_requests.append(metrics_request)
                metric.flushed_value = value_copy
                # if the value is too large, reset it, it rarely happen, no lock is acceptable
                if value_copy >= sys.float_info.max / 2:
                    metric.value = 0.0
                    metric.flushed_value = 0.0

    if len(metrics_requests) > 0:
        url = COUNTER_URL_FORMAT.replace("{}", metrics_cfg.domain)
        metric_message: MetricMessage = MetricMessage()
        metric_message.metrics.extend(metrics_requests)
        try:
            send(metric_message, url)
            if enable_print_log():
                log.debug("[Metrics] exec counter success, url:{}, metrics_requests:{}".format(url, metrics_requests))
        except BaseException as e:
            if enable_print_log():
                log.error("[Metrics] exec counter exception, msg:{}, url:{}, metricsRequests:{}".format(str(e), url,
                                                                                                        metrics_requests))


def flushTimer():
    metrics_requests = []
    with metrics_locks.get(MetricsType.metrics_type_timer):
        for collect_key, metric in metrics_collector.get(MetricsType.metrics_type_timer).items():
            if metric.updated:
                metric.updated = False
                name, tag_kvs, ok = helper.parse_name_and_tags(collect_key)
                if not ok:
                    continue
                snapshot = metric.value.snapshot()
                metric.value.clear()
                metrics_requests.extend(build_stat_metrics(snapshot, name, tag_kvs))

    if len(metrics_requests) > 0:
        url = OTHER_URL_FORMAT.replace("{}", metrics_cfg.domain)
        metric_message: MetricMessage = MetricMessage()
        metric_message.metrics.extend(metrics_requests)
        try:
            send(metric_message, url)
            if enable_print_log():
                log.debug("[Metrics] exec timer success, url:{}, metrics_requests:{}".format(url, metrics_requests))
        except BaseException as e:
            if enable_print_log():
                log.error("[Metrics] exec timer exception, msg:{}, url:{}, metricsRequests:{}".format(str(e), url,
                                                                                                      metrics_requests))


def build_stat_metrics(sample: SampleSnapshot, name: str, tag_kvs: map):
    timestamp = int(time.time())
    metrics_requests = []
    for stat_name in timer_stat_metrics:
        stat_func = sample.get_func_from_name(stat_name)
        if stat_func is None:
            continue
        metrics_request: Metric = Metric()
        metrics_request.metric = metrics_cfg.prefix + "." + name + "." + stat_name
        metrics_request.tags.update(tag_kvs)
        metrics_request.value = stat_func()
        metrics_request.timestamp = timestamp
        metrics_requests.append(metrics_request)
    return metrics_requests


def is_enable_metrics() -> bool:
    if metrics_cfg is None:
        return False
    return metrics_cfg.enable_metrics


def enable_print_log() -> bool:
    if metrics_cfg is None:
        return False
    return metrics_cfg.print_log


def emit_store(name: str, value: float, tag_kvs: list):
    if not is_enable_metrics():
        return
    collect_key = helper.build_collect_key(name, tag_kvs)
    update_metric(MetricsType.metrics_type_store, collect_key, value)


def emit_counter(name: str, value: float, tag_kvs: list):
    if not is_enable_metrics():
        return
    collect_key = helper.build_collect_key(name, tag_kvs)
    update_metric(MetricsType.metrics_type_counter, collect_key, value)


def emit_timer(name: str, value: float, tag_kvs: list):
    if not is_enable_metrics():
        return
    collect_key = helper.build_collect_key(name, tag_kvs)
    update_metric(MetricsType.metrics_type_timer, collect_key, value)


def update_metric(metrics_type: MetricsType, collect_key: str, value: float):
    metric: MetricValue = get_or_create_metric(metrics_type, collect_key)
    if metrics_type == MetricsType.metrics_type_store:
        metric.value = value
    if metrics_type == MetricsType.metrics_type_counter:
        with metric.lock:
            metric.value = metric.value + value
    if metrics_type == MetricsType.metrics_type_timer:
        metric.value.update(value)
    metric.updated = True


def get_or_create_metric(metrics_type: MetricsType, collect_key: str):
    if metrics_collector.get(metrics_type).get(collect_key) is not None:
        return metrics_collector.get(metrics_type).get(collect_key)
    with metrics_locks.get(metrics_type):
        if metrics_collector.get(metrics_type).get(collect_key) is None:
            metrics_collector.get(metrics_type)[collect_key] = build_default_metric(metrics_type)
            return metrics_collector.get(metrics_type).get(collect_key)


def build_default_metric(metrics_type: MetricsType):
    if metrics_type == MetricsType.metrics_type_timer:
        return MetricValue(Sample(RESERVOIR_SIZE))
    if metrics_type == MetricsType.metrics_type_counter:
        return MetricValue(0.0, 0.0)
    return MetricValue(0.0)


# send httpRequest to metrics server
def send(metric_requests: MetricMessage, url: str):
    headers = {"Content-Type": "application/protobuf", "Accept": "application/json"}
    req_bytes: bytes = metric_requests.SerializeToString()
    for i in range(MAX_TRY_TIMES):
        try:
            response = requests.post(url=url, headers=headers, data=req_bytes,
                                     timeout=DEFAULT_HTTP_TIMEOUT_MS / 1000)
            if response.status_code == SUCCESS_HTTP_CODE:
                return
            if response.content is None:
                raise BizException("rsp body is null")
            raise BizException("do http request fail, url:{}， rsp:{}".format(url, response.content))

        except BaseException as e:
            if is_timeout_exception(e) and i < MAX_TRY_TIMES - 1:
                continue
            raise BizException(str(e))


def is_timeout_exception(e):
    lower_err_msg = str(e).lower()
    if "time" in lower_err_msg and "out" in lower_err_msg:
        return True
    return False
