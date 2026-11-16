import unittest
from csvpath.util.config import Config


class SkipUtility:
    """Lets tests honor the [testing] <backend>.skip flags in the active config.

    A test that reaches a remote backend (S3, Azure, GCS or SFTP) calls
    skip_unless_enabled() before it touches the network. The flags look
    like this:

        [testing]
        azure.skip = yes
        gcs.skip = yes
        s3.skip = yes
        sftp.skip = no

    "no" means the backend is enabled and the test runs. "yes" means the
    test is skipped. A missing flag also means skip, because a remote call
    costs money and the safe default is not to make one. Any other value is
    a ValueError, so a typo in a config fails loudly rather than silently
    running, or silently skipping, the cloud tests.
    """

    BACKENDS = ("azure", "gcs", "s3", "sftp")

    @classmethod
    def is_skipped(cls, *, backend: str, config: Config = None) -> bool:
        if backend is None or not isinstance(backend, str):
            raise TypeError(f"backend must be a str, not {type(backend)}")
        if backend not in cls.BACKENDS:
            raise ValueError(f"backend must be one of {cls.BACKENDS}, not {backend!r}")
        if config is None:
            config = Config()
        flag = config.get(section="testing", name=f"{backend}.skip")
        if flag is None:
            return True
        flag = f"{flag}".strip().lower()
        if flag == "yes":
            return True
        if flag == "no":
            return False
        raise ValueError(
            f"[testing] {backend}.skip must be yes or no, not {flag!r}, in {config.configpath}"
        )

    @classmethod
    def skip_unless_enabled(cls, *, backend: str, config: Config = None) -> None:
        if cls.is_skipped(backend=backend, config=config):
            #
            # unittest.SkipTest is honored by both pytest and unittest
            #
            raise unittest.SkipTest(
                f"[testing] {backend}.skip is not 'no' in the active config"
            )
