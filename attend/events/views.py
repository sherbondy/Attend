from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import logout
from datetime import datetime
from events.models import *
import facebook

def home(request):
    c = RequestContext(request)
    
    if request.user.is_authenticated and request.user.is_active:
        fbuser = request.facebook.graph.get_object("me")
        events = request.facebook.graph.get_connections("me", "events")
        real_events = []
        now = datetime.now()
	
	db_events = []
	db_event_ids = []
	for db_event in FacebookEvent.objects.all():
	    db_event_ids.append(db_event.facebook_event_id)
            new_db_event = request.facebook.graph.get_object(db_event.facebook_event_id)
	    new_db_event["start_dt"] = datetime.strptime(new_db_event["start_time"], "%Y-%m-%dT%H:%M:%S")
            new_db_event["end_dt"] = datetime.strptime(new_db_event["end_time"], "%Y-%m-%dT%H:%M:%S")
	    db_events.append(new_db_event)

        for event in events["data"]:
            event["start_dt"] = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
            event["end_dt"] = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S")
            
            if event["rsvp_status"] == u'attending' and event["start_dt"] > now:
                new_event = request.facebook.graph.get_object(event["id"])
                new_event["start_dt"] = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
                new_event["end_dt"] = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S")
                
                if new_event["owner"]["id"] == fbuser["id"] and new_event["privacy"] == u'OPEN' and not new_event["id"] in db_event_ids: 
                    real_events.append(new_event)
        
        return render_to_response('events.html', 
                {'me':fbuser, 'events':real_events, 'db_events':db_events}, context_instance=c)
    else:
        return render_to_response('index.html', {}, context_instance=c)

def logout_view(request):
    logout(request)
    return redirect(home)

def mobile(request, event_id):
    c = RequestContext(request)
    api = facebook.GraphAPI()
    event = api.get_object(event_id)
    return render_to_response('mobile.html', {'event':event}, context_instance=c)

def event(request,event_id):
    c = RequestContext(request)
    matches = FacebookEvent.objects.filter(facebook_event_id=event_id)
    if len(matches)==0:
        event_obj = FacebookEvent(facebook_event_id=event_id)
        event_obj.save()
    return render_to_response('event.html', {'event_id':event_id}, context_instance=c)
