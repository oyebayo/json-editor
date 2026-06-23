import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gtk  # noqa: E402

from editor.logger import get_logger, setup_logging  # noqa: E402
from editor.ui.window import AppWindow  # noqa: E402


def on_activate(app):
    logger = get_logger(__name__)
    logger.info("Application activated")

    win = AppWindow(app)
    win.present()

    if hasattr(app, "initial_file") and app.initial_file:
        win.load_initial_file(app.initial_file)


def main():
    # Parse --debug flag
    debug = "--debug" in sys.argv
    if debug:
        sys.argv.remove("--debug")

    # Setup logging
    setup_logging(debug=debug)
    logger = get_logger(__name__)

    if debug:
        logger.debug("Debug logging enabled")

    logger.info("Starting JSON Editor")

    # Check for file argument
    initial_file = None
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]
        logger.info(f"Initial file provided: {initial_file}")
        # Validate file exists and is readable
        if not os.path.exists(initial_file):
            logger.error(f"File not found: {initial_file}")
            # App will still launch, but error will be shown after window is created
        elif not os.access(initial_file, os.R_OK):
            logger.error(f"File not readable: {initial_file}")
            # App will still launch, but error will be shown after window is created

    app = Gtk.Application(application_id="com.fdcs.jsoneditor")
    app.connect("activate", on_activate)

    # Store initial file for use in on_activate
    app.initial_file = initial_file

    sys.argv = [sys.argv[0]]
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
