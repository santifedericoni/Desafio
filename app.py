from flask import Flask, jsonify
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://pythonchallenge:PkfT8FGUlN3m5PtO@cluster0.sf15y.mongodb.net/challenge_set"
mongo = PyMongo(app)

# Importa las rutas (endpoints) del archivo routes.py
from routes import *

if __name__ == "__main__":
    app.run(debug=True)
