"""Convenience launcher: python run.py"""

from talktoword.app import TalkToWordApp


if __name__ == "__main__":
    app = TalkToWordApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown()
