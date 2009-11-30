from django import forms
from django.contrib.auth.models import User
import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.localflavor.us.forms import USStateSelect
from django.contrib.localflavor.au.forms import AUStateSelect
from django.contrib.localflavor.br.forms import BRStateSelect
from django.contrib.localflavor.ca.forms import CAProvinceSelect
from django.contrib.localflavor.uk.forms import UKCountySelect

from djangosanta.countries.models import Country

class LoginForm(forms.Form):
	username = forms.EmailField(required=True)
	password = forms.CharField(widget=forms.PasswordInput, required=True)

class ResendForm(forms.Form):
	notrobot = forms.CharField(required=True)
	wordindex = forms.CharField(widget=forms.HiddenInput(), required=True)

class RequestForm(forms.Form):
	email = forms.EmailField(required=True)
	
class StateSelect(forms.Form):
	us = forms.CharField(widget=USStateSelect())
	au = forms.CharField(widget=AUStateSelect())
	br = forms.CharField(widget=BRStateSelect())
	ca = forms.CharField(widget=CAProvinceSelect())
	uk = forms.CharField(widget=UKCountySelect())	

class PersonForm(forms.ModelForm):
	
	def __init__(self, *args, **kwargs):
		super(PersonForm, self).__init__(*args, **kwargs)
		self.fields['country'].choices = [('US', 'United States')] + [(country.iso, country.printable_name) for country in Country.objects.all() if country.iso != 'US']
		
	email = forms.EmailField()
	username = forms.CharField(widget=forms.HiddenInput(), required=False)
	state = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput(render_value=False))
	country = forms.ChoiceField(
		choices=(), widget=forms.Select(),
	)
	date_joined = forms.CharField(widget=forms.HiddenInput(), required=False)
	last_login = forms.CharField(widget=forms.HiddenInput(), required=False)
	invite_code = forms.CharField(widget=forms.HiddenInput())
	invited_by = forms.CharField(widget=forms.HiddenInput(), required=False)
	
	def clean_email(self):
		"""
		Validates email address not already in use - one per please		   
		"""
		if self.cleaned_data.get('email', None):
			try:
				user = User.objects.get(email__exact=self.cleaned_data['email'])
			except User.DoesNotExist:
				return self.cleaned_data['email']
			raise forms.ValidationError(u'The email address "%s" is already registered.' %	self.cleaned_data['email'])
	
	class Meta:
		model = models.Person

class StartForm(forms.Form):
	email = forms.EmailField(required=True, label='Your e-mail')
	invite_code = forms.CharField(required=True, label='Invitation Code')

	def clean_invite_code(self):
		if self.cleaned_data.get('invite_code'):
			try:
				models.InvitationCode.objects.get(code=self.cleaned_data['invite_code'])
				return self.cleaned_data['invite_code']
			except ObjectDoesNotExist:
				raise forms.ValidationError(u"This doesn't look like a valid invite code")





