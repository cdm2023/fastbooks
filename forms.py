from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, DecimalField,SubmitField,PasswordField, RadioField, BooleanField, DateField, SelectField)
from wtforms.validators import InputRequired, Length,EqualTo 

class ExpenseForm(FlaskForm):
    exp_date= DateField('Date', validators=[InputRequired()])
    exp_amount = DecimalField('Amount',validators=[InputRequired()])
    exp_descr = StringField('Description',validators=[InputRequired()])
    
  #  exp_cat = IntegerField('Exp cat', validators=[InputRequired()])
    exp_cat = SelectField("Category", coerce=int)
    exp_vendor =  StringField('Vendor',validators=[InputRequired()])
    btnSubmit = SubmitField('Save expense')


class ExpenseReportForm(FlaskForm):
    beginMonth = RadioField('Starting', choices=[('1','January'), ('2','February'), ('3','March'), ('4','April'),  ('5','May'),
        ('6','June'), ('7','July'), ('8','August'), ('9','September'), ('10','October'), ('11','November'), ('12','December')  ])
    endMonth = RadioField('Ending', choices=[('1','January'), ('2','February'), ('3','March'), ('4','April'),  ('5','May'),
        ('6','June'), ('7','July'), ('8','August'), ('9','September'), ('10','October'), ('11','November'), ('12','December')  ])
    begin_day = IntegerField('begin_day', validators=[InputRequired()])
    end_day = IntegerField('end_ day', validators=[InputRequired()])
    orderBy = RadioField('Order by', choices=[('exp_date','Date'), ('exp_amount','Amount'), ('exp_cat','Category')  ])


    showMonthTotals = BooleanField('Show totals per month',  default=False)
    showVendorTotals = BooleanField('Show totals per vendor', default=False)
    showCatTotals = BooleanField('Show totals per category', default=False)


class ExpRepTime(FlaskForm):
 #   begin_date = DateField('Begin date', format="%Y/%m/%d")
 #   end_date =   DateField('End date',   format="%Y/%m/%d")
    begin_date = DateField('Begin date', format="%Y/%m/%d", validators=[InputRequired()])
    end_date =   DateField('End date',   format="%Y/%m/%d", validators=[InputRequired()])
    btnSubmit =  SubmitField('Get report')

class ExpenseReportFormTEST(FlaskForm):
    begin_day = IntegerField('Month')
    end_day = IntegerField('Day')
    beginMonth = RadioField('Starting', choices=[('1','January'), ('2','February'), ('3','March'), ('4','April'),  ('5','May'),
        ('6','June'), ('7','July'), ('8','August'), ('9','September'), ('10','October'), ('11','November'), ('12','December')  ])
   
   #exp_year = IntegerField('Year', validators=[InputRequired()])
   # exp_amount = DecimalField('Amount',validators=[InputRequired()])
   # exp_descr = StringField('Description',validators=[InputRequired()])
   # exp_cat = IntegerField('Exp cat', validators=[InputRequired()])
   # exp_vendor =  StringField('Vendor',validators=[InputRequired()])
   # btnSubmit = SubmitField('Save expense'

class LoginForm(FlaskForm):
    username=    StringField("Username",  validators=[InputRequired(), Length(min=3,max=25)])
    password=PasswordField("Password",    validators=[InputRequired(), Length(min=4,max=50)])


class NewCat(FlaskForm):
    newcat =    StringField("New category",  validators=[InputRequired(), Length(min=3,max=25)])

class NewItem(FlaskForm):
    new_item  =    StringField("New item",  validators=[InputRequired(), Length(min=3,max=35)])

class RegisterForm(FlaskForm):
    firstname=StringField("First name", validators = [InputRequired()])
    lastname=StringField("Last name",   validators = [InputRequired()])
    username=StringField("User name",   validators = [InputRequired(), Length(min=4, max=25)])
   # email=EmailField("Email", [validators.Required()])
    secret=StringField("Secret key",   validators = [InputRequired()])
    password=PasswordField("New password", validators = [InputRequired(),
                                            EqualTo('confirm',message='Passwords must match'),
                                            Length(min=4,max=50)])
    confirm = PasswordField("Repeat password")




