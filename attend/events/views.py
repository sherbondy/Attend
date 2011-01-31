from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import logout

def home(request):
    c = RequestContext(request)
    
    if request.user.is_authenticated and request.user.is_active:
        return render_to_response('events.html', {}, context_instance=c)
    else:
        return render_to_response('index.html', {}, context_instance=c)

def logout_view(request):
    logout(request)
    return HttpResponse("You're logged out.")