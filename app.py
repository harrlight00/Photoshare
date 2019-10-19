######################################
# author Charlie Harr <charr@bu.edu> 
# Adapted from code by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from datetime import date
from flaskext.mysql import MySQL
#import flask.ext.login as flask_login
import flask_login
from flask_login import current_user
#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = '460Password' #CHANGE THIS TO YOUR MYSQL PASSWORD
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users") 
    return cursor.fetchall()

class User(flask_login.UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not(email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0] )
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
    return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
            <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'></input>
                <input type='password' name='password' id='password' placeholder='password'></input>
                <input type='submit' name='submit'></input>
            </form></br>
            <a href='/'>Home</a>
            '''
    #The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    #check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0] )
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user) #okay login in user
            return flask.redirect(flask.url_for('user_profile')) #user_profile is a function defined in this file

    #information did not match
    return "<a href='/login'>Try again</a>\
            </br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html') 
    
@app.route("/top", methods=['GET'])
def top_users():
    top_list = getTopUsers()
    topl=[]
    for item in top_list:
        topl.append((getEmailFromUID(item[0]),item[1]))
    return render_template('top.html',top=topl, users=True)

@app.route("/toptags", methods=['GET'])
def top_tags():
    top_list = getTopTags()
    return render_template('top.html',top=top_list, users=False)    
    
@app.route("/tagreccs", methods=['GET','POST'])
def tag_reccs():
    if request.method=='GET':
        return render_template('findtag.html', recc=True)
    tags=request.form.get('taglist')
    tag_list=tags.split(' ')
    if not tag_list:
        return render_template('hello.html', message="No suitable pictures found")
    pid_list=reccTags(tag_list) #List of pids with these tags
    
    if not pid_list:
        return render_template('hello.html', message="No suitable tags found")
    query="SELECT tag, count(tag) FROM (SELECT tag from Tag T WHERE picture_id='{0}'".format(pid_list[0][0]) 
    for i in range(1,len(pid_list)):
        query += " union all SELECT tag from Tag q{0} WHERE picture_id='{1}'".format(i,pid_list[i][0])
    query+=") Q GROUP BY tag ORDER BY count(tag)"
    cursor.execute(query)
    tag_list2=cursor.fetchall()
    tagl=[]
    for tag in tag_list2:
        if not tag[0] in tag_list:
            tagl.append(tag[0])
    return render_template("top.html",top=tagl,recc=True)
        
@app.route("/reccs", methods=['GET'])
@flask_login.login_required
def reccs():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    tag_list = getUserTopTags(uid) #Gets users top 5 tags
    tags=""
    for tag in tag_list:
        tags+=tag+" "
    if not tag_list:
        return render_template('hello.html', message="No suitable pictures found")
    pid_list=reccTags(tag_list) #Gets photos with all 5 tags
    if not pid_list:
        return render_template('hello.html', message="No suitable pictures found")
    pidl = []
    for pid in pid_list:
        data=getPhotoData(pid[0])
        pidl.append((data[0],data[2],getEmailFromUID(data[4]),data[1])) #imgdata,caption,uid
    return render_template('tags.html', photos=pidl, tag = tags) 
            
@app.route("/search/", methods=['GET','POST'])
def search_user():
    if request.method == 'GET':
        return render_template('search.html', friend=False)  
    friend_email=request.form.get('email')
    try:
        if(friend_email==flask_login.current_user.id):
            return render_template('search.html', message='That is your email', friend=False) 
    except:
        pass
    cursor = conn.cursor()
    if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(friend_email)): 
        #this means there are greater than zero entries with that email
        return redirect(url_for('view_profile',uemail=friend_email))
    else:
        return render_template('search.html', message='User does not have an account', friend=False) 
  
@app.route("/findtag/", methods=['GET','POST'])
def find_tag():
    if request.method == 'GET':
        return render_template('findtag.html')
    tags=request.form.get('taglist')
    tag_list=tags.split(' ')
    if not tag_list:
        return render_template('hello.html', message="No suitable pictures found")
    pid_list=reccTags(tag_list)
    if not pid_list:
        return render_template('hello.html', message="No suitable pictures found")
    pidl = []
    for pid in pid_list:
        data=getPhotoData(pid[0])
        pidl.append((data[0],data[2],getEmailFromUID(data[4]),data[1])) #imgdata,caption,uid
    return render_template('tags.html', photos=pidl, tag = tags) 
  
def reccTags(tag_list):
    cursor = conn.cursor()
    queries = []
    query = "Select T.picture_id from (Select picture_id from Tag where tag = '{0}') T".format(tag_list[0])
    for i in range(1,len(tag_list)):
        queryin = "Select picture_id from Tag where tag = '{0}'".format(tag_list[i])
        if i==1:
            table="T"
        else:
            table="q{0}".format((i-1))
        query += " inner join ({0}) q{1} on {2}.picture_id=q{1}.picture_id".format(queryin,i, table) 
    cursor.execute(query)
    return cursor.fetchall()
  
@app.route('/profpic', methods=['GET', 'POST'])
@flask_login.login_required
def upload_prof():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        photo_data = base64.standard_b64encode(imgfile.read())
        photo_data = photo_data.decode('ASCII')
        cursor = conn.cursor()
        cursor.execute("UPDATE Users SET profilepic='{0}' WHERE user_id='{1}'".format(photo_data,uid))
        conn.commit()
        return render_template('hello.html', name=flask_login.current_user.id,
            message='Profile Pic updated!' )
    #The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('profpic.html')
#end photo uploading code 

@app.route("/<uemail>/view/", methods=['POST', 'GET'])
def view_profile(uemail):
    return check_profile(uemail,False)

@app.route("/<pid>/deletepic", methods=['POST', 'GET'])
@flask_login.login_required
def delete_pic(pid):
    if request.method == 'GET':
        return render_template('confirmp.html',photo=pid)
    
    delete_picture(pid)
    return redirect(url_for('user_profile', message='Deleted!'))
    
@app.route("/<aid>/deletealbum", methods=['POST', 'GET'])
@flask_login.login_required
def delete_album(aid):
    if request.method == 'GET':
        return render_template('confirma.html',album=aid)
    cursor=conn.cursor()
    cursor.execute("DELETE FROM Album WHERE album_id='{0}'".format(aid))
    cursor.execute("SELECT picture_id FROM Pictures WHERE album_id='{0}'".format(aid))
    piclist=cursor.fetchall()
    for pic in piclist:
        if pic:
            delete_picture(pic[0])
    conn.commit()
    return redirect(url_for('user_profile', message='Deleted!'))
    
def delete_picture(pid):
    cursor = conn.cursor()
    #Delete Photo
    cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(pid))
    #Delete Likes
    cursor.execute("DELETE FROM Likes WHERE picture_id='{0}'".format(pid))
    #Delete Comments
    cursor.execute("DELETE FROM Comments WHERE picture_id='{0}'".format(pid))
    #Delete Tags
    cursor.execute("DELETE FROM Tag WHERE picture_id='{0}'".format(pid))
    conn.commit()
    
@app.route("/friend/", methods=['POST', 'GET'])
@flask_login.login_required
def friend_user():
    if request.method == 'GET':
        return render_template('search.html', friend=True)
    friend_email=request.form.get('email')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if(friend_email==flask_login.current_user.id):
        return render_template('search.html', message='That is your email', friend=True) 
        
    cursor = conn.cursor()
    if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(friend_email)): 
        #this means there are greater than zero entries with that email
        fid = getUserIdFromEmail(friend_email)
        if cursor.execute("SELECT * FROM Friend WHERE user_id='{0}' AND friend_id='{1}'".format(uid,fid)):
            return render_template('hello.html', message='Friend previously added!') 
        else:
            cursor.execute("INSERT INTO Friend (user_id, friend_id) VALUES ('{0}','{1}' )".format(uid,fid))
            conn.commit()
            return render_template('hello.html', message='Friend added!') 
    else:
        return render_template('search.html', message='Friend does not have an account', friend=True) 
    
@app.route("/<pid>/comment", methods=['POST'])
def comment(pid):
    commentt=request.form.get('commentt')
    try:
        uid = getUserIdFromEmail(flask_login.current_user.id)
    except:
        uid=0
    dateofC=str(date.today())
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comments (user_id, picture_id, text, dateofC) VALUES ('{0}','{1}','{2}','{3}' )".format(uid,pid,commentt,dateofC))
    conn.commit()
    return render_template('photos.html', photo=getPhotoData(pid), comments=getPhotoComments(pid), tags=getPhotoTags(pid),
            likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=False, message='Comment added!')

@app.route("/<pid>/photos", methods=['GET'])
def show_photo(pid):
    try:
        uid1 = getUserIdFromEmail(flask_login.current_user.id)
        uid2 = getPhotoUser(pid)
        currentu = (uid1==uid2)
    except:
        currentu = False
    return render_template('photos.html', photo=getPhotoData(pid), comments=getPhotoComments(pid),
            likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=currentu, tags=getPhotoTags(pid))
       
@app.route("/<tagc>/tag/<mine>", methods=['GET'])
def show_tag(tagc, mine):
    cursor = conn.cursor()
    if mine=="User":
        mine=True
        uid = getUserIdFromEmail(flask_login.current_user.id)
        current=True
        cursor.execute("SELECT Tag.picture_id, Tag.tag FROM Tag, Pictures WHERE tag='{0}' AND Tag.picture_id=Pictures.picture_id AND Pictures.user_id='{1}'".format(tagc,uid))
    else:
        mine=False
        current=current_user.is_authenticated
        cursor.execute("SELECT picture_id, tag FROM Tag WHERE tag='{0}'".format(tagc))
    pic_list=cursor.fetchall()
    picl = []
    for item in pic_list:
        data=getPhotoData(item[0])
        picl.append((data[0],data[2],getEmailFromUID(data[4]),data[1])) #image, caption, user, pid
    return render_template('tags.html', photos=picl, tag=tagc, useronly=mine, logged=current)
       
@app.route("/<pid>/addtag", methods=['POST'])
def add_tag(pid):
    tag = request.form.get('tag')
    cursor = conn.cursor()
    if cursor.execute("SELECT * FROM Tag WHERE tag='{0}' AND picture_id='{1}'".format(tag,pid)):
        return render_template('photos.html', photo=getPhotoData(pid), comments=getPhotoComments(pid), tags=getPhotoTags(pid),
            likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=True, message='Tag already added!')
    cursor.execute("INSERT INTO Tag (tag, picture_id) VALUES ('{0}','{1}')".format(tag,pid))
    conn.commit()
    return render_template('photos.html', photo=getPhotoData(pid), comments=getPhotoComments(pid), tags=getPhotoTags(pid),
            likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=True, message='Tag added!')
       
@app.route("/<pid>/<tagc>/remtag", methods=['POST', 'GET'])
def rem_tag(pid, tagc):
    if request.method=='GET':
        return render_template('confirmt.html', photo=pid, tag=tagc)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Tag WHERE tag='{0}' AND picture_id='{1}'".format(tagc,pid))
    conn.commit()
    return render_template('photos.html', photo=getPhotoData(pid), comments=getPhotoComments(pid), tags=getPhotoTags(pid),
            likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=True, message='Tag deleted!')

@app.route("/<pid>/photos", methods=['POST'])
@flask_login.login_required
def show_photop(pid):
    cursor = conn.cursor()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    uid2 = getPhotoUser(pid)
    currentu = (uid==uid2)
    if cursor.execute("SELECT * FROM Likes WHERE user_id='{0}' AND picture_id='{1}'".format(uid,pid)):
        return render_template('photos.html', photo=getPhotoData(pid), message='Already liked!', comments=getPhotoComments(pid),
                likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=currentu, tags=getPhotoTags(pid)) 
    else:
        cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}','{1}' )".format(uid,pid))
        conn.commit()
        return render_template('photos.html', photo=getPhotoData(pid), message='Liked!', comments=getPhotoComments(pid),
                likes=getPhotoLikes(pid), likeno=len(getPhotoLikes(pid)), current=currentu, tags=getPhotoTags(pid))
        
@app.route("/register/", methods=['POST', 'GET'])
def register_user():
    if request.method == 'GET':
        return render_template('improved_register.html', supress='True') 
    try:    
        email=request.form.get('email')
        password=request.form.get('password')
        firstname=request.form.get('firstname')
        lastname=request.form.get('lastname')
        birthday=request.form.get('birthday')
    except:
        print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    gender=request.form.get('gender')
    if(gender==None):
        gender = ""
    bio=request.form.get('bio')
    hometown=request.form.get('hometown')
    try:
        imgfile = request.files['photo'] #This line doesn't work for some reason
        photo_data = base64.standard_b64encode(imgfile.read())
        photo_data = photo_data.decode('ASCII')
    except:
        profilepic=""
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        cursor.execute("INSERT INTO Users (email, password, firstname, lastname, birthday) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(email, password,firstname,lastname,birthday))
        user_id=getUserIdFromEmail(email)
        if(gender):
            cursor.execute("UPDATE Users SET gender='{0}' WHERE user_id='{1}'".format(gender,user_id))
        if(hometown):
            cursor.execute("UPDATE Users SET hometown='{0}' WHERE user_id='{1}'".format(hometown,user_id))
        if(bio):
            cursor.execute("UPDATE Users SET bio='{0}' WHERE user_id='{1}'".format(bio,user_id))
        if(profilepic):
            cursor.execute("UPDATE Users SET profilepic='{0}' WHERE user_id='{1}'".format(photo_data,user_id))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption, album_id FROM Pictures WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getTopUsers():
    cursor = conn.cursor()
    query1="select U.user_id, count(C.user_id) as ct from Users U left outer join Comments C ON U.user_id = C.user_id group by U.user_id"
    query2="select U.user_id, count(P.user_id) as ct from Users U left outer join Pictures P ON U.user_id = P.user_id group by U.user_id"
    query3="select X.user_id, (X.ct+Y.ct) as sumc from ({0}) X, ({1}) Y where X.user_id=Y.user_id order by sumc desc limit 10".format(query1,query2)
    cursor.execute(query3)
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]
    
def getTopTags():
    cursor = conn.cursor()
    query1="select tag, count(tag) as ct from Tag group by tag order by ct desc limit 10"
    cursor.execute(query1)
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]    
 
def getUserTopTags(uid):
    cursor = conn.cursor()
    query1="select tag, count(tag) as ct from Tag T, Pictures P where P.picture_id=T.picture_id and P.user_id='{0}'group by tag order by ct desc limit 5".format(uid)
    cursor.execute(query1)
    tag_list = cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]    
    tagl=[]
    for item in tag_list:
        tagl.append(item[0])
    return tagl
 
def getPhotoLikes(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, picture_id FROM Likes WHERE picture_id = '{0}'".format(pid))
    likel = []
    like_list=cursor.fetchall()
    for like in like_list:
        likel.append(getEmailFromUID(like[0]))
    return likel

def getPhotoTags(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT tag, picture_id FROM Tag WHERE picture_id = '{0}'".format(pid))
    tagl = []
    tag_list=cursor.fetchall()
    for tag in tag_list:
        tagl.append(tag[0])
    return tagl
    
def getPhotoComments(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT comment_id, user_id, text FROM Comments WHERE picture_id = '{0}'".format(pid))
    commentl = []
    comment_list=cursor.fetchall()
    for comment in comment_list:
        if comment[1]==0:
            commentl.append((comment[0],"Anonymous",comment[2],False))
        else:
            commentl.append((comment[0],getEmailFromUID(comment[1]),comment[2],True))
    return commentl
    
def getPhotoData(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption, album_id, user_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
    return cursor.fetchone()
    
def getPhotoUser(pid):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
    return cursor.fetchone()[0]
    
def getUsersPhotosA(uid,aid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}' AND album_id='{1}'".format(uid,aid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]
    
def getUsersAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id, name FROM Album WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUsersFriends(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT friend_id FROM Friend WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]    
    
def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
    return cursor.fetchone()[0]
    
def getEmailFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0]

def getFirstNameFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT firstname FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0]
    
def getLastNameFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT lastname FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0]

def getBirthdayFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT birthday FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0] 

def getHometownFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT hometown FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0] 
    
def getGenderFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT gender FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0] 

def getBioFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT bio FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0] 
    
def getProfilePicFromUID(userID):
    cursor = conn.cursor()
    cursor.execute("SELECT profilepic FROM Users WHERE user_id = '{0}'".format(userID))
    return cursor.fetchone()[0] 
    
def getAlbumIDFromUID(userID,album_name):
    cursor = conn.cursor()
    cursor.execute("SELECT album_id FROM Album WHERE user_id = '{0}' AND name = '{1}'".format(userID,album_name))
    answer=cursor.fetchone()
    if(answer):
        return answer[0]
    return answer
    
def isEmailUnique(email):
    #use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
        #this means there are greater than zero entries with that email
        return False
    else:
        return True
#end login code

def check_profile(emailc, current_user, messagel=False):
    userID=getUserIdFromEmail(emailc)
    friends_list=getUsersFriends(userID)
    friendsl=[]
    album_list=getUsersAlbums(userID)
    albuml=[]
    for album in album_list:
        if album:
            aid = album[0]
            name= album[1]
            photo_list=getUsersPhotosA(userID,aid)
            albuml.append((name,photo_list,aid))
    for i in range(len(friends_list)):
        if(friends_list[i]):
            friendsl.append(getEmailFromUID(friends_list[i][0]))
    return render_template('profile.html', name=getFirstNameFromUID(userID), lastname=getLastNameFromUID(userID), 
            birthday=getBirthdayFromUID(userID), hometown=getHometownFromUID(userID), gender=getGenderFromUID(userID),
            bio=getBioFromUID(userID), profilepic=getProfilePicFromUID(userID), email = emailc, current = current_user,
            photos=albuml,friends=friendsl, message=messagel)

@app.route('/profile')
@flask_login.login_required
def user_profile(message=False):
    emailc=flask_login.current_user.id
    return check_profile(emailc, True, message)
    
#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        album_name = request.form.get('album_name')
        dateofC=str(date.today())
        album_id=getAlbumIDFromUID(uid,album_name)
        photo_data = base64.standard_b64encode(imgfile.read())
        photo_data = photo_data.decode('ASCII')
        cursor = conn.cursor()
        if(not album_id):
            cursor.execute("INSERT INTO Album (user_id, dateofC, name) VALUES ('{0}','{1}','{2}' )".format(uid,dateofC,album_name))
            conn.commit()
            album_id=getAlbumIDFromUID(uid,album_name)
        cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}' )".format(photo_data,uid,caption,album_id))
        conn.commit()
        return redirect('/profile')
    #The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('upload.html')
#end photo uploading code 


#default page  
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
    #this is invoked when in the shell  you run 
    #$ python app.py 
    app.run(port=5000, debug=True)
