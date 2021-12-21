import logging
from datetime import datetime, timedelta
from optparse import Option
from typing import Optional

from byteplus.common.client import CommonClient
from byteplus.core import BizException
from byteplus.core import MAX_WRITE_ITEM_COUNT, MAX_IMPORT_ITEM_COUNT
from byteplus.core import Region
from byteplus.core.context import Param
from byteplus.retailv2.protocol import *
from byteplus.retailv2.url import _RetailURL

log = logging.getLogger(__name__)

_TOO_MANY_WRITE_ITEMS_ERR_MSG = "Only can receive {} items in one write request".format(MAX_WRITE_ITEM_COUNT)
_TOO_MANY_IMPORT_ITEMS_ERR_MSG = "Only can receive {} items in one import request".format(MAX_IMPORT_ITEM_COUNT)


class Client(CommonClient):

    def __init__(self, param: Param):
        super().__init__(param)
        self._retail_url: _RetailURL = _RetailURL(self._context)

    def do_refresh(self, host: str):
        self._retail_url.refresh(host)

    def write_users(self, request: WriteUsersRequest, *opts: Option) -> WriteUsersResponse:
        if len(request.users) > MAX_WRITE_ITEM_COUNT:
            raise BizException(_TOO_MANY_WRITE_ITEMS_ERR_MSG)
        url: str = self._retail_url.write_users_url
        response: WriteUsersResponse = WriteUsersResponse()
        self._http_caller.do_pb_request(url, request, response, *opts)
        log.debug("[ByteplusSDK][WriteUsers] rsp:\n %s", response)
        return response

    def write_products(self, request: WriteProductsRequest, *opts: Option) -> WriteProductsResponse:
        if len(request.products) > MAX_WRITE_ITEM_COUNT:
            raise BizException(_TOO_MANY_WRITE_ITEMS_ERR_MSG)
        url: str = self._retail_url.write_products_url
        response: WriteProductsResponse = WriteProductsResponse()
        self._http_caller.do_pb_request(url, request, response, *opts)
        log.debug("[ByteplusSDK][WriteProducts] rsp:\n %s", response)
        return response

    def write_user_events(self, request: WriteUserEventsRequest, *opts: Option) -> WriteUserEventsResponse:
        if len(request.user_events) > MAX_WRITE_ITEM_COUNT:
            raise BizException(_TOO_MANY_WRITE_ITEMS_ERR_MSG)
        url: str = self._retail_url.write_user_events_url
        response: WriteUserEventsResponse = WriteUserEventsResponse()
        self._http_caller.do_pb_request(url, request, response, *opts)
        log.debug("[ByteplusSDK][WriteUserEvents] rsp:\n %s", response)
        return response

    def done(self, date_list: Optional[list], topic: str, *opts: Option) -> DoneResponse:
        request: DoneRequest = DoneRequest()
        if date_list is None or len(date_list) == 0:
            previous_day = datetime.now() - timedelta(days=1)
            self.append_done_date(request, previous_day)
        else:
            for date in date_list:
                self.append_done_date(request, date)
        url_format = self._retail_url.done_url_format
        url = url_format.replace("#", topic)
        response = DoneResponse()
        self._http_caller.do_json_request(url, request, response, *opts)
        log.debug("[ByteplusSDK][Done] rsp:\n%s", response)
        return response

    @staticmethod
    def append_done_date(request: DoneRequest, date: datetime):
        protoDate: Date = Date()
        protoDate.year = date.year
        protoDate.month = date.month
        protoDate.day = date.day
        request.data_date.append(protoDate)

    def predict(self, request: PredictRequest, scene: str, *opts: Option) -> PredictResponse:
        url_format: str = self._retail_url.predict_url_format
        url: str = url_format.replace("#", scene)
        response: PredictResponse = PredictResponse()
        self._http_caller.do_pb_request(url, request, response, *opts)
        log.debug("[ByteplusSDK][Predict] rsp:\n%s", response)
        return response

    def ack_server_impressions(self, request: AckServerImpressionsRequest,
                               *opts: Option) -> AckServerImpressionsResponse:
        url: str = self._retail_url.ack_impression_url
        response: AckServerImpressionsResponse = AckServerImpressionsResponse()
        self._http_caller.do_pb_request(url, request, response, *opts)
        log.debug("[ByteplusSDK][AckImpressions] rsp:\n%s", response)
        return response


class ClientBuilder(object):
    def __init__(self):
        self._param = Param()

    def tenant(self, tenant: str):
        self._param.tenant = tenant
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
