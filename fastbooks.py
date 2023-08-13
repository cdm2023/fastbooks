from flask import Flask, render_template, url_for, request, redirect, session, jsonify, g, flash 
from flask_mysqldb import MySQL
from flask_wtf import Form
from forms import ExpenseForm,ExpenseReportForm,ExpRepTime,LoginForm,RegisterForm
import datetime as dt
from  flask_bcrypt import Bcrypt

from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
import datetime as dt
from datetime import date

app = Flask(__name__)
bcrypt = Bcrypt(app)

db_conf = yaml.safe_load(open('db.yaml'))

app.config['SECRET_KEY'] = '0us0ntlesne1ges'
app.config['MYSQL_HOST'] = db_conf['mysql_host']
app.config['MYSQL_USER'] = db_conf['mysql_user']
app.config['MYSQL_PASSWORD'] = db_conf['mysql_password']
app.config['MYSQL_DB'] = db_conf['mysql_db']
app.config['DEBUG'] = db_conf['debug']

mysql = MySQL(app)
Bootstrap(app)

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/formtest", methods=['GET','POST'])
def formtest():
    if 'user_id' in session:
        form = ExpenseForm()
        return render_template("new_expense.html",form=form)
    else:
        return redirect(url_for('login'))


@app.route('/new_expense', methods=['GET', 'POST'])
def new_expense():
    
        user_id = session['user_id']
        ecats_list = []
        curEcats=mysql.connection.cursor()
        sqlEcats ="SELECT c.cat_id, c.category FROM categories c  WHERE c.webshow=1 and c.user_id =%s ORDER BY 2"
        curEcats.execute(sqlEcats,(user_id,) )
        Ecats=curEcats.fetchall()
        curEcats.close()
        if Ecats:
            for c in Ecats: 
                ecats_list.append(c)
        else:
            return "No Ecats"
        if request.method=='POST':
            cur = mysql.connection.cursor()
            expamount = request.form.get('exp_amount')
            expdescr = request.form.get('exp_descr')
            expvendor = request.form.get('exp_vendor')
            expcat = request.form.get('exp_cat')
            card_total = request.form.get('card_total')
            multi = int(request.form.get('multi'))
          #  return " LINE 64"            
            if int(multi) > 0:
                beg_mo = int(request.form.get('mo'))
                mo_amt = float(expamount)/int(multi)
                for i in range(multi):   
                    insert_mo = (beg_mo + i ) % 12
              # OK      return "LINE 67"
                    d=request.form.get('yr')+'-'+ str(insert_mo) +'-'+request.form.get('day')   
               
               #  OK     return "LINE 68"
                    cur.execute("INSERT INTO expenses(exp_amount, exp_descr,exp_vendor,exp_cat,exp_date,user_id) VALUES (%s,%s,%s,%s,%s,%s)", (mo_amt,expdescr,expvendor,expcat,d,user_id, ))
                    
            else:
                d=request.form.get('yr')+'-'+request.form.get('mo')+'-'+request.form.get('day')   
                cur.execute("INSERT INTO expenses(exp_amount, exp_descr,exp_vendor,exp_cat,exp_date,user_id) VALUES (%s,%s,%s,%s,%s,%s)", (expamount,expdescr,expvendor,expcat,d,user_id, ))
            
            cur.close()
        

            if card_total:
                curCT = mysql.connection.cursor()
                ct = request.form.get('card_total')
            #    return "LINE 71"
                curCT.execute("INSERT INTO card_trans(ct_amount, ct_date,vendor,user_id,status) VALUES (%s,%s,%s,%s,%s)", (ct,d, expvendor,user_id,1, ))
                curCT.close()
            mysql.connection.commit()

            return redirect(url_for('new_expense'))
        d = dt.datetime.now()
        d_int= d.day #strftime("%d")
        m_int = d.month #strftime("%m")
        y_int = d.year #()  #strftime("%yyyy")

        return render_template("new_expense.html", month=m_int, day=d_int, year=y_int, ecats_list = ecats_list)


@app.route("/exp_rep_time", methods=['GET','POST'])
def exp_rep_time():
    form = ExpRepTime()
    if request.method=='POST':
        cur = mysql.connection.cursor()
        user_id=session['user_id'];
        bd=request.form.get('begin_date')
        ed=request.form.get('end_date')
        sqlSELECT ="SELECT e.exp_date, e.exp_amount,e.exp_descr,e.exp_vendor, c.category, e.expense_id FROM expenses e JOIN categories c on e.exp_cat = c.cat_id WHERE e.exp_date>=%s AND e.exp_date<=%s AND e.user_id = %s ORDER BY 1"
        cur.execute(sqlSELECT,(bd,ed,user_id,) )
        exps=cur.fetchall()
        cur.close()

        curCats=mysql.connection.cursor()
        sqlCATS ="SELECT SUM(e.exp_amount) as catTotal, c.category as cat FROM expenses e JOIN categories c on e.exp_cat = c.cat_id WHERE e.exp_date >=%s AND e.exp_date <=%s  AND e.user_id = %s GROUP BY c.category ORDER BY 2"
        curCats.execute(sqlCATS,(bd,ed,user_id,) )
        cats=curCats.fetchall()
        curCats.close()

        curTotal=mysql.connection.cursor()
        sqlTotal ="SELECT SUM(e.exp_amount) as expTotal FROM expenses e WHERE e.exp_date >=%s AND e.exp_date <=%s AND e.user_id=%s"
        curTotal.execute(sqlTotal,(bd,ed, user_id,) )
        tot=curTotal.fetchone()
        curTotal.close()
        
        if exps:
            return render_template('list_expenses.html', exps=exps,cats=cats,bd=bd,ed=ed,tot=tot) 
        else:
            return "No expenses found"

    return render_template('exp_rep_time.html',form=form)

@app.route("/exp_rep_cat", methods=['GET','POST'])
def exp_rep_cat():
    form = ExpRepTime()
    if request.method=='POST':
        cur = mysql.connection.cursor()
        user_id=session['user_id'];
        bd=request.form.get('begin_date')
        ed=request.form.get('end_date')
        #return "LINE `131"
    ######################################
    #  sqlSELECT ="SELECT e.exp_date, e.exp_amount,e.exp_descr,e.exp_vendor, c.category, e.expense_id FROM expenses e JOIN categories c on e.exp_cat = c.cat_id WHERE e.exp_date>=%s AND e.exp_date<=%s AND e.user_id = %s ORDER BY 1"
     #   cur.execute(sqlSELECT,(bd,ed,user_id,) )
      #  exps=cur.fetchall()
     #   cur.close()
 ####################################       

        curCats=mysql.connection.cursor()
        sqlCATS ="SELECT SUM(e.exp_amount) as catTotal, c.category as cat FROM expenses e JOIN categories c on e.exp_cat = c.cat_id WHERE e.exp_date >=%s AND e.exp_date <=%s  AND e.user_id = %s GROUP BY c.category ORDER BY 2"
        curCats.execute(sqlCATS,(bd,ed,user_id,) )
        cats=curCats.fetchall()
        curCats.close()

        curTotal=mysql.connection.cursor()
        sqlTotal ="SELECT SUM(e.exp_amount) as expTotal FROM expenses e WHERE e.exp_date >=%s AND e.exp_date <=%s AND e.user_id=%s"
        curTotal.execute(sqlTotal,(bd,ed, user_id,) )
        tot=curTotal.fetchone()
        curTotal.close()
        
        if cats:
            return render_template('list_expenses.html', cats=cats,bd=bd,ed=ed,tot=tot) 
        else:
            return "No expenses found"

    return render_template('exp_rep_time.html',form=form)



@app.route("/exp_today")
def exp_today():
        d=dt.datetime.now().date()   
        cur = mysql.connection.cursor()
        user_id=session['user_id'];
        sqlSELECT ="SELECT e.exp_date, e.exp_amount,e.exp_descr,e.exp_vendor, c.category, e.expense_id FROM expenses e JOIN categories c on e.exp_cat = c.cat_id WHERE e.exp_date=%s AND e.user_id = %s ORDER BY 1"
        cur.execute(sqlSELECT,(d,user_id,) )
        exps=cur.fetchall()
        cur.close()
        
        curTotal=mysql.connection.cursor()
        sqlTotal ="SELECT SUM(e.exp_amount) as expTotal FROM expenses e WHERE e.exp_date =%s AND e.user_id=%s"
        curTotal.execute(sqlTotal,(d, user_id,) )
        tot=curTotal.fetchone()
        curTotal.close()
        
        if exps:
            return render_template('list_expenses.html', exps=exps,d=d,tot=tot) 
        else:
            return "No expenses found"



@app.route("/expense_reports")
def expense_reports():
    form = ExpenseReportForm()
    return render_template('expense_reports.html', form=form)  


@app.route("/list_categories")
def list_categories():
    cur = mysql.connection.cursor()
    cur.execute('SELECT cat_id, category FROM categories WHERE user_id=%s',(session['user_id'],))
    cats=cur.fetchall()
    cur.close()
    return render_template("list_categories.html", cats=cats)



@app.route("/card_transactions", methods=['GET','POST'])
def card_transactions():
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    sqlCards = 'SELECT ct_date, ct_amount, vendor, ct_id  FROM card_trans WHERE status = 1 AND  user_id =%s';
    cur.execute(sqlCards,(user_id,))
    ct=cur.fetchall()
    cur.close()

    if request.method == 'POST':
        reconciled = request.form.get('reconciled')
        rec_list = reconciled.split(",")
        #return "176  " + str(rec_list[0]) + " " + str(rec_list[1])  + " " +   str(rec_list[2])
   
        if rec_list:
          #  v =  int(rec_list[0]) 
            curCTupdate = mysql.connection.cursor()
            sqlCTupdate = "UPDATE card_trans SET status = 2 WHERE ct_id = %s"
           
            for d in rec_list:
                v =  int(d)   
                      #rec_list[0]) 

                curCTupdate.execute(sqlCTupdate,(v,)) 
         #   return "LINE 190"
            
            mysql.connection.commit()

            return redirect(url_for('card_transactions'))

    if ct:
        return render_template("card_transactions.html", ct=ct)
    else:
        return "</h3>No card transactions for this user</h3>"



@app.route("/new_category", methods=['GET','POST'])
def new_category():
       # form = NewCatForm()
        user_id = session['user_id']
        ecats_list = []
        curEcats=mysql.connection.cursor()
        sqlEcats ="SELECT  c.category,c.cat_id FROM categories c  WHERE c.webshow=1 and c.user_id =%s ORDER BY 2"
        curEcats.execute(sqlEcats,(user_id,) )
        Ecats=curEcats.fetchall()
        curEcats.close()
        if Ecats:
            for c in Ecats: 
                ecats_list.append(c)
        else:
            ecats_list.append(('Misc.',99))
        if request.method=='POST':
         #   return "POST 172"
            cur = mysql.connection.cursor()
            newcat = request.form.get('new_category')
            #return newcat
            cur.execute("INSERT INTO categories(category, user_id,webshow,status) VALUES (%s,%s,%s,%s)", (newcat, user_id,1,1, ))
            cur.close()
        
            mysql.connection.commit()
            return redirect(url_for('new_category'))

        return render_template('new_category.html', ecats_list=ecats_list)  


@app.route("/list_ivendors")
def list_vendors():
    return render_template('list_vendors.html')  


@app.route("/new_vendor")
def new_vendor():
    return render_template('new_vendor.html')  



@app.route("/login", methods=['GET','POST'])
def login():
    form=LoginForm()
    error = None
    if form.validate_on_submit():
        
        login_username = request.form.get('username')
        login_pw = request.form.get('password')
        
        sqlDBpassword = 'SELECT user_id, first_name, last_name, password FROM users WHERE username =%s';
        curDBpassword = mysql.connection.cursor()
        curDBpassword.execute(sqlDBpassword,(login_username,))
        DBpassword=curDBpassword.fetchone()
        
     #  curDBpassword.close()
        if DBpassword:
            user_id = DBpassword[0]
            user_password = DBpassword[3]
            user_firstname = DBpassword[1]
            user_lastname = DBpassword[2]
            if user_password==login_pw:
              # return' <h2>Correct password</h2>'
                session['user_id'] = user_id
            #    session['logged_in']=True
                session['username']=login_username
                session['firstname']=user_firstname
                session['lastname']=user_lastname
                curDBpassword.close()
       
                return render_template('index.html', username=login_username)

            else:
                error="Unknown user/password"
            return render_template('login.html', form=form, error=error)
        
        else:
            error =  "Unknown user/password"
            return render_template('login.html', form=form, error=error)
 
        return render_template('index.html')
    return render_template('login.html', form=form, error=error)



@app.route('/register', methods=['GET', 'POST'])
def register():
    form=RegisterForm()
    if request.method == "POST":
        error = ""
        if form.validate_on_submit():
   #         return "register 241"
            username = form.username.data
            password = form.password.data
            firstname = form.firstname.data
            lastname = form.lastname.data
            secret = form.secret.data
     
            if secret == "k_maxx":

                cur = mysql.connection.cursor()
                registerSQL = ''' INSERT INTO users(first_name, last_name, username, password) VALUES (%s,%s,%s,%s)'''
                cur.execute(registerSQL, (firstname, lastname, username, password,))
                

                new_id = cur.lastrowid
           #     return "LINE 257" 
                cur.close()

                curCat = mysql.connection.cursor()
                catSQL = ''' INSERT INTO categories(category, user_id, webshow,status) VALUES (%s,%s,%s,%s)'''
                curCat.execute(catSQL, ('Misc.', new_id,1,1,))
                curCat.close()

            #    return  "<h3> 282 </h3>"
                mysql.connection.commit()
                return redirect(url_for('login'))

            else:
                return "<h3>The secret was just too secret.</h3>"
    return render_template('register.html', form=form)



@app.route("/dummy")
def dummy():
    return '<h2 style="color:navy" >/dummy</h2>'


@app.route("/new_item", methods=['GET','POST'])
def new_item():
        user_id = session['user_id']
        boxes_list = []
        curBoxes=mysql.connection.cursor()
        sqlBoxes ="SELECT b.box_id, b.box_label FROM boxes b ORDER BY 2"
        
        curBoxes.execute(sqlBoxes)
        bx =curBoxes.fetchall()
     #   return "351 new_item()"
        curBoxes.close()
        if bx:
     #       return "354 bx"
            for b in bx: 
                boxes_list.append(b)
    #    return "LINE 357"
    #  else:
      #      ecats_list.append(('Misc.',99))
    #    return ("357 new_item()")
        if request.method=='POST':
         #   return "POST 172"
            curItem = mysql.connection.cursor()
            new_item = request.form.get('new_item')
            #return newcat
            cur.execute("INSERT INTO items(item, box_id) VALUES (%s,%s)", (new_item, box_id, ))
            cur.close()
        
            mysql.connection.commit()

            return redirect(url_for('new_category'))
        return "LINE 372" 
        return render_template('new_item.html', boxes_list=boxes_list)  


@app.route("/logout")
def logout():

    if 'username' in session:
        session.pop('username')
    if 'user_id' in session:
        session.pop('user_id')
    if 'firstname' in session:
        session.pop('firstname')
    if 'lastname' in session:
        session.pop('lastname')
    return render_template("index.html")
    #<h2 style="color:navy" >Logged out</h2>'



if __name__ == "__main__":
    app.run(host='0.0.0.0')
