import threading

from metrics_option import *
from constant import *
from helper import *

metrics_cfg = MetricsCfg()
metrics_collector: map = {}


class MetricValue(object):
    def __init__(self, value: float, flushed_value=None):
        self.value = value
        self.flushed_value = flushed_value


class Collector(object):
    initialed: bool = False  # init func should exec once

    @staticmethod
    def init(metrics_opts: tuple):
        for opt in metrics_opts:
            opt.fill(metrics_cfg)

        metrics_collector[MetricsType.metrics_type_store] = {}
        metrics_collector[MetricsType.metrics_type_counter] = {}
        metrics_collector[MetricsType.metrics_type_timer] = {}

        ## todo：初始化
        http_cli = None

        if not Collector.initialed:
            Collector.initialed = True
            threading.Thread(target=Collector.report()).start()

    @staticmethod
    def report():
        if not Collector.is_enable_metrics():
            return
        Collector.flushTimer()
        Collector.flushCounter()
        Collector.flushStore()

        # a timer only execute once after spec duration
        threading.Timer(DEFAULT_FLUSH_INTERVAL_MS / 1000, Collector.report).start()
        return

    @staticmethod
    def flushStore():
        pass

    @staticmethod
    def flushCounter():
        pass

    @staticmethod
    def flushTimer():
        pass

    @staticmethod
    def is_enable_metrics() -> bool:
        if metrics_cfg is None:
            return False
        return metrics_cfg.enable_metrics

    @staticmethod
    def enable_print_log() -> bool:
        if metrics_cfg is None:
            return False
        return metrics_cfg.print_log

    @staticmethod
    def emit_store(name: str, value: float, tag_kvs: list):
        if not Collector.is_enable_metrics():
            return
        collect_key = build_collect_key(name, tag_kvs)
        Collector.update_metric(MetricsType.metrics_type_store, collect_key, value)

    @staticmethod
    def emit_counter(name: str, value: float, tag_kvs: list):
        if not Collector.is_enable_metrics():
            return
        collect_key = build_collect_key(name, tag_kvs)
        Collector.update_metric(MetricsType.metrics_type_counter, collect_key, value)

    @staticmethod
    def emit_timer(name: str, value: float, tag_kvs: list):
        if not Collector.is_enable_metrics():
            return
        collect_key = build_collect_key(name, tag_kvs)
        Collector.update_metric(MetricsType.metrics_type_timer, collect_key, value)

    @staticmethod
    def update_metric(metrics_type: MetricsType, collect_key: str, value: float):
        pass

    @staticmethod
    def get_or_createMetric(metrics_type: MetricsType, collect_key: str):
        if metrics_collector.get(metrics_type).get(collect_key) is not None:
            return metrics_collector.get(metrics_type).get(collect_key)
        threading.Lock.acquire()
        if metrics_collector.get(metrics_type).get(collect_key) is None:
            metrics_collector.get(metrics_type)[collect_key] = None
            return metrics_collector.get(metrics_type).get(collect_key)
        threading.Lock.release()

    @staticmethod
    def build_default_metric(metrics_type: MetricsType):
        if metrics_type == MetricsType.metrics_type_store:
            return MetricValue(0)
        if metrics_type == MetricsType.metrics_type_counter:

        return
