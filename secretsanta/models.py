from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User, UserManager

class Person(User):
	street_address_1 = models.CharField(max_length=255)
	street_address_2 = models.CharField(max_length=255, blank=True)
	zipcode = models.CharField(max_length=255)
	city = models.CharField(max_length=255)
	state = models.CharField(max_length=255)
	country = models.CharField(max_length=255)
	invited_by = models.ForeignKey('self', blank=True, null=True)
	
	objects = UserManager()
	
	def __unicode__(self):
		return self.first_name + " " + self.last_name
		
	def save(self):
		super(Person, self).save()
	

class InvitationCode(models.Model):
	requester = models.ForeignKey(Person, blank=True, null=True)
	email = models.CharField(max_length=255, blank=True, null=True)
	code = models.CharField(max_length=255, unique=True)
	
class PersonInvite(models.Model):
	invited_by = models.ForeignKey(Person)
	to_name = models.CharField(max_length=255)
	email = models.CharField(max_length=255)
	
admin.site.register(Person)
admin.site.register(InvitationCode)