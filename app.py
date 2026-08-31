from flask import Flask, render_template
from config import configure_app
import sys

app = Flask(__name__)
configure_app(app)

sys.modules['app'] = sys.modules[__name__]

import routes
import models

if __name__ == '__main__':
    app.run(debug=True)
