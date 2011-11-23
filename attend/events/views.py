from urllib import quote
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.core import mail
from django.core.validators import validate_email
from django import forms
from datetime import datetime
from events.models import *
import facebook

ical = \
"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
DTSTART:{0}
DTEND:{1}
SUMMARY:{2}
LOCATION:{3}
DESCRIPTION:{4}
URL;VALUE=URI:http://www.facebook.com/event.php?eid={5}
BEGIN:VALARM
TRIGGER:-PT15M
DESCRIPTION:QRAttend event reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
"""

# convenience method to avoid strange AttributeError
# complaining the facebook object has no attribute graph
def fb(request):
    try:
        return request.facebook.graph
    except AttributeError:
        return False
    
def logged_in(request):
    return request.user.is_authenticated and request.user.is_active
    
# returns event object with added start_dt and end_dt parameters for convenience
def start_end(event):
    event["start_dt"] = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
    event["end_dt"] = datetime.strptime(event["end_time"], "%Y-%m-%dT%H:%M:%S")
    return event

# custom render function, vars is a dictionary, request is the request object
def render(template, vars, request):
    c = RequestContext(request)
    if fb(request) and logged_in(request):
        vars["me"] = fb(request).get_object("me")
    return render_to_response(template, vars, context_instance=c)
        

def home(request):    
    if fb(request) and logged_in(request):
        fbuser = fb(request).get_object("me")
        events = fb(request).get_connections("me", "events")
        real_events = []
        now = datetime.now()

        db_events = []
        db_event_ids = []
        for db_event in FacebookEvent.objects.filter(facebook_user_id=fbuser["id"]):
            db_event_ids.append(db_event.facebook_event_id)
            new_db_event = fb(request).get_object(db_event.facebook_event_id)
            new_db_event = start_end(new_db_event)
            db_events.append(new_db_event)

        for event in events["data"]:
            event = start_end(event)

            if event["rsvp_status"] == u'attending' and event["start_dt"] > now:
                new_event = fb(request).get_object(event["id"])
                new_event = start_end(new_event)
    
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
    event = start_end(event)
    success = request.GET.__contains__('success')
    return render('mobile.html', {'event':event, 'success':success}, request)

def event(request,event_id):
    c = RequestContext(request)
    try:
        event_obj = FacebookEvent.objects.get(facebook_event_id=event_id)
    except FacebookEvent.DoesNotExist:
        if fb(request) and logged_in(request):
            fbuser = fb(request).get_object("me")
            fbevent = fb(request).get_object(event_id)
            if fbevent["owner"]["id"]==fbuser["id"]: #create a QR code
                event_obj = FacebookEvent(facebook_event_id=event_id,facebook_user_id=fbuser["id"])
                event_obj.save()
    
    if event_obj:
        event = fb(request).get_object(event_id)
        event = start_end(event)
        return render('event.html', {'event_id':event_id,'event_obj':event}, request)
    else:
        return render('no_event.html', {}, request)

def email(request, event_id):
    if request.method == "POST":
        try:
            addr = request.POST["email"].strip()
            validate_email(addr)
            
            api = facebook.GraphAPI()
            event = api.get_object(event_id)

            content = ical.format("".join("".join(event["start_time"].split("-")).split(":")), 
                                  "".join("".join(event["end_time"].split("-")).split(":")),
                                  event["name"], event["location"], event["description"],
                                  event["id"])
        
            email = mail.EmailMessage('Event from QR Attend!', 'Hey there. Attached is the iCal event for {0}'.format(event["name"]),
                                to=[addr])
            email.attach("fbevent.ics", content, "text/calendar")
            email.send()
        
            return redirect('/m/'+event_id+"?success")
        except forms.ValidationError:
            return redirect('/m/'+event_id+"/?email="+quote(addr))
    
    
