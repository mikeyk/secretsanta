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
from models import Person, InvitationCode, Interests, Group
from invitecode import generate_code

def path_processor(request):
    return {'path': request.path}

def render(request, template_name, context={}):
	template = get_template(template_name)
	context = RequestContext(request, context, [path_processor])
	return HttpResponse(template.render(context))
	
def delete_group(request, group_id):
	response = {'stat':'fail'}
	try:
		try:
			group = Group.objects.get(id=group_id)
			if group.owner != request.user:
				raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			response['msg'] = 'not authorized'
		group.active = False
		group.save()
		response['stat'] = 'ok'
	except Exception, e:
		response['msg'] = e
	finally:
		return HttpResponse(json.dumps(response), content_type='text/javascript')
	

def join_group(request):
	invite_code = request.REQUEST.get("i")
	if not invite_code:
		pass
		# TODO error page
	try:
		code_obj = InvitationCode.objects.get(code=invite_code)
		group = Group.objects.get(code=code_obj.id)
		request.session['invite_code'] = invite_code		
	except ObjectDoesNotExist:
		# TODO error
		pass
	if not request.user.is_authenticated():
		return HttpResponseRedirect(reverse(login))
	if request.user not in group.members.all():
		print "adding to group"
		group.members.add(request.user)
		group.save()
	return HttpResponseRedirect(reverse('actions'))
	

def login(request):
	print request.session.get("invite_code")
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
	return render(request, 'login.html', {'next':next, 'form': form})

def register(request):

	# validate invite code
	if request.method == "POST":
		form = forms.PersonForm(data=request.POST)
		if form.is_valid():
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
			return HttpResponseRedirect(reverse(add_interests))
	else:
		form = forms.PersonForm(label_suffix="")
	state_select = forms.StateSelect()
	return render(request, 'register.html', {'form': form, 'state_select': state_select})

@login_required
def edit_members(request, group_id):
	try:
		group = Group.objects.get(id=group_id)
		if group.owner != request.user:
			raise ObjectDoesNotExist
	except ObjectDoesNotExist:
		return HttpResponseRedirect(reverse(actions))
	return render(request, 'members.html', {'members':group.members.exclude(username=request.user.username), 'group':group})
	
@login_required
def delete_member(request, group_id, member_name):
	
	json_response = {'stat':'fail'}
	try:
		group = Group.objects.get(id=group_id)
		if group.owner != request.user:
			raise ObjectDoesNotExist
		user = Person.objects.get(username=member_name)
		group.members.remove(user)
		group.save()
		json_response['stat'] = 'ok'
	finally:
		return HttpResponse(json.dumps(json_response))
	


@login_required
def add_interests(request):
	try:
		interest = Interests.objects.get(person=request.user)
	except ObjectDoesNotExist:
		sample = random.choice(['bandanna', 'australia', 'guitar', 'coffee'])
		interest = Interests(interest_1=sample, person=request.user)
	
	if request.method == "POST":
		form = forms.InterestForm(data=request.POST, instance=interest)
		if form.is_valid():
			interest = form.save()
			if request.session.get('completed', False) == True:
				return HttpResponseRedirect(reverse(actions))
			if not request.session.get('invite_code'):
				return HttpResponseRedirect(reverse(group))
			next = reverse('join-group') + "?i=%s" % (request.session['invite_code'])
			del request.session['invite_code']
			return HttpResponseRedirect(next)
	else:
		form = forms.InterestForm(label_suffix="", instance=interest)
	return render(request, 'interests.html', {'form': form})

def shorten_url(url):
	create_api = 'http://api.bit.ly/shorten'
	try:
		# based on Bittle's calls
		data = urllib.urlencode(dict(version="2.0.1", longUrl=url, login=settings.BITLY_LOGIN, apiKey=settings.BITLY_API_KEY, history=1))
		link = json.loads(urllib2.urlopen(create_api, data=data).read().strip())
		
		if link["errorCode"] == 0 and link["statusCode"] == "OK":
			results = link["results"][url]
			url = results['shortUrl']
	finally:
		return url
	
@login_required
def invite_friends(request, group_id):
	# first check if they already have a generated invite_code
	try:
		group = Group.objects.get(id=group_id)
		invite = group.code
		if not invite:
			pass # TODO FIXXXX
		url = "http://%s?i=%s" % (request.get_host(), invite.code)
		short_url = shorten_url(url)
		if not short_url: short_url = url
		tweet = "Hey Followers, I'd like to invite you to join me in a secret santa. Sign up here: %s" % short_url
		mailto_params = [("subject","Secret Santa"), ("body","Hey there, I'd like to invite you to join me in a secret santa. Sign up here: %s" % short_url)]	
		mailto = "mailto:?" + "&".join("%s=%s" % (k,v) for k,v in mailto_params)

		fb_link = url
		return render(request, 'invitefriends.html', {'tweet': tweet, 'short_url': short_url, 'group': group, 'invite_code': invite.code, 'mailto':mailto, 'fb_link': fb_link})		
		
	except ObjectDoesNotExist:
		# TODO ERRRRORRRRRZZ
		
		
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
				url = "http://%s/joingroup?i=%s" % (request.get_host(), email_lookup.code)
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
	
@login_required
def group(request, group_id=-1):
	
	group = None
	action = "Create"
	if group_id:
		try:
			group = Group.objects.get(id=group_id)
			if group.owner != request.user:
				raise ObjectDoesNotExist
			action = "Edit"
		except ObjectDoesNotExist:
			pass
	if not group:
		group = Group(owner=request.user)
	
	if request.method == "POST":
		form = forms.GroupForm(data=request.POST, instance=group)
		if form.is_valid():
			group = form.save(commit=False)
			is_new = False
			if not group.code: # this is a new group
				is_new = True
				invite_code = generate_code(3)
				code_obj = InvitationCode()
				code_obj.code = invite_code
				code_obj.email = request.user.email
				code_obj.save()
				group.code = code_obj
			group.save()
			if request.user not in group.members.all():
				group.members.add(request.user)
				group.save()
			if is_new:
				return HttpResponseRedirect(reverse('invite-friends', args=(group.id,)))
			else:
				return HttpResponseRedirect(reverse(actions))
	else:
		form = forms.GroupForm(label_suffix="", instance=group)
	return render(request, 'create.html', {'form': form, 'action':action})
	
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

				
				# TODO don't hardcode 'register'
				host = request.get_host()
				url = "http://%s/joingroup?i=%s" % (host, code_obj.code)
				
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
	request.session['completed'] = True
	# when we drawing will be
	# num_days = abs(date.today() - date(2009, 12, settings.DRAWING_DAY)).days
	interests = Interests.objects.get(person=request.user)
	owned_groups = Group.objects.filter(owner=request.user, active=True)
	joined_groups = request.user.group_set.filter(active=True).exclude(owner=request.user)
	return render(request, 'actions.html', {'owned_groups':owned_groups, 'interests': ", ".join(interests.all_interests()), 'joined_groups': joined_groups})
	
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