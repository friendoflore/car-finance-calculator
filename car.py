from google.appengine.ext import ndb

class Car(ndb.Model):
	sid = ndb.StringProperty(required=True)
	name = ndb.StringProperty(required=True)
	mpg = ndb.IntegerProperty(required=True)
	price = ndb.IntegerProperty(required=True)

