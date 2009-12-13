from django.db import models
from django.contrib import admin
from datetime import date
from django.contrib.auth.models import User, UserManager

class Person(User):
	street_address_1 = models.CharField(max_length=255)
	street_address_2 = models.CharField(max_length=255, blank=True)
	zipcode = models.CharField(max_length=255)
	city = models.CharField(max_length=255)
	state = models.CharField(max_length=255)
	country = models.CharField(max_length=255)
	
	objects = UserManager()
	
	def __unicode__(self):
		return self.first_name + " " + self.last_name
		
	def save(self):
		super(Person, self).save()
		

class Interests(models.Model):
	
	interest_1 = models.CharField(max_length=255)
	interest_2 = models.CharField(max_length=255)
	interest_3 = models.CharField(max_length=255)
	person = models.ForeignKey(Person)
	
	def all_interests(self):
		return [self.interest_1, self.interest_2, self.interest_3]	

class InvitationCode(models.Model):
	requester = models.ForeignKey(Person, blank=True, null=True)
	email = models.CharField(max_length=255, blank=True, null=True)
	code = models.CharField(max_length=255, unique=True)
	
class PersonInvite(models.Model):
	invited_by = models.ForeignKey(Person)
	to_name = models.CharField(max_length=255)
	email = models.CharField(max_length=255)
	
class Group(models.Model):
	code = models.ForeignKey(InvitationCode, blank=True, null=True)
	owner = models.ForeignKey(Person, related_name='owner')
	drawing = models.DateField()
	name = models.CharField(max_length=255)
	members = models.ManyToManyField(Person)
	active = models.BooleanField(default=True)
	def get_days(self):
		return (self.drawing - date.today()).days
		
	def get_drawing(self):
		return self.drawing

	
admin.site.register(Person)
admin.site.register(InvitationCode)
admin.site.register(Interests)