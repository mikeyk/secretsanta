"""
	TODO: 
		- write logout template
		- style errors
		- Twitter link
"""

from datetime import datetime, date
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as do_login
from django.core.mail import send_mail
from django.template import RequestContext
from django.template.loader import get_template
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import urllib, urllib2
import random
import forms
import strings
import simplejson as json
from models import Person, InvitationCode
from invitecode import generate_code

def path_processor(request):
    return {'path': request.path}

def render(request, template_name, context={}):
	template = get_template(template_name)
	context = RequestContext(request, context, [path_processor])
	return HttpResponse(template.render(context))

def login(request):
	
	if request.method == "POST":
		form = forms.LoginForm(data=request.POST)
		if form.is_valid():
			user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
			if user:
				do_login(request, user)
				return HttpResponseRedirect(request.GET.get('next','/'))
			else:
				form.errors['_all'] = "NOOOO"
	else:
		form = forms.LoginForm()
	return render(request, 'login.html', {'form': form})

def create(request):
	
	# validate invite code
	if request.method == "POST":
		form = forms.PersonForm(data=request.POST)
		if form.is_valid():
			try:
				# look up who invited them
				code_obj = InvitationCode.objects.get(code=form.cleaned_data['invite_code'])
				if code_obj.requester:
					form.cleaned_data['invited_by'] = code_obj.requester.id
				else:
					form.cleaned_data['invited_by'] = None
			except ObjectDoesNotExist:
				form.cleaned_data['invited_by'] = None
			form.cleaned_data['date_joined'] = datetime.now().strftime("%Y-%m-%d %H:%M")
			form.cleaned_data['last_login'] = datetime.now().strftime("%Y-%m-%d %H:%M")
			form.cleaned_data['username'] = form.cleaned_data['email']

			person = form.save()

			user = User.objects.get(username__exact=person.username)
			user.set_password(form.cleaned_data['password'])
			user.save()
		
			user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
			do_login(request, user)
		
			request.session['person'] = person
			return HttpResponseRedirect(reverse(invite_friends))
	else:
		if request.GET.get("i"):
			invite_code = request.GET['i']
			email = ""
		elif request.session.get('invite_code'):
			invite_code = request.session['invite_code']
			email = request.session.get('email')
		else:
			# TODO error
			invite_code = ""
			email = ""		
		form = forms.PersonForm(label_suffix="", initial={'invite_code':invite_code, 'email':email})
	state_select = forms.StateSelect()
	return render(request, 'create.html', {'form': form, 'state_select': state_select})


def shorten_url(url):
	create_api = 'http://api.bit.ly/shorten'
	try:
		# based on Bittle's calls
		data = urllib.urlencode(dict(version="2.0.1", longUrl=url, login=settings.BITLY_LOGIN, apiKey=settings.BITLY_API_KEY, history=1))
		link = json.loads(urllib2.urlopen(create_api, data=data).read().strip())
	
		if link["errorCode"] == 0 and link["statusCode"] == "OK":
			results = link["results"][url]
			return results['shortUrl']
		else:
			return url
	finally:
		return url	
	
@login_required
def invite_friends(request):
	# first check if they already have a generated invite_code
	try:
		invite = InvitationCode.objects.get(requester=request.user)
	except ObjectDoesNotExist:
		# TODO final string
		invite = InvitationCode()
		invite.requester = request.user
		invite.email = request.user.email
		code = generate_code(3)
		# TODO put this in a while?
		try:
			invite.code = code
			invite.save()
		# On duplicate...try again
		except IntegrityError:
			invite.code = generate_code(3)
			invite.save()		
	
	url = "http://santa.com?i=%s" % invite.code
	short_url = shorten_url(url)
	if not short_url: short_url = url
	tweet = "Join my Secret Santa group at %s" % short_url
	fb_link = url
	return render(request, 'invitefriends.html', {'tweet': tweet, 'fb_link': fb_link})
	
def confirm_request(request):
	if request.method == "POST":
		form = forms.StartForm(data=request.POST)
		if form.is_valid():
			invite_code = form.cleaned_data['invite_code']
			email = form.cleaned_data['email']
			if invitecode_valid(invite_code):
				request.session['invite_code'] = invite_code
				request.session['email'] = email
				return HttpResponseRedirect(reverse(create))
			else:
				# handle invalid
				pass
	else:
		email = request.session['email']
		form = forms.StartForm(initial={'email':email})
	return render(request, 'confirmrequest.html', {'form': form, 'email': email})
	
def fetch_gift_suggestions(keywords):
	# keyword_tokens = [x.strip() for x in keywords.split(',')]
	data = urllib.urlencode(dict(api_key=settings.ETSY_API_KEY, max_price=25, sort_on='score', limit=50))
	url = "http://beta-api.etsy.com/v1/listings/keywords/%s?%s" % (keywords.replace(" ", "%20"), data)
	results = json.loads(urllib2.urlopen(url).read().strip())
	return results['results']
	
def gift_suggestions(request, keyword):
	results = fetch_gift_suggestions(keyword)
	return render(request, 'giftsuggestions.html', {'results': results, 'keyword':keyword})
	
	
def resend_invite(request):
	
	words = ["apple", "banana", "orange", "strawberry"]
	if request.method == "POST":
		form = forms.ResendForm(data=request.POST)
		if form.is_valid():
			index = int(form.cleaned_data['wordindex'])
			if words[index] == form.cleaned_data['notrobot']:
				email_lookup = InvitationCode.objects.get(email=request.session['email'], requester=None)
				url = "http://%s/create?i=%s" % (request.get_host(), email_lookup.code)
				send_mail(strings.REQUEST_INVITE_SUBJECT, strings.REQUEST_INVITE_MESSAGE % (email_lookup.code, url), settings.FROM_EMAIL,
				    [request.session['email']], fail_silently=False)
				return HttpResponseRedirect(reverse(confirm_request))
			else:
				wordindex = random.randint(0, len(words)-1)
				word = words[wordindex]
				form.cleaned_data['wordindex'] = wordindex
				form.errors[''] = "The word didn't match. Please try again."
	else:
		wordindex = random.randint(0, len(words)-1)
		word = words[wordindex]		
		form = forms.ResendForm(label_suffix="", initial={'wordindex':wordindex})
	
	return render(request, 'resendinvite.html', {'word': word, 'form': form})	
	
def request_invite(request):
	
	if request.method == "POST":
		form = forms.RequestForm(data=request.POST)
		if form.is_valid():
			email = form.cleaned_data['email']
			try:
				email_lookup = InvitationCode.objects.get(email=email, requester=None)
				request.session['email'] = email				
				return HttpResponseRedirect(reverse(resend_invite))
			except ObjectDoesNotExist:
				invite_code = generate_code(3)
				code_obj = InvitationCode()
				code_obj.code = invite_code
				code_obj.email = form.cleaned_data['email']
				code_obj.save()
				
				# TODO don't hardcode 'create'
				host = request.get_host()
				url = "http://%s/create?i=%s" % (host, code_obj.code)
				
				send_mail(strings.REQUEST_INVITE_SUBJECT, strings.REQUEST_INVITE_MESSAGE % (code_obj.code, url), settings.FROM_EMAIL,
				    [request.session['email']], fail_silently=False)
				
				request.session['invite_code'] = invite_code
				request.session['email'] = email				
				return HttpResponseRedirect(reverse(confirm_request))
	else:
		form = forms.RequestForm(label_suffix="")
	return render(request, 'request.html', {'form': form})

def invitecode_valid(invite_code):
	try:
		InvitationCode.objects.get(code=invite_code)
		return True
	except ObjectDoesNotExist:
		return False

@login_required	
def actions(request):
	# when we drawing will be
	num_days = abs(date.today() - date(2009, 12, settings.DRAWING_DAY)).days
	return render(request, 'actions.html', {'days': num_days})
	
def home(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect(reverse(actions))
	if request.method == "POST":
		form = forms.StartForm(data=request.POST)
		if form.is_valid():
			invite_code = form.cleaned_data['invite_code']
			email = form.cleaned_data['email']
			request.session['invite_code'] = invite_code
			request.session['email'] = email				
			return HttpResponseRedirect(reverse(create))

	else:
		form = forms.StartForm(label_suffix='')
	return render(request, 'home.html', {'startform': form})