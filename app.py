#initialise flask
from email import header
import re
from urllib import response
from flask import Flask,jsonify,request,make_response
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS, cross_origin
import os
import uuid
from datetime import datetime,timedelta
from passlib.hash import sha256_crypt
import jwt
from  functools import wraps
import boto3

from werkzeug.utils import secure_filename

ENV='development'





#fix cors error




app = Flask(__name__)
db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)
cors=CORS(app,resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = ['Content-Type','x-access-token']


#cors for cookies





basedir=os.path.abspath(os.path.dirname(__file__))
if ENV=='development':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'db.sqlite')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mvjctpxhhwxsoo:2d521b788593006a32d039d5641e43fa155539c98a3af06143421309b4dc7a7d@ec2-3-211-221-185.compute-1.amazonaws.com:5432/d5a1bv4l2p3kd3'
app.config['SECRET_KEY'] = 'thisissecret'
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
    content=db.Column(db.String, nullable=False)
    user_id=db.Column(db.Integer, nullable=False)
    created_at=db.Column(db.String, nullable=False)
    updated_at=db.Column(db.String, nullable=False)
    thumbnail=db.Column(db.String)
    Author=db.Column(db.String,default=None)
    Authur_pic=db.Column(db.String,default=None)
    publish=db.Column(db.Boolean,default=False)
    
    
    #comment schema
class Comment(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    comment=db.Column(db.String(500), nullable=False)
    blog_id=db.Column(db.Integer, nullable=False)
    created_at=db.Column(db.String, nullable=False)
    user=db.Column(db.String,default=None)
   
   
        
#comment schema
class CommentSchema(ma.Schema):
    class Meta:
        fields = ('id','comment','user_id','blog_id','created_at','user','user_pic')
    
       
                


#blog schema
class BlogSchema(ma.Schema):
    class Meta:
        fields = ('id','title','content','user_id','created_at','updated_at','thumbnail','Author','Authur_pic','publish')

#single user schema object
user_schema = UserSchema()
blog_schema = BlogSchema()
users_schema = UserSchema(many=True)
blogs_schema = BlogSchema(many=True)
comment_schema=CommentSchema()
comments_schema=CommentSchema(many=True)

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
@cross_origin(supports_credentials=True,headers=['Content-Type'])

def register_user():
    
    data=request.get_json()
    hashed_password=sha256_crypt.hash(data['password'])

    email=data['email']

    #if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message":"Email already exists"})

    
    new_user=User(public_id=str(uuid.uuid4()),email=data['email'],password=hashed_password,name=data['name'],avatar=data['avatar'])
    db.session.add(new_user)
    db.session.commit()
    return user_schema.jsonify(new_user)


#get all users (for testing)
@app.route('/user/all', methods=["GET"])
@cross_origin(supports_credentials=True,headers=['Content-Type'])


def get_all_users():
    all_users=User.query.all()
    result=users_schema.dump(all_users)
    return users_schema.jsonify(result)

#login user
@app.route('/user/login', methods=["POST"])


def login_user():
    data=request.get_json()
    user=User.query.filter_by(email=data['email']).first()
    #if user does not exist
    if not user:
        return jsonify({"message":"User does not exist"})
    if user and sha256_crypt.verify(data['password'],user.password):
        token=jwt.encode({'public_id':user.public_id,'exp':datetime.now()+timedelta(minutes=120)},app.config['SECRET_KEY'])
        return jsonify({'token':token.decode('UTF-8')})
    return jsonify({"message":"Invalid credentials"})

#create blog
@app.route('/blog/create', methods=["POST"])
@cross_origin(supports_credentials=True,headers=['Content-Type','x-access-token'])
@token_required
def create_blog(current_user):
    data=request.get_json()
    Author=current_user.name
    Authur_pic=current_user.avatar
    #get current indian time as string
    date=datetime.now().strftime("%d-%m-%Y %H:%M:%S")  
    
    new_blog=Blog(title=data['title'],content=data['content'],user_id=current_user.id,created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),Author=Author,Authur_pic=Authur_pic,thumbnail=data['thumbnail'],publish=data['publish'])
    db.session.add(new_blog)
    db.session.commit()
    
    
    return blog_schema.jsonify(new_blog)


#get all blogs
@app.route('/blog/all', methods=["GET"])
@cross_origin(supports_credentials=True,headers=['Content-Type'])

def get_all_blogs():
    all_blogs=Blog.query.all()
    result=blogs_schema.dump(all_blogs)
    return blogs_schema.jsonify(result)


#get single blog
@app.route('/blog/<id>', methods=["GET"])
@cross_origin(supports_credentials=True,headers=['Content-Type'])
def get_single_blog(id):
    blog=Blog.query.filter_by(id=id).first()
    return blog_schema.jsonify(blog)


#get all blogs by user using token
@app.route('/blog/all_by_user', methods=["GET"])
@cross_origin(supports_credentials=True,headers=['Content-Type','x-access-token'])
@token_required
def get_all_blogs_by_user(current_user):
    all_blogs=Blog.query.filter_by(user_id=current_user.id).all()
    result=blogs_schema.dump(all_blogs)
    return blogs_schema.jsonify(result)
    
#update blog
@app.route('/blog/update/<id>', methods=["PUT"])
@cross_origin(supports_credentials=True,headers=['Content-Type','x-access-token'])
@token_required
def update_blog(current_user,id):
    
    
    if current_user.id == Blog.query.filter_by(id=id).first().user_id:
        data=request.get_json()
        blog=Blog.query.filter_by(id=id).first()
        blog.title=data['title']
        blog.content=data['content']
        blog.updated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        blog.thumbnail=data['thumbnail']
        blog.publish=data['publish']
        db.session.commit()
        return blog_schema.jsonify(blog)
    return jsonify({"message":"Unauthorized access"}) 

#delete blog
@app.route('/blog/delete/<id>', methods=["DELETE"])
@cross_origin(supports_credentials=True,headers=['Content-Type','x-access-token'])
@token_required


def delete_blog(current_user,id):
    if current_user.id!=Blog.query.filter_by(id=id).first().user_id:
        return make_response("Unauthorized access",401,{"Auth_Status":"invalid"})
    blog=Blog.query.filter_by(id=id).first()
    db.session.delete(blog)
    db.session.commit()
    return blog_schema.jsonify(blog)


#create comment
@app.route('/comment/create/<id>', methods=["POST"])
@cross_origin(supports_credentials=True,headers=['Content-Type','x-access-token'])
@token_required
def create_comment(current_user,id):
    data=request.get_json()
    comment=Comment(comment=data['comment'],blog_id=id,user=current_user.name,created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    db.session.add(comment)
    db.session.commit()
    return comment_schema.jsonify(comment)

#get all comments
@app.route('/comment/all/<id>', methods=["GET"])
def get_all_comments(id):
    data=Comment.query.filter_by(blog_id=id).all()
    return comments_schema.jsonify(data)

#get current user
@app.route('/user/current', methods=["GET"])
@cross_origin(supports_credentials=True,headers=['Content-Type','x-access-token'])
@token_required
def get_current_user(current_user):
    return user_schema.jsonify(current_user)


if __name__ == '__main__':
    app.run(debug=True)



