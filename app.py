from flask import Flask,render_template,request,jsonify
from random import sample
import pandas as pd
import gatherer
import company
import logica
from scripts import tabledef
from scripts import forms
from scripts import helpers
from flask import  redirect, url_for,session
import json
import sys
import os
import stripe
stripe_keys = {'secret_key': 'sk_test_zwcBrhuUvfIVJNywkFwcvF3E00vOtHx8m4',
  'publishable_key':'pk_test_Z7rY6q9CPXqQVSpkmUh6xkMH00IS5uHmoT'
}

stripe.api_key = stripe_keys['secret_key']


app = Flask(__name__)
app.secret_key = os.urandom(12)
symbol = ""
start = ""
end = ""
data = pd.DataFrame()
comp_name = ""
###############################################
# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #
@app.route('/', methods=['GET', 'POST'])
def login():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = request.form['password']
            if form.validate():
                if helpers.credentials_valid(username, password):
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Login successful'})
                return json.dumps({'status': 'Invalid user/pass'})
            return json.dumps({'status': 'Both fields required'})
        return render_template('login.html', form=form)
    user = helpers.get_user()
    return render_template('home.html', user=user)


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('login'))


# -------- Signup ---------------------------------------------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('logged_in'):
        form = forms.LoginForm(request.form)
        if request.method == 'POST':
            username = request.form['username'].lower()
            password = helpers.hash_password(request.form['password'])
            email = request.form['email']
            if form.validate():
                if not helpers.username_taken(username):
                    helpers.add_user(username, password, email)
                    session['logged_in'] = True
                    session['username'] = username
                    return json.dumps({'status': 'Signup successful'})
                return json.dumps({'status': 'Username taken'})
            return json.dumps({'status': 'User/Pass required'})
        return render_template('login.html', form=form)
    return redirect(url_for('login'))


# -------- Settings ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if session.get('logged_in'):
        if request.method == 'POST':
            password = request.form['password']
            if password != "":
                password = helpers.hash_password(password)
            email = request.form['email']
            helpers.change_user(password=password, email=email)
            return json.dumps({'status': 'Saved'})
        user = helpers.get_user()
        return render_template('settings.html', user=user)
    return redirect(url_for('login'))

######################################################################"

@app.route('/')
def index():
	return render_template('main.html')

@app.route('/data',methods=["POST", 'GET'])
def data():

	global symbol
	global start
	global end
	global data
	global comp_name

	if request.method=='POST':
		print(request)
		# if symbol != request.form['search']:
		symbol = request.form['search']
		source = request.form['sourcery']
		start = request.form['trip-start']
		end = request.form['trip-end']

		data = gatherer.data(symbol, source, start, end)
		comp_name = company.get_symbol(symbol)
		return render_template("home1.html", key=stripe_keys['publishable_key'])
        
        

@app.route('/chart1')
def chart1():

	global start
	global end
	global data
	global comp_name

	dt, dd, mav, rets = logica.task1(data)
	print(type(dd))
	return render_template('chart1.html', stock_date=dt, stock_data=dd, mav=mav, company=comp_name, start=start, end=end)

@app.route('/chart2')
def chart2():

	global start
	global end
	global data
	global comp_name

	dt, dd, mav, rets = logica.task1(data)
	return render_template('chart2.html', stock_date=dt, rets=rets, company=comp_name, start=start, end=end)

@app.route('/chart3')
def chart3():

	global start
	global end
	global data
	global comp_name

	dt, dd, reg, pol2, pol3, knn, las, byr, lar, omp, ard, sgd = logica.task2(data)
	return render_template('chart3.html', stock_date=dt, stock_data=dd, reg=reg, pol2=pol2, pol3=pol3, knn=knn, las=las, byr=byr, lar=lar, omp=omp, ard=ard, sgd=sgd, company=comp_name, start=start, end=end)





# @app.route('/chart4')
# def chart4():

# 	global start
# 	global end
# 	global data
# 	global comp_name
	
# 	dt, dd, mav, rets = logica.task1(data)
# 	return render_template('chart4.html', stock_date=dt, rets=rets, company=comp_name, start=start, end=end)

# @app.route('/chart5')
# def chart5():

# 	global start
# 	global end
# 	global data
# 	global comp_name

# 	dt, dd, mav, rets = logica.task1(data)
# 	return render_template('chart5.html', stock_date=dt, rets=rets, company=comp_name, start=start, end=end)

# @app.route('/chart6')
# def chart6():

# 	global start
# 	global end
# 	global data
# 	global comp_name

# 	dt, dd, mav, rets = logica.task1(data)
# 	return render_template('chart6.html', stock_date=dt, rets=rets, company=comp_name, start=start, end=end)

# @app.route('/chart7')
# def chart7():

# 	global start
# 	global end
# 	global data
# 	global comp_name

# 	dt, dd, mav, rets = logica.task1(data)
# 	return render_template('chart7.html', stock_date=dt, rets=rets, company=comp_name, start=start, end=end)

@app.route('/stripeCharge', methods=['POST'])
def stripeCharge():
    try:
        amount = 500   # amount in cents
        customer = stripe.Customer.create(
            email='sample@customer.com',
            source=request.form['stripeToken']
        )
        stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency='usd',
            description='Diagnosis Charge'
        )
        #return render_template('stripeCharge.html', amount=amount)
        return chart1()
    except stripe.error.StripeError:
        return render_template('stripeError.html')


if __name__ == '__main__':
	app.run(debug=1, use_reloader=True)
    
    
#return render_template("stripeIndex.html", key=stripe_keys['publishable_key'])




