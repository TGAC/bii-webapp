from django.contrib.auth import decorators, views
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from bii_webapp.settings import common
from django.views.decorators.csrf import csrf_exempt
import json
import os
import csv
import time
import parser

# def parseHeaders(fileconfig):
#     headers=[]
#     for field in fileconfig['field']:


@decorators.login_required(login_url=views.login)
def create(request, config=None):
    if len(parser.configurations) == 0:
        parser.loadConfigurations()

    if 'config' not in request.session and config == None:
        return render_to_response("select_config.html", {'configurations': parser.configurations.keys()},
                                  context_instance=RequestContext(request))

    if config != None:
        request.session['config'] = config
    else:
        del request.session['config']
        return redirect(create)

    json_data = open(common.SITE_ROOT + '/fixtures/assay_mapping.json')
    jsonf = json.load(json_data)
    json_data.close()
    return render_to_response("create.html", {"configuration": json.dumps(parser.configurations[config])},
                              context_instance=RequestContext(request))

@csrf_exempt
@decorators.login_required(login_url=views.login)
def save(request,config):
    investigation=json.loads(request.POST['investigation'])
    directory=common.SITE_ROOT + '/tmp'
    if not os.path.exists(directory):
        os.makedirs(directory)
        os.chmod(directory,0o777)

    millis = int(round(time.time() * 1000))
    f = csv.writer(open(directory+'/temp'+str(millis)+'.txt', "wb+"), delimiter='\t',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)

    if not investigation['i_skip_investigation']:
        parser.writeInvestigation(f,investigation)
        parser.writePubsFor(f,investigation['i_pubs'],'INVESTIGATION')
        parser.writeContactsFor(f,investigation['i_contacts'],'INVESTIGATION')

    for study in investigation['i_studies']:
        parser.writeStudy(f,study)
        parser.writePubsFor(f,study['s_pubs'],'STUDY')
        parser.writeFactors(f,study['s_factors'])
        parser.writeAssays(f,study['s_assays'])
        parser.writeProtocols(f,study['s_protocols'])
        parser.writeContactsFor(f,study['s_contacts'],'STUDY')

    return HttpResponse(json.dumps({'INFO':{'messages':'File saved','total':1}}))


