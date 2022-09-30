from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ahdaztctptewca:ef47138d3f73411afc5a975d32641eb7429b6dfc39fca82227a88b9c9098ffe8@ec2-44-209-158-64.compute-1.amazonaws.com:5432/ddd71l2ndds216"
db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)

class File(db.Model):
    __tablename__ = "file"
    id = db.Column(db.Integer, primary_key=True, unique=True)
    file_name = db.Column(db.String(64),nullable=False)
    file = db.Column(db.String,nullable=False)
    user_fk = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self,file_name,file,user_fk):
        self.file_name = file_name
        self.file = file
        self.user_fk = user_fk

class FileSchema(ma.Schema):
    class Meta:
        fields = ("id","file_name","file","user_fk")

file_schema = FileSchema()
multiple_file_schema = FileSchema(many=True)

@app.route("/file/add", methods=["POST"])
def add_file():
    data = request.get_json()
    file_name = data["user"]["file_name"]
    file = data["user"]["file"]
    user_fk = data["user"]["user_fk"]

    new_record = File(file_name, file, user_fk)
    db.session.add(new_record)
    db.session.commit()

    return jsonify("File added successfully")

@app.route('/file/get/<id>', methods=["GET"])
def get_file(id):
    file = db.session.query(File).filter(File.id == id).first()
    return jsonify(file_schema.dump(file))

@app.route('/file/delete/<id>', methods=["DELETE"])
def file_delete(id):
    delete_file = db.session.query(File).filter(File.id == id).first()
    db.session.delete(delete_file)
    db.session.commit()
    return jsonify("from dust to dust!")

@app.route('/file/update/<id>', methods=["PUT"])
def update_file(id):
    if request.content_type != "application/json;charset=UTF-8":
        return jsonify("JSON!")
    
    put_data = request.get_json()
    file = put_data["user"]["file"]
    file_name = put_data["user"]["file_name"]
    theFile = db.session.query(File).filter(File.id == id).first()

    theFile.file = file
    theFile.file_name = file_name

    db.session.commit()
    return jsonify(file_schema.dump(theFile))

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64),nullable=False, unique=True)
    password = db.Column(db.String(32), nullable=False)
    files = db.relationship('File',backref="user",cascade="all,delete,delete-orphan")
    

    def __init__(self,email,password):
        self.email = email
        self.password = password

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','email','password',"files")
    files = ma.Nested(multiple_file_schema)

user_schema = UserSchema()
many_user_schema = UserSchema(many=True)

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(many_user_schema.dump(all_users))

@app.route('/user/add',methods=['POST'])
def add_user():
    if request.content_type != "application/json;charset=UTF-8":
        return jsonify("Error Adding User Enter AS type JSON!")
    post_data = request.get_json()
    email = post_data["user"]["email"]
    password = post_data["user"]["password"]
    possible_dup = db.session.query(User).filter(User.email == email).first()
    if possible_dup is not None:
        return jsonify('Username Exists')

    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(email, encrypted_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify('new user created')

@app.route('/user/verify', methods=["POST"])
def verification():
    if request.content_type != 'application/json;charset=UTF-8':
        return jsonify("JSON!")
    
    post_data = request.get_json()
    email = post_data["user"]["email"]
    password = post_data["user"]["password"]

    user = db.session.query(User).filter(User.email == email).first()

    if email is None:
        return jsonify("User could not be Verified")

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify("User couldn't be Verified")
    return jsonify(["true", user.id])

@app.route('/user/resetpass/<id>', methods=["PUT"])
def update_password(id):
    if request.content_type != "application/json;charset=UTF-8":
        return jsonify("JSON!")
    
    put_data = request.get_json()
    password = put_data["user"]["password"]
    user = db.session.query(User).filter(User.id == id).first()

    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user.password = encrypted_password
    db.session.commit()
    return jsonify(user_schema.dump(user))   

@app.route('/user/delete/<id>', methods=["DELETE"])
def user_delete(id):
    delete_user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(delete_user)
    db.session.commit()
    return jsonify("from dust to dust!") 

@app.route('/user/get/<id>', methods=["GET"])
def get_user(id):
    user = db.session.query(User).filter(User.id == id).first()
    return jsonify(user_schema.dump(user))

if __name__ == '__main__':
    app.run(debug=True)