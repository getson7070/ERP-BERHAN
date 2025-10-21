from erp.models import db

class Organization(db.Model):
    __tablename__ = "organizations"
    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self) -> str:  # helpful in tests/logs
        return f"<Organization {self.id} {self.name!r}>"



