from sqlalchemy import Column, ForeignKey, Integer, create_engine, event
from sqlalchemy.orm import Session, DeclarativeBase, joinedload, relationship


class Base(DeclarativeBase):
    pass


class Parent(Base):
    __tablename__ = "parents"
    id = Column(Integer, primary_key=True)
    children = relationship("Child", back_populates="parent")


class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("parents.id"))
    parent = relationship("Parent", back_populates="children")


def test_joinedload_prevents_n_plus_one(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/n1.db")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        p = Parent()
        session.add(p)
        session.add_all([Child(parent=p) for _ in range(3)])
        session.commit()
        queries: list[str] = []

        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            if statement.strip().upper().startswith("SELECT"):
                queries.append(statement)

        event.listen(engine, "before_cursor_execute", before_cursor_execute)
        parents = session.query(Parent).options(joinedload(Parent.children)).all()
        for parent in parents:
            _ = list(parent.children)
        event.remove(engine, "before_cursor_execute", before_cursor_execute)
        assert len(queries) <= 2


