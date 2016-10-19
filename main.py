# [START app]
import logging

from flask import Flask, session, render_template, request, abort
import flask_cors
from google.appengine.ext import ndb
from decimal import Decimal
from uuid import uuid4

from car import Car

import firebase_helper

app = Flask(__name__)
flask_cors.CORS(app)

app.config['DEBUG'] = True

# Used for Flask session
app.secret_key='XMzRu);5bT<`1}]l5;INg![20+:6-s('


# [Auto loan calcalation functions]
def calculate_monthly_payment(principal, rate, loan_period):
	"""Returns monthly payment of auto loan

	This implements formula for computing car loan repayment
	The rate variable is given in decimal form, not percentage
	"""
	n = loan_period
	r = rate / 12
	monthly_payment = principal * (r * ((1+r) ** n)) / (((1+r) ** n) - 1)
	return monthly_payment


def calculate_car_data(car, mpd, cog, ir, lp):
	"""Modifies car object

	Car object is updated with car loan calculation data
	"""
	gallons_per_day = float(mpd) / car.mpg
	car.gallons_per_month = gallons_per_day * 30.44
	car.monthly_gas = gallons_per_day * float(cog) * 30.44

	A = calculate_monthly_payment(car.price, (float(ir) * 0.01), float(lp))

	car.monthly_payment = A
	car.true_cost = A * float(lp)

	car.monthly_cost = car.monthly_payment + car.monthly_gas


def prepare_cars_with_loan_data(cars):
	"""Modifies car objects in list

	If loan data has been provided and stored in session, calculate car data.
	If loan data has not been provided, return None.
	"""
	try:
		mpd = session['miles_per_day']
		cog = session['cost_of_gas']
		ir = session['interest_rate']
		lp = session['loan_period']
	
		for car in cars:
			calculate_car_data(car, mpd, cog, ir, lp)

		cars.sort(key=lambda x: x.monthly_cost, reverse=False)

		if cars:
			cheapest_price = cars[0].monthly_cost

		for car in cars:
			car.off_leader = cheapest_price - car.monthly_cost

	except KeyError:
		return None
# [END Auto loan calculation functions]



def render_content(template, request, get_perm):
	"""Returns render_template function

	Passes the appropriate data to the template.
	The "get_perm" variable defines if the caller of this function is 
	giving permission to get cars from the DB to be rendered.
	"""
	if get_perm:
		cars = user_car_filter(request)
	else:
		cars = []

	try:
		data = {
			"mpd": session['miles_per_day'], 
			"cog": session['cost_of_gas'], 
			"ir": session['interest_rate'], 
			"lp": session['loan_period']
		}

		return render_template(template, cars=cars, data=data)
  
 	except KeyError:
		return render_template(template, cars=cars)



# [Cars DB functions]
def query_db(sid):
	"""Returns all cars with matching parent key
	
	Cars are grouped by user if logged in.
	Otherwise, cars are grouped by session.
	The Car DB is guaranteed to be strongly consistent for each user and 
	for each session.
	"""
	ancestor_key = ndb.Key(Car, sid)
	cars = Car.query(ancestor=ancestor_key).order(-Car.mpg).fetch()
	return cars


def get_cars(sid):
	"""Returns list of cars belonging to user or session

	"sid" is either a user id or session id
	"""
	cars = query_db(sid)
	prepare_cars_with_loan_data(cars)
	return cars


def user_car_filter(request):
	"""Returns cars by user or by session

	If user is verified as logged in, returns user's cars.
	Otherwise the cars associated with the session are returned.
	"""
	try:
		claims = firebase_helper.verify_auth_token(request)
		if not claims:
			cars = get_cars(str(session['sid']))
		else:
			cars = get_cars(claims['sub'])
	except:
		cars = get_cars(str(session['sid']))

	return cars


def user_new_car_filter(request):
	"""Returns a new car object

	If the user is logged in, creates a new car using "subject" returned 
	by Firebase.
	Otherwise, creates a new car using session ID.
	"""
	try:
		claims = firebase_helper.verify_auth_token(request)
		if not claims:
			new_car = Car(parent=ndb.Key(Car, str(session['sid'])))
		else:
			new_car = Car(parent=ndb.Key(Car, claims['sub']))
	except:
		new_car = Car(parent=ndb.Key(Car,  str(session['sid'])))

	return new_car
# [END Cars DB functions]



# [Routing functions]
@app.route('/')
def root():
	"""Returns a rendered template of the car listing for the user or 
	the session.

	This function creates and sets a session ID if not done so already.
	"""
	if 'sid' not in session:
		session['sid'] = uuid4()

	return render_content('base.html', request, False)

@app.route('/data', methods=['POST'])
def data():
	"""Returns a rendered template of the car listing for the user or 
	the session.

	Stores the mutable user data in session variables.
	"""
	session['miles_per_day'] = request.form['miles_per_day']
	session['cost_of_gas'] = request.form['cost_of_gas']
	session['interest_rate'] = request.form['interest_rate']
	session['loan_period'] = request.form['loan_period']

	return render_content('car_data.html', request, True)

@app.route('/car', methods=['GET'])
def list_cars():
	"""Returns a rendered template of the car listing for the user or 
	the session.

	Refuse a request without a form submission
	"""
	try:
		test = request.args['name']
		return render_content('car_data.html', request, True)
	except:
		abort(403)


@app.route('/car', methods=['POST'])
def car():
	"""POST method adds new car to DB

	If user is logged in, a new car is stored belonging to the user.
	Otherwise, a new car is stored belonging to the session.
	"""
	new_car = user_new_car_filter(request)

	name = request.form['name']
	price = request.form['price']
	mpg = request.form['mpg']

	new_car.name = name
	new_car.price = int(price)
	new_car.mpg = int(mpg)
	new_car.sid = str(session['sid'])

	key = new_car.put()

	return render_content('car_data.html', request, True)

@app.route('/car', methods=['PUT'])
def deleteCar():
	"""Returns a rendered template of the car listing for the user or 
	the session.

	Deletes a car with associated key.
	"""
	car_key = request.form['car_key']
	car_entity = ndb.Key(urlsafe=car_key).get()
	car_entity.key.delete()

	return render_content('car_data.html', request, True)
# [END Routing functions]


# [Error Handlers]
@app.errorhandler(500)
def server_error(e):
	logging.exception('An error occurred during a request')
	return 'An internal error occurred', 500

@app.errorhandler(404)
def page_not_found(e):
	return 'Sorry. nothing at this URL', 404

@app.errorhandler(400)
def bad_request(e):
	return 'There was a bad request', 400
# [END Error Handlers]
# [END app]