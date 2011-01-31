from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core import mail
from datetime import datetime
from events.models import *
import facebook
import uuid

def home(request):
    c = RequestContext(request)
    
    if request.user.is_authenticated and request.user.is_active:
        fbuser = request.facebook.graph.get_object("me")
        events = request.facebook.graph.get_connections("me", "events")
        real_events = []
        now = datetime.now()
	
	friends = request.facebook.graph.get_object("me/friends")
	friend_hash = {}
	for friend in friends["data"]:
            friend_hash[friend["id"]]=friend["name"]
	friend_events = []
	for db_event in FacebookEvent.objects.all():
	    if db_event.facebook_user_id in friend_hash:
                friend_event = request.facebook.graph.get_object(db_event.facebook_event_id)
                friend_event["start_dt"] = datetime.strptime(friend_event["start_time"], "%Y-%m-%dT%H:%M:%S")
                friend_event["end_dt"] = datetime.strptime(friend_event["end_time"], "%Y-%m-%dT%H:%M:%S")
                friend_event["friend_name"] = friend_hash[db_event.facebook_user_id]
                friend_event["friend_id"] = db_event.facebook_user_id
                friend_events.append(friend_event)
	
	db_events = []
	db_event_ids = []
	for db_event in FacebookEvent.objects.filter(facebook_user_id=fbuser["id"]):
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
			{'me':fbuser, 'events':real_events, 'db_events':db_events, 'friend_events':friend_events}, context_instance=c)
    else:
        return render_to_response('index.html', {}, context_instance=c)

def logout_view(request):
    logout(request)
    return redirect(home)

def mobile(request, event_id):
    c = RequestContext(request)
    api = facebook.GraphAPI()
    event = api.get_object(event_id)
    event["start_dt"] = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
    event["end_dt"] = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S")
    return render_to_response('mobile.html', {'event':event}, context_instance=c)

def event(request,event_id):
    c = RequestContext(request)
    matches = FacebookEvent.objects.filter(facebook_event_id=event_id)
    success = False
    if len(matches)==0:
        if request.user.is_authenticated and request.user.is_active:
            fbuser = request.facebook.graph.get_object("me")
            fbevent = request.facebook.graph.get_object(event_id)
            if fbevent["owner"]["id"]==fbuser["id"]: #create a QR code
                event_obj = FacebookEvent(facebook_event_id=event_id,facebook_user_id=fbuser["id"])
                event_obj.save()
		success = True
    else:
        success = True
    
    if success == True:
        event = request.facebook.graph.get_object(event_id)
        event["start_dt"] = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
        event["end_dt"] = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S")
	return render_to_response('event.html', {'event_id':event_id,'event_obj':event}, context_instance=c)
    else:
        return render_to_response('no_event.html', context_instance=c)

def email(request, event_id):
    if request.method == "POST":
        api = facebook.GraphAPI()
        event = api.get_object(event_id)
        
        addr = request.POST["email"]
    
        content = """BEGIN:VCALENDAR
        CALSCALE:GREGORIAN
        X-WR-TIMEZONE;VALUE=TEXT:US/Eastern
        METHOD:PUBLISH
        PRODID:-//Apple Computer\, Inc//iCal 1.0//EN
        X-WR-CALNAME;VALUE=TEXT:Example
        VERSION:2.0
        BEGIN:VEVENT
        SEQUENCE:5
        DTSTART;TZID=US/Eastern:{0}
        DTSTAMP:{0}Z
        SUMMARY:{1}
        UID:{2}
        DTEND;TZID=US/Eastern: {3}
        BEGIN:VALARM
        TRIGGER;VALUE=DURATION:-P1D
        ACTION:DISPLAY
        DESCRIPTION:Event reminder
        END:VALARM
        END:VEVENT
        END:VCALENDAR""".format(event["start_time"].strip("-"), event["name"], str(uuid.uuid1()), event["end_time"].strip("-"))
        
        connection = mail.get_connection()
        
        email = mail.EmailMessage('Event from QREvents!', 'Hey there. Attached is the iCal event for {0}'.format(event["name"]),
                            to=[addr])
        email.attach("fbevent.ics", content, "text/calendar")
        email.send()
        
        return redirect(home)
    
    
