import datetime
import logging
import os

from flask import render_template, has_request_context, request

from postcoderoonie import create_app
from logging.handlers import SMTPHandler, RotatingFileHandler

app = create_app()


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    # note that we set the 500 status explicitly
    app.logger.error(e)
    return render_template('500.html', error=e), 500


class RequestFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None

        return super().format(record)


def set_logger():
    formatter = RequestFormatter(
        '%(asctime)s||%(remote_addr)s||requested %(url)s||%(levelname)s||in %(module)s||%(message)s'
    )
    # Create handlers
    f_handler = RotatingFileHandler(os.getcwd() + '/file.log', maxBytes=100000, backupCount=10)
    f_handler.setLevel(logging.DEBUG)
    # Create formatters and add it to handlers
    f_handler.setFormatter(formatter)
    # Add handlers to the logger
    app.logger.addHandler(f_handler)


set_logger()

if __name__ == '__main__':
    host = "0.0.0.0"
    app.run(debug=True, host=host, port=5006)
