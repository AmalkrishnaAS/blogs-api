#initialise flask
from flask import Flask,jsonify,request,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import os
import uuid
from datetime import datetime,timedelta
from passlib.hash import sha256_crypt
import jwt
from  functools import wraps
import boto3
from dotenv import dotenv_values
from werkzeug.utils import secure_filename


config=dotenv_values('.env')


s3=boto3.client(
    "s3",
    aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY'],
    region_name='us-east-1'
)

bucket_name=config['BUCKET_NAME']




app = Flask(__name__)
db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)
basedir=os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'db.sqlite')
app.config['SECRET_KEY'] = config['SECRET_KEY']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#user schema
class User(db.Model):
    id=db.Column(db.Integer, primary_key=True,autoincrement=True)
    public_id=db.Column(db.String(50), unique=True)
    email=db.Column(db.String(120), unique=True, nullable=False)
    password=db.Column(db.String, nullable=False)
    name=db.Column(db.String(120), nullable=False)
    avatar=db.Column(db.String,default=None)


#user schema
class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','public_id','email','name','avatar')



#blog schema
class Blog(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(120), nullable=False)
    content=db.Column(db.String(500), nullable=False)
    user_id=db.Column(db.Integer, nullable=False)
    created_at=db.Column(db.String, nullable=False)
    updated_at=db.Column(db.String, nullable=False)
    thumbnail=db.Column(db.String,default=None)
    Author=db.Column(db.String,default=None)
    Authur_pic=db.Column(db.String,default=None)


#blog schema
class BlogSchema(ma.Schema):
    class Meta:
        fields = ('id','title','content','user_id','created_at','updated_at','thumbnail','Author','Authur_pic')

#single user schema object
user_schema = UserSchema()
blog_schema = BlogSchema()
users_schema = UserSchema(many=True)
blogs_schema = BlogSchema(many=True)

#token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token=None
        if 'x-access-token' in request.headers:
            token=request.headers['x-access-token']

        if not token:
            return make_response("Unauthorized access",401)

        try:
            data=jwt.decode(token,app.config['SECRET_KEY'])
            current_user=User.query.filter_by(public_id=data['public_id']).first()

        except:
            return make_response("Could not Verify",401,{"Auth_Status":"invalid"})

        return f(current_user,*args,**kwargs)
    return decorated


#create user
@app.route('/user/register', methods=["POST"])
def register_user():
    data=request.get_json()
    hashed_password=sha256_crypt.hash(data['password'])

    email=data['email']

    #if email already exists
    if User.query.filter_by(email=email).first():
        return make_response("Email already exists",400)

    
    new_user=User(public_id=str(uuid.uuid4()),email=data['email'],password=hashed_password,name=data['name'],avatar=data['avatar'])
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user)


#get all users (for testing)
@app.route('/user/all', methods=["GET"])
def get_all_users():
    all_users=User.query.all()
    result=users_schema.dump(all_users)
    return users_schema.jsonify(result)

#login user
@app.route('/user/login', methods=["POST"])
def login_user():
    data=request.get_json()
    user=User.query.filter_by(email=data['email']).first()
    if user and sha256_crypt.verify(data['password'],user.password):
        token=jwt.encode({'public_id':user.public_id,'exp':datetime.utcnow()+timedelta(minutes=120)},app.config['SECRET_KEY'])
        return jsonify({'token':token.decode('UTF-8')})
    return make_response("Could not verify",401,{"Auth_Status":"invalid"})

#create blog
@app.route('/blog/create', methods=["POST"])
@token_required
def create_blog(current_user):
    data=request.get_json()
    Author=current_user.name
    Authur_pic=current_user.avatar
    new_blog=Blog(title=data['title'],content=data['content'],user_id=current_user.id,created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),updated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),Author=Author,Authur_pic=Authur_pic)
    db.session.add(new_blog)
    db.session.commit()
    return blog_schema.jsonify(new_blog)


#get all blogs
@app.route('/blog/all', methods=["GET"])
def get_all_blogs():
    all_blogs=Blog.query.all()
    result=blogs_schema.dump(all_blogs)
    return blogs_schema.jsonify(result)


#get single blog
@app.route('/blog/<id>', methods=["GET"])
def get_single_blog(id):
    blog=Blog.query.filter_by(id=id).first()
    return blog_schema.jsonify(blog)


#get all blogs by user using token
@app.route('/blog/all_by_user', methods=["GET"])
@token_required
def get_all_blogs_by_user(current_user):
    all_blogs=Blog.query.filter_by(user_id=current_user.id).all()
    result=blogs_schema.dump(all_blogs)
    return blogs_schema.jsonify(result)
    
#update blog
@app.route('/blog/update/<id>', methods=["PUT"])
@token_required
def update_blog(current_user,id):
    data=request.get_json()
    blog=Blog.query.filter_by(id=id).first()
    blog.title=data['title']
    blog.content=data['content']
    blog.updated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    blog.thumbnail=data['thumbnail']
    db.session.commit()
    return blog_schema.jsonify(blog)

#delete blog
@app.route('/blog/delete/<id>', methods=["DELETE"])
@token_required
def delete_blog(current_user,id):
    blog=Blog.query.filter_by(id=id).first()
    db.session.delete(blog)
    db.session.commit()
    return blog_schema.jsonify(blog)








    










if __name__ == '__main__':
    app.run(debug=True)



