# This file is an instructional README for integrating app_ext modules.
# If your app factory lives at <package>/__init__.py, add:
#
#   from app_ext.security_headers import init_security_headers
#   from app_ext.perf_defaults import init_perf_defaults
#   def create_app():
#       app = Flask(__name__)
#       ...
#       init_perf_defaults(app)
#       init_security_headers(app)
#       return app
#
# This file can be deleted after integration.
