from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import logout
from datetime import datetime

def home(request):
    c = RequestContext(request)
    
    if request.user.is_authenticated and request.user.is_active:
        fbuser = request.facebook.graph.get_object("me")
        events = request.facebook.graph.get_connections("me", "events")
        now = datetime.now()
        
        for i, event in enumerate(events["data"]):
            start = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
            
            if (not event["rsvp_status"] == u'attending') or start < now:
                events["data"].pop(i)
                
        return render_to_response('events.html', 
                {'me':fbuser, 
                 'events':events}, context_instance=c)
    else:
        return render_to_response('index.html', {}, context_instance=c)

def logout_view(request):
    logout(request)
    return redirect(home)
