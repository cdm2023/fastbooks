from flask import Flask, render_template, url_for, request, redirect, session, jsonify, g, flash 
from flask_mysqldb import MySQL
#from flask_wtf import Form
from forms import (ExpenseReportForm,ExpRepTime,
                   LoginForm,RegisterForm)
import datetime as dt
from  flask_bcrypt import Bcrypt

from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import yaml
#import datetime as dt
#from datetime import date

from datetime import datetime 
from datetime import date
from dateutil.relativedelta import relativedelta

import random

app = Flask(__name__)
bcrypt = Bcrypt(app)

db_conf = yaml.safe_load(open('db.yaml'))
maxx_conf = yaml.safe_load(open('maxx_config.yaml'))

app.config['SINGLE_LOCATION_MODE'] = maxx_conf['single_location_mode'] # True for Topeka771
app.config['SECRET_KEY'] =           maxx_conf['secret_key'] 
app.config['APP_WORLD'] =            maxx_conf['app_world'] 


if app.config['APP_WORLD'] ==  'colmena' :
    app.config['MYSQL_HOST'] =     db_conf['mysql_host']
    app.config['MYSQL_USER'] =     db_conf['mysql_user']
    app.config['MYSQL_PASSWORD'] = db_conf['mysql_password']
    app.config['MYSQL_DB'] =       maxx_conf['mysql_db']
    app.config['DEBUG'] =          db_conf['debug']

else:
    app.config['MYSQL_HOST'] =     db_conf['mysql_host']
    app.config['MYSQL_USER'] =     db_conf['mysql_user']
    app.config['MYSQL_PASSWORD'] = db_conf['mysql_password']
    app.config['MYSQL_DB'] =       db_conf['mysql_db']
    app.config['DEBUG'] =          db_conf['debug']

mysql = MySQL(app)
Bootstrap(app)


@app.route('/config_test')
def config_test():
    if app.config['SINGLE_LOCATION_MODE']:
        return  app.config['APP_WORLD'] 
    else:    
        return "NOT SINGLE_LOCATION_MODE"


def month_installments(beg_year,beg_month, beg_day, multi, total):
    #installments = []
    installment_amount = round(float(total)/float(multi),2)
    i_multi=int(multi)
    installments = []
    dt= str(beg_year) +'-'+  str(beg_month) +'-'+ str(beg_day)
    for i in range(i_multi):
        nx = datetime.strptime(dt, "%Y-%m-%d").date()
        next_installment_date = str(nx + relativedelta(months = + i) )
        installments.append([next_installment_date,installment_amount])
    return installments


@app.route('/multi_test')
def multi_test():    
    i_year = 2025
    i_month = 10 
    i_day = 30
    i_multi= 5 
    i_tot = 987.65
    installments = month_installments(i_year,i_month, i_day ,i_multi, i_tot)
   # return installments
    
    cur = mysql.connection.cursor()
    newcat =  'TEST_DELETE'
    next_date = '1999-1-1'
    cur.execute("INSERT INTO multi(m_date) VALUES (%s)", (next_date, ))
    cur.close()
    mysql.connection.commit()

    return "63 multi_test()"

@app.route("/")
def hello():
    return render_template("index.html")

@app.route("/formtest", methods=['GET','POST'])
def formtest():
    if 'user_id' in session:
        return render_template("new_expense.html")
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
        
        if int(multi) > 0:
            beg_year = request.form.get('yr')
            beg_month = request.form.get('mo')
            beg_day = request.form.get('day')   
            installment_amount = round(float(expamount)/float(multi),2)
            i_multi=int(multi)
            base_date = date(int(beg_year),int(beg_month),int(beg_day))
            for i in range(i_multi):
                next_installment_date = base_date + relativedelta(months=+i)

                cur.execute("INSERT INTO expenses(exp_amount, exp_descr,exp_vendor,exp_cat,exp_date,user_id) VALUES (%s,%s,%s,%s,%s,%s)", (installment_amount,expdescr,expvendor,expcat,next_installment_date,user_id, ))

        else:
            d=request.form.get('yr')+'-'+request.form.get('mo')+'-'+request.form.get('day')   
            cur.execute("INSERT INTO expenses(exp_amount, exp_descr,exp_vendor,exp_cat,exp_date,user_id) VALUES (%s,%s,%s,%s,%s,%s)", (expamount,expdescr,expvendor,expcat,d,user_id, ))
            
        cur.close()
        
        if float(card_total) > 0:
            curCT = mysql.connection.cursor()
            ct = card_total
            dd=request.form.get('yr')+'-'+request.form.get('mo')+'-'+request.form.get('day')   

            curCT.execute("INSERT INTO card_trans(ct_amount, ct_date,vendor,user_id,status) VALUES (%s,%s,%s,%s,%s)", (ct,dd, expvendor,user_id,1, ))
            curCT.close()
        mysql.connection.commit()

        return redirect(url_for('new_expense'))
#------------------------- end of "if POST" ------------------------
    d = datetime.now()
    d_int= d.day 
    m_int = d.month  
    y_int = d.year

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



@app.route("/exp_rep_group", methods=['GET','POST'])
def exp_rep_group():
    form = ExpRepTime()
    if request.method=='POST':
        cur = mysql.connection.cursor()
        user_id=session['user_id'];
        bd=request.form.get('begin_date')
        ed=request.form.get('end_date')
        sqlSELECT ="SELECT e.exp_date, e.exp_amount,e.exp_descr,e.exp_vendor, c.category, e.expense_id FROM expenses e JOIN categories c on e.exp_cat = c.cat_id WHERE e.exp_date>=%s AND e.exp_date<=%s AND e.user_id = %s ORDER BY 5,1"
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
    sqlCards = 'SELECT ct_date, ct_amount, vendor, ct_id  FROM card_trans WHERE status = 1 AND  user_id =%s ORDER BY ct_date';
    cur.execute(sqlCards,(user_id,))
    ct=cur.fetchall()
    cur.close()

    if request.method == 'POST':
        reconciled = request.form.get('reconciled')
        rec_list = reconciled.split(",")
        #return "176  " + str(rec_list[0]) + " " + str(rec_list[1])  + " " +   str(rec_list[2])
   
        if rec_list:
            curCTupdate = mysql.connection.cursor()
            sqlCTupdate = "UPDATE card_trans SET status = 2 WHERE ct_id = %s"
           
            for d in rec_list:
                v =  int(d)   
                curCTupdate.execute(sqlCTupdate,(v,)) 
            
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
            cur = mysql.connection.cursor()
            newcat = request.form.get('new_category')
            cur.execute("INSERT INTO categories(category, user_id,webshow,status) VALUES (%s,%s,%s,%s)", (newcat, user_id,1,1, ))
            cur.close()
            mysql.connection.commit()
            return redirect(url_for('new_category'))

        return render_template('new_category.html', ecats_list=ecats_list)  


@app.route("/list_vendors")
def list_vendors():
    return render_template('list_vendors.html')  


@app.route("/new_vendor")
def new_vendor():
    return render_template('new_vendor.html')  

def setSessionPerms(perms):
    if (perms & 4) > 0:
        session['can_manage_users']=True
    else:
        session['can_manage_users']=False

    if (perms & 8) > 0:
        session['user_can_search']=True
    else:
        session['user_can_search']=False



@app.route("/login", methods=['GET','POST'])
def login():
    form=LoginForm()
    error = None
    if form.validate_on_submit():
        #return "LINE 361"
 #       session['login_test'] = 'login_test'
     #   return "LINE 363"
 #       if 'login_test 'in session:
 #           return session
 #       else:
 #           return "login_test NOT IN SESSION"
        login_username = request.form.get('username')
        login_pw = request.form.get('password')
        
        sqlDBpassword = 'SELECT u.user_id, u.first_name, u.last_name, u.password, u.perms, l.location_id, l.location FROM users u JOIN locations l on (u.location_id=l.location_id) WHERE username =%s';
        curDBpassword = mysql.connection.cursor()
        curDBpassword.execute(sqlDBpassword,(login_username,))
        DBpassword=curDBpassword.fetchone()
     #  curDBpassword.close()
        if DBpassword:
            user_id = DBpassword[0]
            user_password = DBpassword[3]
            user_firstname = DBpassword[1]
            user_lastname = DBpassword[2]
            user_location_id = DBpassword[5]
            user_location = DBpassword[6]
            user_perms = DBpassword[4]
      #      return f"405 pws: {user_password},{login_pw},{DBpassword[3]}" 
            if user_password==login_pw:
                flash('Successful log-in') 
              # return' <h2>Correct password</h2>'
                session['user_id'] = user_id
            #    session['logged_in']=True
                session['username']=login_username
                session['location_id']=user_location_id
                session['locationd']=user_location
                session['firstname']=user_firstname
                session['lastname']=user_lastname
                session['user_perms']=user_perms
                curDBpassword.close()
                setSessionPerms(user_perms)
                #return "MILESTONE 418"        
               # if (user_perms & 8) > 0:
               #     session['user_can_search']=True
              #  else:
              #      session['user_can_search']=False
             #   return "MILESTONE 421"        
        #:q     return f"417 perms: { session['user_perms'] }" 
 #               return str(session)
              #  return f"388 session: {session}"      
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
            username = form.username.data
            password = form.password.data
            firstname = form.firstname.data
            lastname = form.lastname.data
            secret = form.secret.data
            perms=15
        if secret == "k_maxx":
                cur = mysql.connection.cursor()
                registerSQL = ''' INSERT INTO users(first_name, last_name, username, password,perms) VALUES (%s,%s,%s,%s,%s)'''
                cur.execute(registerSQL, (firstname, lastname, username, password,perms,))

                new_id = cur.lastrowid
                cur.close()

                curCat = mysql.connection.cursor()
                catSQL = ''' INSERT INTO categories(category, user_id, webshow,status) VALUES (%s,%s,%s,%s)'''
#                return f"MILESTONE 476 new_id: {new_id}"
                curCat.execute(catSQL, ('Misc.', new_id,1,1,))
 #               return f"MILESTONE 477 new_id: {new_id}"
                curCat.close()
  #              return f"MILESTONE 478 new_id: {new_id}"

                mysql.connection.commit()
   #             return "MILESTONE 481"
                return redirect(url_for('login'))

        else:
            return "<h3>The secret was just too secret.</h3>"
    return render_template('register.html', form=form)


@app.route("/birthday")
def birthday():
    return render_template('birthday.html')

@app.route("/dummy")
def dummy():
    return  render_template('dummy.html')


@app.route("/list_cells", methods=['GET','POST'])
def list_cells():

    if request.method == "POST":

        return "LINE 464 list_cells() POST NOT IMPLEMENTED should go to view_cell()?"
        user_id = session['user_id']
        cellID = request.form.get('cell_id')
        items_list = []
        curItems=mysql.connection.cursor()
        sqlCellName="SELECT cell_name FROM cells WHERE cell_id =%s"
        curItems.execute(sqlCellName,(cellID,))
        cellName = curItems.fetchone()
        cellName = cellName[0] 
        sqlItems ="SELECT i.item_id, i.item FROM items i WHERE i.cell_id = %s ORDER BY 2"
        curItems.execute(sqlItems,(cellID,))
        items =curItems.fetchall()
        curItems.close()
        return "LINE 477 list_cells() POST" + str(items)
        return render_template('view_cell.html', items=items, cell_id=cellID, cell_name=cellName)  

    #return "LINE 500 list_cells() GET"
    loc_id = session['location_id']
    sqlCells = 'SELECT cell_id, cell_name FROM cells WHERE location_id =%s';
    curCells = mysql.connection.cursor()
    curCells.execute(sqlCells, (loc_id, ))
    cells = curCells.fetchall()
    curCells.close()
   # return "507 list_cells() GET"
    return render_template('list_cells.html', cells=cells,loc_id=loc_id, xyz='xyz')  
#meth_lc = '489 list_cells() GET'


#@app.route("/list_cells", methods=['GET','POST'])
#def view_cells():
#    pass
#    if request.method=='POST':
#        loc_id = request.form.get('loc_id')
#        cell_list = []
#        sqlCells = 'SELECT cell_id, cell_name FROM cells WHERE location_id =%s';
#        curCells = mysql.connection.cursor()
#        curCells.execute(sqlCells, (loc_id, ))
#        cells = curCells.fetchall()
#        curCells.close()
#        if cells:
#            for c in cells:
#                cell_list.append(c)
#        return redirect(url_for('view_cells', cell_list=cell_list,loc_id=loc_id))
#    return "LINE 480"
#    locations_list = []
#    cur = mysql.connection.cursor()
#    cur.execute('SELECT location_id, location  FROM locations ORDER BY  2')
#    Locations=cur.fetchall()
#    cur.close()
#    if Locations:
#        for l in #Locations:
#            locations_list.append(l)

@app.route("/select_location", methods=['GET','POST'])
def select_location():
    session['algo'] = 'LINE 519/538 session[]'
 #   return f"Line 520: {session['algo']}"
    if request.method=='POST':
        loc_id = session['location_id']
        cell_list = []
        sqlCells = 'SELECT cell_id, cell_name FROM cells WHERE location_id =%s';
        curCells = mysql.connection.cursor()
        curCells.execute(sqlCells, (loc_id, ))
        cells = curCells.fetchall()
        curCells.close()
        #return f"LINE 520 select_location() POST: loc_id:{loc_id}  {cells}"
        if not cells:
            #     for c in cells:
        #        cell_list.append(c)
           # cell_list = return_list_from_cursor(cells)
       #     return f"LINE 525 select_location() POST: {cell_list}"
       # else:
            return "LINE 537 select_location() POST:  not cells"
        return render_template('list_cells.html', cells=cells,loc_id=loc_id, meth_sl=' 538 select_location() POST')

    locations_list = []
    cur = mysql.connection.cursor()
    cur.execute('SELECT location_id, location  FROM locations ORDER BY  2')
    Locations=cur.fetchall()
    cur.close()
    if Locations:
        for l in Locations:
            locations_list.append(l)
    return render_template("select_location.html", locations_list=locations_list, meth_sl ='549 select_location() GET')


@app.route("/add_location", methods=['GET','POST'])
def add_location():
       # form = NewCatForm()
        user_id = session['user_id']
        locations_list = []
        curLocations=mysql.connection.cursor()
        sqlLocations ="SELECT l.location_id,  l.location FROM locations l ORDER BY 2"
        curLocations.execute(sqlLocations )
        Locations=curLocations.fetchall()
        curLocations.close()
        if Locations:
            for l in Locations: 
                locations_list.append(l)
        else:
            locations_list.append(('Home',99))
        if request.method=='POST':
            cur = mysql.connection.cursor()
            newloc = request.form.get('new_location')
            cur.execute("INSERT INTO locations(location) VALUES (%s)", (newloc, ))
            cur.close()
            mysql.connection.commit()
            return redirect(url_for('add_location'))

        return render_template('add_location.html', locations_list=locations_list)  




@app.route("/add_cells", methods=['GET','POST'])
def add_cells():
       # form = NewCatForm()
    if request.method=='POST':
        cur = mysql.connection.cursor()
        new_cell = request.form.get('new_location')
        cur.execute("INSERT INTO locations(location) VALUES (%s)", (newloc, ))
        cur.close()
        mysql.connection.commit()
        return redirect(url_for('add_location'))

    if request.method=='POST':
        curItem = mysql.connection.cursor()
        cellID = request.form.get('cell_id')
        newitemSQL='''INSERT INTO items(item, cell_id) VALUES (%s,%s)'''                      
        new_item = request.form.get('new_item1')
    
    if request.method=="POST":    
        locID = request.form.get('loc_id')
        user_id = session['user_id']
        cells_list = []
        curCells=mysql.connection.cursor()
        sqlCells ="SELECT c.cell_id,  c.cell_name FROM cells c WHERE location_id = %s ORDER BY 2"
        curCells.execute(sqlCells, (locID,) )
        Cells=curCells.fetchall()
        curCells.close()
        return "LINE 550"
  #  if Cells:
  #          for c in Cells: 
  #            cells_list.append(l)
  #      else:
  #          cells_list.append(('Store'))
  #      if request.method=='POST':
  #          cur = mysql.connection.cursor()
  #          newcell = request.form.get('new_cell')
  #          cur.execute("INSERT INTO cells(cell) VALUES (%s)", (newcell, ))
  #          cur.close()
  #          mysql.connection.commit()
  #          return redirect(url_for('add_cells'))

        return render_template('add_cells.html', locations_list=locations_list)  

#@app.route("/show_cell", methods=['GET','POST'])
#def show_cell():
#    return "LINE 538 show_cell()"



@app.route("/view_cell", methods=['GET','POST'])
def view_cell():
    if request.method=='POST':
    #    return "LINE 630 view_cell() POST"
     

     #   curItem = mysql.connection.cursor()
     #   cellID = request.form.get('cell_id')
     #   newitemSQL='''INSERT INTO items(item, cell_id) VALUES (%s,%s)'''                      
     #   new_items = request.form.get('new_items')
     #   if new_items:
     #       items_in = new_items.split('and')
     #       for i in items_in:
     #           curItem.execute(newitemSQL, (i, cellID, ))
     #   curItem.close()
     #   mysql.connection.commit()

      #  loc_id = session['location_id']
      #  sqlCells = 'SELECT cell_id, cell_name FROM cells';
      #  curCells = mysql.connection.cursor()
      #  curCells.execute(sqlCells)
      #  cells = curCells.fetchall()
      #  curCells.close()
      #  return redirect(url_for('list_cells', meth_vc = '649 view_cell() POST')) 

        f_action = request.form.get('f_action')
        user_id = session['user_id']
        cellID = request.form.get('cell_id')
      #  return f"LINE 674 view_cell() GET cellID: {cellID}"
        items_list = []
        curItems=mysql.connection.cursor()
        sqlCellName="SELECT cell_name FROM cells WHERE cell_id =%s"
        curItems.execute(sqlCellName,(cellID,))
        cellName = curItems.fetchone()
        cellName = cellName[0] 
     #   return "LINE 681"
        sqlItems ="SELECT i.item_id, i.item_name FROM items i WHERE cell_id = %s ORDER BY 2"
     #   return "LINE 682"
        try:
            curItems.execute(sqlItems,(cellID,))
        except Exception as error:
            return error 

     #   return "LINE 684"
        its =curItems.fetchall()
        curItems.close()
      #  return (f"686 its:  {its}")
        #if its:
        #    for i in its: 
        #        items_list.append(i)
        return render_template('view_cell.html', items_list=its, cell_id=cellID, cell_name=cellName)  


@app.route('/add_items', methods=["GET","POST"])
def add_items():
    #return redirect(url_for('list_cells')) 

    if request.method=='POST':
   #     return "LINE 680 add_items() POST"
        curItem = mysql.connection.cursor()
        cellID = request.form.get('cell_id')
        f_action = request.form.get('f_action')
        newitemSQL='''INSERT INTO items(item_name, cell_id) VALUES (%s,%s)'''                      
        new_items = request.form.get('new_items')
        if new_items:
            items_in = new_items.split('and')
            for i in items_in:
                curItem.execute(newitemSQL, (i, cellID, ))
        curItem.close()
        mysql.connection.commit()
      #  return f"716 add_items() {new_items} POST"
        loc_id = session['location_id']
        sqlCells = 'SELECT cell_id, cell_name FROM cells WHERE location_id = %s';
        curCells = mysql.connection.cursor()
        curCells.execute(sqlCells,(loc_id,))
        cells = curCells.fetchall()
        curCells.close()
    #    return f"723 add_items() POST"
        return redirect(url_for('list_cells')) 

        #return render_template('list_cells.html', cells=cells,loc_id=loc_id)
        

    user_id = session['user_id']
    cellID = request.form.get('cell_id')
    return "LINE 675 should not ever be here  view_cell() GET cell_id="+ cellID
    items_list = []
    curItems=mysql.connection.cursor()
    sqlCellName="SELECT cell_name FROM cells WHERE cell_id =%s"
    curItems.execute(sqlCellName,(cellID,))
    cellName = curItems.fetchone()
    cellName = cellName[0] 

    sqlItems ="SELECT i.item_id, i.item_name FROM items i WHERE cell_id = %s ORDER BY 2"
    curItems.execute(sqlItems,(cellID,))
    items =curItems.fetchall()
    curItems.close()
    return render_template('view_cell.html', items=items, cell_id=cellID, cell_name=cellName,f_aciont=f_action)  
   



# curItems=mysql.connection.cursor()
   # sqlItems ="SELECT i.item_id, i.item FROM items i WHERE cell_id = %s ORDER BY 2"
   # curItems.execute(sqlItems,(cellID,))
   # its =curItems.fetchall()
   # curItems.close()
   # if its:
   #     for i in its: 
  #          items_list.append(i)

       # mysql.connection.commit()

 #   loc_id = session['location_id']
        #cell_list = []
        
  #      if session['location_id'] == 5:
  #          sqlCells = 'SELECT cell_id, cell_name, serial_number FROM cells WHERE location_id =%s';

   #     else:
   #         sqlCells = 'SELECT cell_id, cell_name FROM cells WHERE location_id =%s';
   #     curCells = mysql.connection.cursor()
   #     curCells.execute(sqlCells, (loc_id, ))
   #     cells = curCells.fetchall()
   #     curCells.close()
   #     if cells:
   #         cell_list = return_list_from_cursor(cells)
          #  for c in cells:
           #     cell_list.append(c)

    #    return "LINE 602 " + str(cell_list) 
        #return render_template('add_items.html', items_list=items_list, cell_id=cellID)  
     #   return render_template('list_cells.html', cell_list=cell_list,loc_id=loc_id)
            #return render_template(url_for('show_cell'))  

@app.route("/vg_index")
def vg_index():
    return render_template("vg_index.html")


@app.route("/item_search", methods=["GET","POST"])
def item_search():
    if not (session['user_can_search']):
        return "<h3 style='color:#9C3020'> 797 User not permitted to search for items</h3>"
    if request.method == "POST":
        curSearch = mysql.connection.cursor()
        search_by_in = request.form.get('search_term')
        search_by_param = search_by_in.upper()       
        search_by_param = '%'+ search_by_param + '%'       
        sqlSearch = f"SELECT i.item_id, i.item_name, i.serial_number, i.product_number, c.cell_name FROM items i JOIN cells c on i.cell_id=c.cell_id WHERE i.item_upcase LIKE '{search_by_param}'"
        curSearch.execute(sqlSearch)
        found_items = curSearch.fetchall()
        curSearch.close()
        return render_template("found_items.html", search_by=search_by_in, found_items=found_items)
    return render_template("item_search.html")



@app.route("/list_inventory", methods=["GET","POST"])
def list_inventory():
    curSearch = mysql.connection.cursor()
    sqlSearch = "SELECT i.item_id, i.item_name, i.serial_number, i.product_number, c.cell_name FROM items i JOIN cells c on i.cell_id=c.cell_id ORDER BY 2"
    curSearch.execute(sqlSearch)
    found_items = curSearch.fetchall()
    curSearch.close()
    return render_template("list_inventory.html", found_items=found_items, by_cell=False)


@app.route("/list_cells_inventory", methods=["GET","POST"])
def list_cells_inventory():
    curSearch = mysql.connection.cursor()
    sqlSearch = "SELECT i.item_id, i.item_name, i.serial_number, i.product_number, c.cell_name FROM items i JOIN cells c on i.cell_id=c.cell_id ORDER BY 5,2"
    curSearch.execute(sqlSearch)
    found_items = curSearch.fetchall()
    curSearch.close()
   # return f"819 {found_items}"
    return render_template("list_inventory.html", found_items=found_items,by_cell=True)



@app.route("/propose_transfer", methods=['GET','POST'])
def propose_transfer():
    itemID = request.form.get('item_id')
    targetCell_id = request.form.get('target_cell_id')
    fromCell_id = request.form.get('from_cell_id')
  #  return "checkpoint 815 "


#========================       GET item_name, serial_number ('item_data')  to display in confirm_transfer.html     ==================================
#========================       GET cell_name[s] to display ....    =====================================================
    curFactotum = mysql.connection.cursor()
    sqlItem = "SELECT item_id, item_name, serial_number FROM  items WHERE item_id = %s"
    curFactotum.execute(sqlItem,(itemID,)) 
    item_data = curFactotum.fetchone()
 #   return "checkpoint 823 "   
                  
    sqlCelldata = "SELECT cell_id, cell_name FROM cells WHERE cell_id = %s"
    curFactotum.execute(sqlCelldata,(fromCell_id,));
    from_cell_data = curFactotum.fetchone()
 #   return "checkpoint 828 "   

    curFactotum.execute(sqlCelldata,(targetCell_id,));
    to_cell_data = curFactotum.fetchone()

    curFactotum.close()
   # return f"834 item_data: {item_data} from: {from_cell_data} to: {to_cell_data}"
    return render_template("propose_transfer.html", item_data=item_data, from_cell_data = from_cell_data, to_cell_data=to_cell_data)

     #   return str(itemID) 


@app.route("/confirm_transfer", methods=['GET','POST'])
def confirm_transfer():

    if request.method=='POST':
# ===========================      INSERT TRANSFER   =====================================
        itemID =        request.form.get('item_id')
        targetCell_id = request.form.get('to_cell_id')
        fromCell_id =   request.form.get('from_cell_id')
        notes =         request.form.get('notes')
        user_id =       session['user_id']
        now = datetime.now()
        t_date = now.strftime('%Y-%m-%d')
        curTransfer = mysql.connection.cursor()
        sqlTransfer='''INSERT INTO transfers(item_id,user_id, target_cell_id, source_cell_id, trans_date, notes) VALUES (%s,%s,%s,%s,%s,%s)'''                      
        curTransfer.execute(sqlTransfer, (itemID,user_id,targetCell_id,fromCell_id,t_date , notes, ))
        #mysql.connection.commit()
#        return "checkpoint 838 "   
#========================       GET item_name, serial_number ('item_data')  to display in confirm_transfer.html     ==================================
#========================       GET cell_name[s] to display ....    =====================================================
        curFactotum = mysql.connection.cursor()
        sqlItemID = "SELECT item_name, serial_number FROM  items WHERE item_id = %s"
        curFactotum.execute(sqlItemID,(itemID,)) 
        item_data = curFactotum.fetchone()
#        return "checkpoint 845 "   
                  
        sqlCellname = "SELECT cell_name FROM cells WHERE cell_id = %s"
        curFactotum.execute(sqlCellname,(fromCell_id,));
        from_cell_data = curFactotum.fetchone()
#        return "checkpoint 850 "   

        curFactotum.execute(sqlCellname,(targetCell_id,));
        to_cell_data = curFactotum.fetchone()

        curFactotum.close()
#        return f"846 item_data: {item_data} from: {from_cell_data} to: {to_cell_data}"

#========================       UPDATE cell_id IN items TABLE     ==================================

        curItemUpdate = mysql.connection.cursor()
        sqlItemUpdate = "UPDATE items SET cell_id = %s WHERE item_id = %s"
        curItemUpdate.execute(sqlItemUpdate,(targetCell_id,itemID,)) 
        mysql.connection.commit()
        curItemUpdate.close()
     #   return "checkpoint 865 "   
   
      
#========================       DISPLAY DETAILS OF THE TRANSFER:  ===================================
        curLastID=mysql.connection.cursor()
        curLastID.execute('SELECT LAST_INSERT_ID()')
        last_id = curLastID.fetchone()
        curLastID.close()
  #      return "checkpoint 873 "   

        curTransfer=mysql.connection.cursor()
        sqlTransfer ="SELECT c1. cell_name as from_cell, c2.cell_name as to_cell, t.trans_date, t.notes FROM  transfers t join cells c1 on (t.source_cell_id=c1.cell_id)  join cells c2 on (t.target_cell_id=c2.cell_id)  WHERE t.transfer_id = %s"

#+-----------+----------+------------+-------------------------+------------+-----------+
#| from_cell | to_cell  | trans_date | notes                   | first_name | last_name |
#+-----------+----------+------------+-------------------------+------------+-----------+
#| Cage 3-A  | Cage 3-A | 2023-09-09 |  Needed some wheedling. | Sharon     | Faurot    |
#+-----------+----------+------------+-------------------------+------------+-----------+

        curTransfer.execute(sqlTransfer,(last_id,) )
#        return "checkpoint 885 "   
        db_transfer = curTransfer.fetchone()
        curTransfer.close()
#        return "checkpoint 889 "   
        return render_template('confirm_transfer.html', db_transfer=db_transfer,item_data=item_data,to_cell_data=to_cell_data, from_cell_data=from_cell_data)



@app.route("/show_item", methods=['GET','POST'])
def show_item():
#  =========== get the item details to display  ================== 
    itemID = request.form.get('item_id')
   #     return f"876 itemID: { itemID }" 
    curItem=mysql.connection.cursor()
    sqlItem = 'SELECT i.item_id, i.cell_id, i.item_name, i.serial_number, i.product_number, c.cell_name FROM items i JOIN cells c on i.cell_id=c.cell_id WHERE i.item_id =%s ORDER BY 2';
    curItem.execute(sqlItem,(itemID,))
    item =curItem.fetchone()
    curItem.close()
       # return "LINE 886 the request object? " + str(item)

#============= get the cells for selection for possible transfer  ==============
    loc_id = session['location_id']
    curCells=mysql.connection.cursor()
    sqlCells ="SELECT c.cell_id,  c.cell_name FROM cells c WHERE  c.location_id = %s ORDER BY 2"
    curCells.execute(sqlCells, (loc_id,) )
    cells = curCells.fetchall()
#        return "LINE 896 " + str(cells)
    curCells.close()

# ================   get the item's transfer history for display   =====================    
    curTransfers=mysql.connection.cursor()
    sqlTransfers ="SELECT c1. cell_name as from_cell, c2.cell_name as to_cell, t.trans_date, t.notes, u.first_name, u.last_name FROM  transfers t join cells c1 on (t.source_cell_id=c1.cell_id)  join cells c2 on (t.target_cell_id=c2.cell_id) join users u on (u.user_id=t.user_id) WHERE t.item_id = %s" 
#+-----------+----------+------------+-------------------------+------------+-----------+
#| from_cell | to_cell  | trans_date | notes                   | first_name | last_name |
#+-----------+----------+------------+-------------------------+------------+-----------+
#| Cage 3-A  | Cage 3-A | 2023-09-09 |  Needed some wheedling. | Sharon     | Faurot    |
#+-----------+----------+------------+-------------------------+------------+-----------+
    curTransfers.execute(sqlTransfers, (itemID,) )
   
    transfers = curTransfers.fetchall()
    curTransfers.close()
    return render_template('show_item.html', item=item,  cells=cells, transfers=transfers) 



@app.route('/add_inventory', methods = ["GET","POST"])
def add_inventory():
    if request.method == 'POST':
        res_list = []
        br = request.form.get('brand')
        mo = request.form.get('model')
        sn = request.form.get('serial')
        pn = request.form.get('product')
   #     return "LINE 855 " + str( pn)
        res_list.append(br)
        res_list.append(mo)
        res_list.append(sn)
        res_list.append(pn)
#  NEw INVENTORY:  CELL_ID ==1        

        user_id = session['user_id']
        loc_id =  session['location_id']
        now = datetime.now()
        t_date = now.strftime('%Y-%m-%d')
        curNewInv = mysql.connection.cursor()
        if session['location_id'] == 5 :  # Topeka #771
            sqlNewInv='''INSERT INTO items(item_name,brand, serial_number, product_number,user_id, cell_id, location_id, last_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''                 
            curNewInv.execute(sqlNewInv, (mo, br, sn, pn, user_id, 1, loc_id, t_date, ))

       
#~~~~~~~~~~~~~~~~~~~~~~~~  RECORD "TRANSFER" FOR  NEW ITEM  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

        curLastID=mysql.connection.cursor()
        curLastID.execute('SELECT LAST_INSERT_ID()')
        last_id = curLastID.fetchone()
        curLastID.close()
        
        targetCell_id = 1  # 1="new inventory"
        fromCell_id   = 2 # 2= svpw
        user_id =       session['user_id']
        now = datetime.now()
        t_date = now.strftime('%Y-%m-%d')
        notes = 'New inventory from SVPW'
        curTransfer = mysql.connection.cursor()
        if session['location_id'] == 5 :  # Topeka #771
            sqlTransfer='''INSERT INTO transfers(item_id,user_id, target_cell_id, source_cell_id, trans_date, notes) VALUES (%s,%s,%s,%s,%s,%s)'''                      
            curTransfer.execute(sqlTransfer, (last_id, user_id, targetCell_id, fromCell_id,t_date, notes, ))
        mysql.connection.commit()
    
        
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        mysql.connection.commit()
        return render_template('add_inventory.html', res_list=res_list)
    
    return render_template('add_inventory.html')


@app.route('/barcodetest', methods= ['GET','POST'])
def barcodetest():
    
    if request.method=="POST":
     #   n=random.randrange(1,100)  
        bc=request.form.get('barcode')
        sn=request.form.get('serial')
        pn=request.form.get('prod')
     #   bc += ': ' + str(n)
        return render_template('barcodetest.html', barcode = bc, serial = sn, prod=pn)
   
    return render_template('barcodetest.html', barcode='804', serial='', prod='')

@app.route("/logout")
def logout():

    session.clear()
#    if 'location' in session:
#        session.pop('location')
#    if 'location_id' in session:
#        session.pop('location_id')
#    if 'username' in session:
#        session.pop('username')
#    if 'user_id' in session:
#        session.pop('user_id')
#    if 'firstname' in session:
#        session.pop('firstname')
#    if 'lastname' in session:
#        session.pop('lastname')

    return render_template("index.html")


def return_list_from_cursor(cur):
    if cur:
        ret = []
        for i in cur:
            ret.append(i)
        return ret
    else:
        return None

@app.route('/session_test')
def session_test():
    session['whassup']='meretricious'
    return render_template("dummy.html", session=session) 

@app.route('/background_test')
def background_test():
    return render_template('vg_base.html')

@app.route("/func_test")
def func_test():
        locID = 5 
        user_id = 1 
        #cells_list = []
        curCells=mysql.connection.cursor()
        sqlCells ="SELECT c.cell_id,  c.cell_name FROM cells c WHERE location_id = %s ORDER BY 2"
        with curCells as cC:
      #  curCells.execute(sqlCells, (locID,) )
       # Cells=curCells.fetchall()
        #curCells.close()
            cC.execute(sqlCells, (locID,) )
            Cells=cC.fetchall()
            cC. close()
        cells_list = return_list_from_cursor(Cells)
        return cells_list
   
@app.route('/coltest')
def col_add_item():
    return render_template('coltest/add_item.html')
    #return render_template('add_item.html')


#THIS DOES NOT WORK in DigitalOcean fastbooks-as-service....
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404




if __name__ == "__main__":
      app.run(host='0.0.0.0')
