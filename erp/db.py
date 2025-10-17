from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app) -> None:
    db.init_app(app)


class Health:
    @staticmethod
    def ok() -> bool:
        return True
