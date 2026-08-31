import logging
import re


class SensitiveDataFilter(logging.Filter):
    sensitive_fields = ("password", "token", "authorization", "document")

    def filter(self, record):
        message = record.getMessage()
        for field in self.sensitive_fields:
            message = re.sub(
                rf"({field}\s*[=:]\s*)([^\s,]+)",
                rf"{field}=[REDACTED]",
                message,
                flags=re.IGNORECASE,
            )
        record.msg = message
        record.args = ()
        return True
