from flask import Flask,render_template,request,session,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
import json
import pymysql


from sqlalchemy import text


pymysql.install_as_MySQLdb()


# MY db connection
local_server= True
app = Flask(__name__)
app.secret_key='kusumachandashwini'


# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



# app.config['SQLALCHEMY_DATABASE_URL']='mysql://username:password@localhost/databas_table_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://flaskuser:flaskpass@localhost:3307/studentdbms'



db=SQLAlchemy(app)


class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))
    email=db.Column(db.String(100))

class Department(db.Model):
    cid=db.Column(db.Integer,primary_key=True)
    branch=db.Column(db.String(100))

class Attendence(db.Model):
    aid=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(100))
    attendance=db.Column(db.Integer())

class Trig(db.Model):
    tid=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(100), nullable=False)
    action=db.Column(db.String(100), nullable=False)
    timestamp=db.Column(db.String(100), nullable=False)


class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50))
    email=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(1000))

class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    rollno=db.Column(db.String(50))
    sname=db.Column(db.String(50))
    sem=db.Column(db.Integer)
    gender=db.Column(db.String(50))
    branch=db.Column(db.String(50))
    email=db.Column(db.String(50))
    number=db.Column(db.String(12))
    address=db.Column(db.String(100))
    

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/studentdetails')
def studentdetails():
    
    with db.engine.connect() as connection:
        sql_query = text("SELECT * FROM v_student_report")
        result = connection.execute(sql_query)
        query = result.fetchall() # Get all results before connection closes
    # #################################################
    
    return render_template('studentdetails.html',query=query)
 
@app.route('/triggers')
def triggers():
    # This route is fine as-is.
    query=Trig.query.all()
    return render_template('triggers.html',query=query)

@app.route('/department',methods=['POST','GET'])
def department():
    # This route is fine as-is.
    if request.method=="POST":
        dept=request.form.get('dept')
        query=Department.query.filter_by(branch=dept).first()
        if query:
            flash("Department Already Exist","warning")
            return redirect('/department')
        dep=Department(branch=dept)
        db.session.add(dep)
        db.session.commit()
        flash("Department Addes","success")
    return render_template('department.html')

@app.route('/addattendance',methods=['POST','GET'])
def addattendance():
    query=Student.query.all()
    if request.method=="POST":
        rollno=request.form.get('rollno')
        attend=request.form.get('attend')
        
        
        with db.engine.connect() as connection:
            sp_call = text(f"CALL sp_add_attendance('{rollno}', {attend})")
            connection.execute(sp_call)
            connection.commit() # Commit the change
        # #################################################
        
        flash("Attendance added/updated","warning")
        
    return render_template('attendance.html',query=query)

@app.route('/search',methods=['POST','GET'])
def search():
    if request.method=="POST":
        rollno=request.form.get('roll')
        
        
        result = None
        with db.engine.connect() as connection:
            query_sql = text(f"SELECT * FROM v_student_report WHERE rollno = '{rollno}'")
            result_proxy = connection.execute(query_sql)
            result = result_proxy.first() # Get the first result
        # #################################################
        
        return render_template('search.html', result=result)
        
    return render_template('search.html')

@app.route("/delete/<string:id>",methods=['POST','GET'])
@login_required
def delete(id):
    
    with db.engine.connect() as connection:
        sp_call = text(f"CALL sp_delete_student({id})")
        connection.execute(sp_call)
        connection.commit() # Commit the change
    
    
    flash("Student Deleted Successfully","danger")
    return redirect('/studentdetails')


@app.route("/edit/<string:id>",methods=['POST','GET'])
@login_required
def edit(id): 
    if request.method=="POST":
        rollno=request.form.get('rollno')
        sname=request.form.get('sname')
        sem=request.form.get('sem')
        gender=request.form.get('gender')
        branch=request.form.get('branch')
        email=request.form.get('email')
        num=request.form.get('num')
        address=request.form.get('address')

        
        with db.engine.connect() as connection:
            sp_call = text(f"CALL sp_edit_student({id}, '{rollno}', '{sname}', {sem}, '{gender}', '{branch}', '{email}', '{num}', '{address}')")
            connection.execute(sp_call)
            connection.commit() # Commit the change
        
        
        flash("Slot is Updated","success")
        return redirect('/studentdetails')
        
    
    dept=Department.query.all()
    posts=Student.query.filter_by(id=id).first()
    return render_template('edit.html',posts=posts,dept=dept)


@app.route('/signup',methods=['POST','GET'])
def signup():
    
    if request.method == "POST":
        username=request.form.get('username')
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exist","warning")
            return render_template('/signup.html')
        # encpassword=generate_password_hash(password) 
        
        newuser=User(username=username,email=email,password=password) # and password=encpassword
        db.session.add(newuser)
        db.session.commit()
        flash("Signup Succes Please Login","success")
        return render_template('login.html')
        
    return render_template('signup.html')

@app.route('/login',methods=['POST','GET'])
def login():
    
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()

        
        if user and user.password == password: 
            login_user(user)
            flash("Login Success","primary")
            return redirect(url_for('index'))
        else:
            flash("invalid credentials","danger")
            return render_template('login.html')     

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # NO CHANGES
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))



@app.route('/addstudent',methods=['POST','GET'])
@login_required
def addstudent():
    dept=Department.query.all()
    if request.method=="POST":
        rollno=request.form.get('rollno')
        sname=request.form.get('sname')
        sem=request.form.get('sem')
        gender=request.form.get('gender')
        branch=request.form.get('branch')
        email=request.form.get('email')
        num=request.form.get('num')
        address=request.form.get('address')
        
        # ##########  MODIFIED CODE FOR NEW SYNTAX ##########
        with db.engine.connect() as connection:
            sp_call = text(f"CALL sp_add_student('{rollno}', '{sname}', {sem}, '{gender}', '{branch}', '{email}', '{num}', '{address}')")
            connection.execute(sp_call)
            connection.commit() # Commit the change
        # #################################################

        flash("Student Added","info")

    return render_template('student.html',dept=dept)

@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except:
        return 'My db is not Connected'


app.run(debug=True)