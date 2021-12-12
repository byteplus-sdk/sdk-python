from byteplus.common.url import CommonURL
from byteplus.core.context import Context

# The URL template of "predict" request, which need fill with "model_Id" info when use
# Example: https://byteair-api-sg1.recplusapi.com/predict/123456/model/654321
_PREDICT_URL_FORMAT = "{}://{}/predict/{}/model/#"

# The URL format of reporting the real exposure list
# Example: https://byteair-api-sg1.recplusapi.com/predict/123456/model/654321/ack_server_impressions
_ACK_IMPRESSION_URL_FORMAT = "{}://{}/predict/{}/model/#/callback"

# The URL format of data uploading
# Example: https://byteair-api-sg1.recplusapi.com/data/api/saas/123456/user?method=write
_UPLOAD_URL_FORMAT = "{}://{}/data/api/saas/{}/#?method={}"

# The URL format of marking a whole day data has been imported completely
# Example: https://byteair-api-sg1.recplusapi.com/data/api/saas/123456/done?topic=user
_DONE_URL_FORMAT = "{}://{}/data/api/saas/{}/done?topic=#"


class _SaasURL(CommonURL):

    def __init__(self, context: Context):
        super().__init__(context)
        # The URL template of "predict" request, which need fill with "model_Id" info when use
        # Example: https://byteair-api-sg1.recplusapi.com/predict/123456/model/654321
        self.predict_url_format: str = ""

        # The URL of reporting the real exposure list
        # Example: https://byteair-api-sg1.recplusapi.com/predict/123456/model/654321/ack_server_impressions
        self.ack_impression_url: str = ""

        # The URL of uploading real-time user data
        # Example: https://byteair-api-sg1.recplusapi.com/data/api/saas/123456/user?method=write
        self.write_data_url_format: str = ""

        # The URL of importing daily offline user data
        # Example: https://byteair-api-sg1.recplusapi.com/data/api/saas/123456/user?method=import
        self.import_data_url_format: str = ""

        # The URL format of marking a whole day data has been imported completely
        # Example: https://byteair-api-sg1.recplusapi.com/data/api/saas/123456/done?topic=user
        self.done_url_format: str = ""
        self.refresh(context.hosts[0])

    def refresh(self, host: str) -> None:
        super().refresh(host)
        self.predict_url_format: str = self._saas_predict_url(host)
        self.ack_impression_url: str = self._saas_ack_url(host)
        self.write_data_url_format: str = self._saas_upload_url(host, "write")
        self.import_data_url_format: str = self._saas_upload_url(host, "import")
        self.done_url_format: str = self._saas_done_url(host)

    def _saas_predict_url(self, host) -> str:
        return _PREDICT_URL_FORMAT.format(self.schema, host, self.tenant)

    def _saas_ack_url(self, host) -> str:
        return _ACK_IMPRESSION_URL_FORMAT.format(self.schema, host, self.tenant)

    def _saas_upload_url(self, host, method) -> str:
        return _UPLOAD_URL_FORMAT.format(self.schema, host, self.tenant, method)

    def _saas_done_url(self, host) -> str:
        return _DONE_URL_FORMAT.format(self.schema, host, self.tenant)
