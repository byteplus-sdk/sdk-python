from abc import abstractmethod
from constant import *


class MetricsCfg(object):
    def __init__(self):
        self.enable_metrics: bool = True
        self.domain: str = DEFAULT_METRICS_DOMAIN
        self.prefix: str = DEFAULT_METRICS_PREFIX
        self.flush_interval_ms = DEFAULT_FLUSH_INTERVAL_MS
        self.print_log: bool = False


class MetricsOption(object):
    @abstractmethod
    def fill(self, cfg: MetricsCfg) -> None:
        raise NotImplementedError

    @staticmethod
    def with_metrics_domain(domain: str):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.domain = domain

        return OptionImpl()

    @staticmethod
    def with_metrics_prefix(prefix: str):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.prefix = prefix

        return OptionImpl()

    @staticmethod
    def with_metrics_log():
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.print_log = True

        return OptionImpl()

    @staticmethod
    def with_flush_interval(flush_interval_ms: int):
        class OptionImpl(MetricsOption):
            def fill(self, cfg: MetricsCfg) -> None:
                cfg.flush_interval_ms = flush_interval_ms

        return OptionImpl()
