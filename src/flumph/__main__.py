import signal
from threading import Thread

from flumph.flask_server import start_flask
from flumph.kivy_window import start_kivy


def signal_handler(signal, frame):
    print(' CTRL + C detected, exiting ...')
    exit(1)


def main():
    # CTRL+C signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # start flask in another thread
    Thread(target=start_flask).start()
    # keep kivy stay in main thread
    start_kivy()


if __name__ == '__main__':
    main()
