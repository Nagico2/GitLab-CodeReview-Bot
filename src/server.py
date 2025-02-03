import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / 'src'

# Add the root path to the sys.path
sys.path.append(PROJECT_ROOT.as_posix())
sys.path.append(SRC_ROOT.as_posix())

try:
    import gevent.monkey
    gevent.monkey.patch_all()
except ImportError:
    pass

import os

from flask import Flask, jsonify, make_response
from app.gitlab_webhook import git
from utils.args_check import check_config
from utils.logger import log

app = Flask(__name__)

debug = True if os.environ.get('DEBUG', 'False').lower() == 'true' else False
port = os.environ.get('PORT', 8000)

app.config['debug'] = debug

# router group
app.register_blueprint(git, url_prefix='/git')


@app.errorhandler(400)
@app.errorhandler(404)
def handle_error(error):
    error_msg = 'Args Error' if error.code == 400 else 'Page Not Found'
    return make_response(jsonify({'code': error.code, 'msg': error_msg}), error.code)


app.config['JSON_AS_ASCII'] = False
log.info('Starting args check...')
check_config()
log.info('Starting the app...')

if __name__ == '__main__':
    app.run(debug=debug, host="0.0.0.0", port=port, use_reloader=False)
