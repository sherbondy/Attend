from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext

def home(request):
    return render_to_response('index.html', {}, context_instance=RequestContext(request))