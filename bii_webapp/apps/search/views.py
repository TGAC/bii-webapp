from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

def search(request):
    return render_to_response("search.html", context_instance=RequestContext(request))

