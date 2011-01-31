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

def logged_in(request):
    return request.user.is_authenticated and request.user.is_active

# custom render function, vars is a dictionary, request is the request object
def render(template, vars, request):
    c = RequestContext(request)
    if logged_in(request):
        vars["me"] = request.facebook.graph.get_object("me")
    return render_to_response(template, vars, context_instance=c)
        

def home(request):    
    if logged_in(request):
        fbuser = request.facebook.graph.get_object("me")
        events = request.facebook.graph.get_connections("me", "events")
        real_events = []
        now = datetime.now()

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
    
        return render('events.html', {'me':fbuser, 'events':real_events, 'db_events':db_events}, request)
    else:
        return render('index.html', {}, request)

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
    try:
        event_obj = FacebookEvent.objects.get(facebook_event_id=event_id)
    except FacebookEvent.DoesNotExist:
        if logged_in(request):
            fbuser = request.facebook.graph.get_object("me")
            fbevent = request.facebook.graph.get_object(event_id)
            if fbevent["owner"]["id"]==fbuser["id"]: #create a QR code
                event_obj = FacebookEvent(facebook_event_id=event_id,facebook_user_id=fbuser["id"])
                event_obj.save()
    
    if event_obj:
        event = request.facebook.graph.get_object(event_id)
        event["start_dt"] = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
        event["end_dt"] = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S")
        return render('event.html', {'event_id':event_id,'event_obj':event}, request)
    else:
        return render('no_event.html', {}, request)

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
    
    
