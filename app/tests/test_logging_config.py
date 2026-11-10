import logging

import logging_config


def test_configure_logging_sets_level():
    logging_config.configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING


def test_configure_logging_idempotent_no_duplicate_handlers():
    logging_config.configure_logging("INFO")
    before = len(logging.getLogger().handlers)
    logging_config.configure_logging("INFO")
    after = len(logging.getLogger().handlers)
    assert after == before
