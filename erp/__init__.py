def init_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)        # <— required
    socketio.init_app(app, message_queue=app.config.get("SOCKETIO_MESSAGE_QUEUE"))
