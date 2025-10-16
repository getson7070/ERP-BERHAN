def init_perf_defaults(app):
    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 10,
    })
    app.config.setdefault("SEND_FILE_MAX_AGE_DEFAULT", 300)
