from byteplus.common.url import CommonURL
from byteplus.core.context import Context

# The URL template of "predict" request
# Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/Predict
_PREDICT_URL_FORMAT = "{}://{}/RetailSaaS/Predict"

# The URL format of reporting the real exposure list
# Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/AckServerImpressions
_ACK_IMPRESSION_URL_FORMAT = "{}://{}/RetailSaaS/AckServerImpressions"

# The URL format of data uploading
# Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/WriteUsers
_UPLOAD_URL_FORMAT = "{}://{}/RetailSaaS/{}"


class _SaasURL(CommonURL):

    def __init__(self, context: Context):
        super().__init__(context)
        # The URL template of "predict" request
        # Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/Predict
        self.predict_url: str = ""

        # The URL of reporting the real exposure list
        # Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/AckServerImpressions
        self.ack_impression_url: str = ""

        # The URL of uploading real-time user data
        # Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/WriteUsers
        self.write_users_url: str = ""

        # The URL of uploading real-time product data
        # Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/WriteProducts
        self.write_products_url: str = ""

        # The URL of uploading real-time user event data
        # Example: https://rec-api-sg1.recplusapi.com/RetailSaaS/WriteUserEvents
        self.write_user_events_url: str = ""

    def refresh(self, host: str) -> None:
        super().refresh(host)
        self.predict_url: str = self._saas_predict_url(host)
        self.ack_impression_url: str = self._saas_ack_url(host)
        self.write_users_url: str = self._saas_upload_url(host, "WriteUsers")
        self.write_products_url: str = self._saas_upload_url(host, "WriteProducts")
        self.write_user_events_url: str = self._saas_upload_url(host, "WriteUserEvents")

    def _saas_predict_url(self, host) -> str:
        return _PREDICT_URL_FORMAT.format(self.schema, host)

    def _saas_ack_url(self, host) -> str:
        return _ACK_IMPRESSION_URL_FORMAT.format(self.schema, host)

    def _saas_upload_url(self, host, topic) -> str:
        return _UPLOAD_URL_FORMAT.format(self.schema, host, topic)
