from src.flowtrace import create_app
from src.flowtrace.config import FLOWTRACE_DEBUG, PORT, logger

app = create_app()


def main():
    logger.info("Starting FlowTrace on http://0.0.0.0:%s", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=FLOWTRACE_DEBUG)


if __name__ == "__main__":
    main()
