"""The browser tests need Selenium and Chrome (pip install selenium). Without Selenium they
are not collected, so a plain `pytest` still runs every other test. CI runs them in its
own "ui" job."""
import importlib.util

collect_ignore_glob = [] if importlib.util.find_spec("selenium") else ["test_*.py"]
