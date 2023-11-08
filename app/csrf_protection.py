from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def init_csrf(app):
    csrf.init_app(app)
