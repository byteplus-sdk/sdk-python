import logging
from byteplus.core import *
from byteplus.common.client import CommonClient
from byteplus.common.protocol import *
from byteplus.core.context import Param
from byteplus.core.options import Options
from byteplus.saas.url import _SaasURL
from byteplus.saas.protocol import *

log = logging.getLogger(__name__)

_ERR_MSG_TOO_MANY_ITEMS: str = "Only can receive max to {} items in one request".format(MAX_IMPORT_WRITE_ITEM_COUNT)

_HTTP_HEADER_SERVER_FROM: str = "Server-From"
_SAAS_FLAG: str = "saas"

_ERR_MSG_FORMAT: str = "{},field can not empty"
_ERR_FIELD_PROJECT_ID: str = "project_id"
_ERR_FIELD_STAGE: str = "stage"
_ERR_FIELD_MODEL_ID: str = "model_id"


class Client(CommonClient):

    def __init__(self, param: Param):
        super().__init__(param)
        self._saas_url: _SaasURL = _SaasURL(self._context)

    def _do_refresh(self, host: str):
        self._saas_url.refresh(host)

    def _add_saas_flag(self, opts: tuple) -> tuple:
        return opts + (self.with_saas_header(),)

    @staticmethod
    def _with_saas_header() -> Option:
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
    def _check_project_id_and_model_id(project_id: str, model_id: str):
        if project_id != "" or model_id != "":
            return
        empty_params = []
        if project_id == "":
            empty_params.append(_ERR_FIELD_PROJECT_ID)
        if model_id == "":
            empty_params.append(_ERR_FIELD_MODEL_ID)
        raise BizException(_ERR_MSG_FORMAT.format(",".join(empty_params)))

    @staticmethod
    def _check_project_id_and_stage(project_id: str, stage: str):
        if project_id != "" or stage != "":
            return
        empty_params = []
        if project_id == "":
            empty_params.append(_ERR_FIELD_PROJECT_ID)
        if stage == "":
            empty_params.append(_ERR_FIELD_STAGE)
        raise BizException(_ERR_MSG_FORMAT.format(",".join(empty_params)))

    def _do_write_data(self, write_request: WriteDataRequest, url: str, *opts: Option) -> WriteResponse:
        self._check_project_id_and_stage(write_request.topic, write_request.stage)
        if len(opts) == 0:
            opts = ()
        if write_request.datas > MAX_IMPORT_WRITE_ITEM_COUNT:
            log.warning("[ByteplusSDK][WriteData] item count more than '%d'", MAX_IMPORT_WRITE_ITEM_COUNT)
            if len(write_request.datas) > MAX_IMPORT_ITEM_COUNT:
                raise BizException(_ERR_MSG_TOO_MANY_ITEMS)
        opts: tuple = self.add_saas_flag(opts)
        response: WriteResponse = WriteResponse()
        self._http_caller.do_pb_request(url, write_request, response, *opts)
        log.debug("[ByteplusSDK][WriteData] rsp:\n %s", response)
        return response

    def write_users(self, write_request: WriteDataRequest, *opts: Option) -> WriteResponse:
        return self._do_write_data(write_request, self._saas_url.write_users_url, *opts)

    def write_products(self, write_request: WriteDataRequest, *opts: Option) -> WriteResponse:
        return self._do_write_data(write_request, self._saas_url.write_products_url, *opts)

    def write_user_events(self, write_request: WriteDataRequest, *opts: Option) -> WriteResponse:
        return self._do_write_data(write_request, self._saas_url.write_user_events_url, *opts)

    def predict(self, predict_request: PredictRequest, *opts: Option) -> PredictResponse:
        self._check_project_id_and_model_id(predict_request.project_id, predict_request.model_id)
        if len(opts) == 0:
            opts = ()
        opts: tuple = opts + (Option.with_stage(predict_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        response: PredictResponse = PredictResponse()
        self._http_caller.do_pb_request(self._saas_url.predict_url, predict_request, response, *opts)
        log.debug("[ByteplusSDK][Predict] rsp:\n%s", response)
        return response

    def ack_server_impressions(self, ack_request: AckServerImpressionsRequest,
                               *opts: Option) -> AckServerImpressionsResponse:
        self._check_project_id_and_model_id(ack_request.project_id, ack_request.model_id)
        if len(opts) == 0:
            opts = ()
        opts: tuple = opts + (Option.with_stage(ack_request.stage),)
        opts: tuple = self.add_saas_flag(opts)
        response: AckServerImpressionsResponse = AckServerImpressionsResponse()
        self._http_caller.do_pb_request(self._saas_url.ack_impression_url, ack_request, response, *opts)
        log.debug("[ByteplusSDK][AckImpressions] rsp:\n%s", response)
        return response


class ClientBuilder(object):
    def __init__(self):
        self._param = Param()

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
