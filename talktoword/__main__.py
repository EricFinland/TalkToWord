"""Entry point: python -m talktoword"""

from talktoword.app import TalkToWordApp


def main():
    app = TalkToWordApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown()


if __name__ == "__main__":
    main()
