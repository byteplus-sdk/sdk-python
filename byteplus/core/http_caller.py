import datetime
import gzip
import hashlib
import json
import logging
import random
import string
import time
import uuid
from typing import Callable, Optional

import requests
from google.protobuf.message import Message
from requests import Response
from requests.auth import AuthBase
from byteplus.core.constant import VOLC_AUTH_SERVICE

from byteplus.core.context import Context
from byteplus.core.exception import NetException, BizException
from byteplus.core.option import Option
from byteplus.core.options import Options
from byteplus.core.time_helper import rfc3339_format, milliseconds
from byteplus.volcauth.volcauth import VolcAuth
from byteplus.core.metrics_helper import report_request_success, report_request_error, report_request_exception
from byteplus.core.constant import METRICS_KEY_INVOKE_ERROR, METRICS_KEY_INVOKE_SUCCESS

try:
    from urllib.parse import urlparse, parse_qs, quote, unquote, unquote_plus
except ImportError:
    from urlparse import urlparse, parse_qs
    from urllib import quote, unquote, unquote_plus

log = logging.getLogger(__name__)

_SUCCESS_HTTP_CODE = 200


class HttpCaller(object):

    def __init__(self, context: Context):
        self._context = context
        self._volc_auth: VolcAuth = None
        if len(context.volc_auth_conf.ak) > 0:
            self._volc_auth = VolcAuth(context.volc_auth_conf.ak, context.volc_auth_conf.sk,
                                       context.volc_auth_conf.region, VOLC_AUTH_SERVICE)

    def do_json_request(self, url: str, request, response: Message, *opts: Option):
        options: Options = Option.conv_to_options(opts)
        self.do_json_request_with_opts_object(url, request, response, options)

    def do_pb_request(self, url: str, request: Message, response: Message, *opts: Option):
        options: Options = Option.conv_to_options(opts)
        self.do_pb_request_with_opts_object(url, request, response, options)

    def do_json_request_with_opts_object(self, url: str, request, response: Message, options: Options):
        req_str: str = json.dumps(request)
        req_bytes: bytes = req_str.encode("utf-8")
        content_type: str = "application/json"
        self.do_request(url, req_bytes, response, content_type, options)

    def do_pb_request_with_opts_object(self, url: str, request: Message, response: Message, options: Options):
        req_bytes: bytes = request.SerializeToString()
        content_type: str = "application/x-protobuf"
        self.do_request(url, req_bytes, response, content_type, options)

    def do_request(self, url, req_bytes, response, contextType, options: Options):
        req_bytes: bytes = gzip.compress(req_bytes)
        headers: dict = self._build_headers(options, contextType)
        url = self._build_url_with_queries(options, url)
        auth_func = self._build_auth(req_bytes)
        rsp_bytes = self._do_http_request(url, headers, req_bytes, options.timeout, auth_func)
        if rsp_bytes is not None:
            try:
                response.ParseFromString(rsp_bytes)
            except BaseException as e:
                log.error("[ByteplusSDK] parse response fail, err:%s url:%s", e, url)
                raise BizException("parse response fail")

    def _build_headers(self, options: Options, contentType: str) -> dict:
        headers = {
            "Content-Encoding": "gzip",
            # The 'requests' lib support '"Content-Encoding": "gzip"' header,
            # it will decompress gzip response without us
            "Accept-Encoding": "gzip",
            "Content-Type": contentType,
            "Accept": "application/x-protobuf",
            "Tenant-Id": self._context.tenant_id,
        }
        self._with_options_headers(headers, options)
        return headers

    @staticmethod
    def _build_url_with_queries(options: Options, url: str):
        queries = {}
        if options.stage is not None:
            queries["stage"] = options.stage
        if options.queries is not None:
            queries.update(options.queries)
        if len(queries) == 0:
            return url
        query_parts = []
        for query_name in queries.keys():
            query_parts.append(query_name + "=" + queries[query_name])
        query_string = "&".join(query_parts)
        if "?" in url:
            return url + "&" + query_string
        return url + "?" + query_string

    @staticmethod
    def _with_options_headers(headers: dict, options: Options):
        if options.headers is not None:
            headers.update(options.headers)
        if options.request_id is not None and len(options.request_id) > 0:
            headers["Request-Id"] = options.request_id
        else:
            request_id = uuid.uuid1()
            log.info("[ByteplusSDK] use requestId generated by sdk: '%s' ", request_id)
            headers["Request-Id"] = str(request_id)
        if options.data_date is not None:
            headers["Content-Date"] = rfc3339_format(options.data_date)
        if options.date_end is not None:
            headers["Content-End"] = str(options.date_end)
        if options.server_timeout is not None:
            headers["Timeout-Millis"] = str(milliseconds(options.server_timeout))

    def _build_auth(self, req_bytes: bytes) -> Callable:
        if self._context.use_air_auth:
            return lambda req: self._with_air_auth_headers(req, req_bytes)
        return self._volc_auth

    def _with_air_auth_headers(self, req, req_bytes: bytes) -> None:
        # 获取当前时间不带小数的秒级时间戳
        ts = str(int(time.time()))
        # 生成随机字符串。取8字符即可，太长会浪费
        # 为节省性能，也可以直接使用`ts`作为`nonce`
        nonce = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        signature = self._cal_signature(req_bytes, ts, nonce)

        req.headers['Tenant-Ts'] = ts
        req.headers['Tenant-Nonce'] = nonce
        req.headers['Tenant-Signature'] = signature
        return req

    def _cal_signature(self, req_bytes: bytes, ts: str, nonce: str) -> str:
        # 按照token、httpBody、tenantId、ts、nonce的顺序拼接，顺序不能搞错
        # 本身为字符串的字段，需要使用utf-8方式编码
        # http_body_bytes本身为bytes类型，因此无需编码
        sha256 = hashlib.sha256()
        sha256.update(self._context.token.encode('utf-8'))
        sha256.update(req_bytes)
        sha256.update(self._context.tenant_id.encode('utf-8'))
        sha256.update(ts.encode('utf-8'))
        sha256.update(nonce.encode('utf-8'))
        # 生成16进制的sha256 hash码
        return sha256.hexdigest()

    def _do_http_request(self, url: str, headers: dict,
                         req_bytes: bytes, timeout: Optional[datetime.timedelta], auth: Optional[AuthBase]) -> Optional[
        bytes]:
        start = time.time()
        # log.debug("[ByteplusSDK][HTTPCaller] URL:%s Request Headers:\n%s", url, str(headers))
        self._set_host(url, headers)
        try:
            if timeout is not None:
                timeout_secs = timeout.total_seconds()
                rsp: Response = requests.post(url=url, headers=headers, data=req_bytes, timeout=timeout_secs, auth=auth)
            else:
                rsp: Response = requests.post(url=url, headers=headers, data=req_bytes, auth=auth)
        except BaseException as e:
            report_request_exception(METRICS_KEY_INVOKE_ERROR, url, start * 1000, e)
            if self._is_timeout_exception(e):
                log.error("[ByteplusSDK] do http request timeout, url:%s msg:%s", url, e)
                raise NetException(str(e))
            log.error("[ByteplusSDK] do http request occur io exception, url:%s msg:%s", url, e)
            raise BizException(str(e))
        finally:
            cost = int((time.time() - start) * 1000)
            log.debug("[ByteplusSDK] http path:%s, cost:%dms", url, cost)
        # log.debug("[ByteplusSDK][HTTPCaller] URL:%s Response Headers:\n%s", url, str(rsp.headers))
        if rsp.status_code != _SUCCESS_HTTP_CODE:
            self._log_rsp(url, rsp)
            report_request_error(METRICS_KEY_INVOKE_ERROR, url, start * 1000, "invoke-fail")
            raise BizException("code:{} msg:{}".format(rsp.status_code, rsp.reason))
        report_request_success(METRICS_KEY_INVOKE_SUCCESS, url, start * 1000)
        return rsp.content

    def _set_host(self, url: str, headers: dict):
        host = urlparse(url).netloc
        if host.split(":")[-1] == "80":
            host = host[0]
        headers['Host'] = host

    @staticmethod
    def _is_timeout_exception(e):
        lower_err_msg = str(e).lower()
        if "time" in lower_err_msg and "out" in lower_err_msg:
            return True
        return False

    @staticmethod
    def _log_rsp(url: str, rsp: Response) -> None:
        rsp_bytes = rsp.content
        if rsp_bytes is not None and len(rsp.content) > 0:
            log.error("[ByteplusSDK] http status not 200, url:%s code:%d msg:%s headers:\n%s body:\n%s",
                      url, rsp.status_code, rsp.reason, str(rsp.headers), str(rsp_bytes))
        else:
            log.error("[ByteplusSDK] http status not 200, url:%s code:%d msg:%s headers:\n%s",
                      url, rsp.status_code, rsp.reason, str(rsp.headers))
        return
