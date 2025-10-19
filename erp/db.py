# erp/db.py — single shared SQLAlchemy shim compatible with Flask-SQLAlchemy usage

from __future__ import annotations
import os
from typing import Any

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, Boolean,
    Date, DateTime, Enum, ForeignKey, Table, UniqueConstraint, Index
)
try:
    from sqlalchemy import JSON  # SQLAlchemy 1.4/2.x
except Exception:
    JSON = None  # optional

from sqlalchemy.orm import (
    declarative_base, relationship, backref, scoped_session, sessionmaker, Session
)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
_engine = create_engine(DATABASE_URL, future=True)
_Session = scoped_session(sessionmaker(bind=_engine, autocommit=False, autoflush=False, future=True))
Base = declarative_base()

class _DB:
    # ORM base like Flask-SQLAlchemy
    Model = Base

    # Re-export common SQLAlchemy symbols so models can do db.Column(db.Integer) etc.
    Column = Column; Integer = Integer; String = String; Text = Text; Float = Float
    Boolean = Boolean; Date = Date; DateTime = DateTime; Enum = Enum
    ForeignKey = ForeignKey; Table = Table; UniqueConstraint = UniqueConstraint; Index = Index
    relationship = relationship; backref = backref
    if JSON is not None:
        JSON = JSON

    session: Session = _Session()
    metadata = Base.metadata

    def create_all(self) -> None:
        self.metadata.create_all(_engine)

    def drop_all(self) -> None:
        self.metadata.drop_all(_engine)

db = _DB()

# Late import: register all models AFTER db is defined, to avoid circulars.
try:
    from erp.models import *  # noqa:F401,F403
except Exception:
    # Allow partial imports during tooling; tests will import models anyway.
    pass

# Re-export models (classes usually start with uppercase)
__all__ = ["db"] + [n for n in globals().keys() if n and n[0].isupper()]