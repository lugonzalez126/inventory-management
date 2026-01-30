from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)

#1. conifguration boilorplate code
#connecting SQLAlchemy to SQLite
#creating storage data base
#adding werkzeug for hasing
app.config["SECRET_KEY"] = "dev-only-change-later"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///storage.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

#2. Creating user model
db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    #creating acolumns called ID that takes int, and is a primary key
    username = db.Column(db.String(20), unique=True, nullable=False)
    #creates columns username, as a string(max 100 ch, must be unique, must have value)
    password_hash = db.Column(db.String(255), nullable=False)
    #create columns of hashed password, max 255 ch, must have value
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)
    #creates function that hashes password and assigns it to password_hash to be stored
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
    # creating function that returns T/F if hashed password match when logging in

@app.route("/")
def home():
    return "Inventory app running"
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
