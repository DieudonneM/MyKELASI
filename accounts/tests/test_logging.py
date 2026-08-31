import logging

from accounts.logging import SensitiveDataFilter


def test_sensitive_data_filter_redacts_sensitive_log_fields():
    record = logging.LogRecord(
        name="mykelasi",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="password=secret token:abc authorization=Bearer-secret document=passport.pdf",
        args=(),
        exc_info=None,
    )

    assert SensitiveDataFilter().filter(record) is True
    assert record.getMessage() == (
        "password=[REDACTED] token=[REDACTED] authorization=[REDACTED] document=[REDACTED]"
    )
