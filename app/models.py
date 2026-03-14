from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint

from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    username = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16
)
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Inventory(db.Model):
    __table_args__ = (
        CheckConstraint('length(trim("itemName")) > 0', name="ck_inventory_itemname_not_empty"),
    )  
    id = db.Column(db.Integer, primary_key=True)
    userID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    itemName = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    restockmin = db.Column(db.Integer)
    restockmax = db.Column(db.Integer)
    description = db.Column(db.Text)

class SharedInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ownersID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sharedID = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    permissionLevel = db.Column(db.String(20), nullable=False)