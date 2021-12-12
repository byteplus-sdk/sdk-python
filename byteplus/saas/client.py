import logging
from byteplus.core import *
from byteplus.common.client import CommonClient
from byteplus.common.protocol import *
from byteplus.core.context import Param
from byteplus.core.options import Options
from byteplus.saas.url import _SaasURL
from byteplus.saas.protocol import *

log = logging.getLogger(__name__)

_ERR_MSG_TOO_MANY_ITEMS = "Only can receive max to {} items in one request".format(MAX_IMPORT_ITEM_COUNT)

_HTTP_HEADER_SERVER_FROM = "Server-From"
_SAAS_FLAG = "saas"

_ERR_MSG_FORMAT = "{},field can not empty"
_ERR_FIELD_TOPIC = "topic"
_ERR_FIELD_STAGE = "stage"


class Client(CommonClient):

    def __init__(self, param: Param):
        super().__init__(param)
        self._saas_url: _SaasURL = _SaasURL(self._context)

    def do_refresh(self, host: str):
        self._saas_url.refresh(host)

    def add_saas_flag(self, opts: tuple) -> tuple:
        return opts + (self.with_saas_header(),)

    @staticmethod
    def with_saas_header() -> Option:
        class OptionImpl(Option):
            def fill(self, options: Options) -> None:
                if len(options.headers) == 0:
                    options.headers = {
                        _HTTP_HEADER_SERVER_FROM: _SAAS_FLAG
                    }
                    return
                options.headers[_HTTP_HEADER_SERVER_FROM] = _SAAS_FLAG
                return

        return OptionImpl()

    @staticmethod
    def check_topic_and_stage(topic: str, stage: str):
        if topic != "" or stage != "":
            return
        empty_params = []
        if topic == "":
            empty_params.append(_ERR_FIELD_TOPIC)
        if stage == "":
            empty_params.append(_ERR_FIELD_STAGE)
        raise BizException(_ERR_MSG_FORMAT.format(",", empty_params))

    def write_data(self, write_request: WriteDataRequest, *opts: Option) -> WriteResponse:
        self.check_topic_and_stage(write_request.topic, write_request.stage)
        if len(opts) == 0:
            opts = ()
        if write_request.datas > MAX_WRITE_ITEM_COUNT:
            log.warning("[ByteplusSDK][WriteData] item count more than '%d'", MAX_WRITE_ITEM_COUNT)
            if len(write_request.datas) > MAX_IMPORT_ITEM_COUNT:
                raise BizException(_ERR_MSG_TOO_MANY_ITEMS)
        url_format: str = self._saas_url.write_data_url_format
        opts: tuple = opts + (Option.with_stage(write_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        url: str = url_format.replace("#", write_request.topic)
        response: WriteResponse = WriteResponse()
        self._http_caller.do_json_request(url, write_request, response, *opts)
        log.debug("[ByteplusSDK][WriteData] rsp:\n %s", response)
        return response

    def import_data(self, import_request: ImportDataRequest, *opts: Option) -> OperationResponse:
        url_format: str = self._saas_url.import_data_url_format
        if len(opts) == 0:
            opts = ()
        opts: tuple = opts + (Option.with_stage(import_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        url: str = url_format.replace("#", import_request.topic)
        response: OperationResponse = OperationResponse()
        self._http_caller.do_json_request(url, import_request, response, *opts)
        log.debug("[ByteplusSDK][ImportData] rsp:\n%s", response)
        return response

    def done(self, done_request: DoneRequest, *opts: Option) -> DoneResponse:
        self.check_topic_and_stage(done_request.topic, done_request.stage)
        if len(opts) == 0:
            opts = ()
        url_format = self._saas_url.done_url_format
        url = url_format.replace("#", done_request.topic)
        opts: tuple = opts + (Option.with_stage(done_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        response = DoneResponse()
        self._http_caller.do_json_request(url, done_request, response, *opts)
        log.debug("[ByteplusSDK][Done] rsp:\n%s", response)
        return response

    def predict(self, predict_request: PredictRequest, model_id: str, *opts: Option) -> PredictResponse:
        self.check_topic_and_stage(predict_request.topic, predict_request.stage)
        if len(opts) == 0:
            opts = ()
        url_format: str = self._saas_url.predict_url_format
        opts: tuple = opts + (Option.with_stage(predict_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        url: str = url_format.replace("#", model_id)
        response: PredictResponse = PredictResponse()
        self._http_caller.do_pb_request(url, predict_request, response, *opts)
        log.debug("[ByteplusSDK][Predict] rsp:\n%s", response)
        return response

    def ack_server_impressions(self, ack_request: AckServerImpressionsRequest,
                               *opts: Option) -> AckServerImpressionsResponse:
        self.check_topic_and_stage(ack_request.topic, ack_request.stage)
        if len(opts) == 0:
            opts = ()
        url: str = self._saas_url.ack_impression_url
        opts: tuple = opts + (Option.with_stage(ack_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        response: AckServerImpressionsResponse = AckServerImpressionsResponse()
        self._http_caller.do_pb_request(url, ack_request, response, *opts)
        log.debug("[ByteplusSDK][AckImpressions] rsp:\n%s", response)
        return response


class ClientBuilder(object):
    def __init__(self):
        self._param = Param()

    def project_id(self, project_id: str):
        self._param.tenant = project_id
        return self

    def tenant_id(self, tenant_id: str):
        self._param.tenant_id = tenant_id
        return self

    def token(self, token: str):
        self._param.token = token
        return self

    def schema(self, schema: str):
        self._param.schema = schema
        return self

    def hosts(self, hosts: list):
        self._param.hosts = hosts
        return self

    def headers(self, headers: dict):
        self._param.headers = headers
        return self

    def region(self, region: Region):
        self._param.region = region
        return self

    def build(self) -> Client:
        return Client(self._param)
