from django.shortcuts import render_to_response
from django.template import RequestContext
import requests, json
from django.conf import settings
from django.http import HttpResponse
from bii_webapp.settings import common
from django.shortcuts import redirect
from django.contrib.auth import decorators, views
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
import re

cache.clear()

@csrf_exempt
@decorators.login_required(login_url=views.login)
def deleteInvestigation(request):
    url = settings.WEBSERVICES_URL + 'update/delete'
    try:
        r=requests.post(url, data=request.body);
    except Exception:
        return HttpResponse(json.dumps({"ERROR":{"messages":"Server is down","total":1}}))

    loaded = json.loads(r.content)
    cache.delete('browse')
    loaded=json.loads(request.body)
    inv=cache.get(loaded['pk'])
    studies=inv['i_studies']
    for study in studies:
        cache.delete(study['s_id'])

    cache.delete(loaded['pk'])

    return HttpResponse(json.dumps(loaded))

@csrf_exempt
@decorators.login_required(login_url=views.login)
def deleteStudy(request):
    url = settings.WEBSERVICES_URL + 'update/delete'
    try:
        r=requests.post(url, data=request.body);
    except Exception:
        return HttpResponse(json.dumps({"ERROR":{"messages":"Server is down","total":1}}))

    loaded = json.loads(r.content)
    cache.delete('browse')
    loaded=json.loads(request.body)
    cache.delete(loaded['pk'])

    return HttpResponse(json.dumps(loaded))

@csrf_exempt
@decorators.login_required(login_url=views.login)
def updateInvestigation(request):
    data=request.POST.copy()
    data['type']='investigation';
    url = settings.WEBSERVICES_URL + 'update'
    try:
        r=requests.post(url, data=json.dumps(data));
    except Exception:
        return HttpResponse(json.dumps({"ERROR":{"messages":"Server is down","total":1}}))

    loaded = json.loads(r.content)
    loaded['field']=data['name']

    cache.delete('browse')
    pk=request.POST['pk']
    cache.delete(pk)

    return HttpResponse(json.dumps(loaded))

@csrf_exempt
@decorators.login_required(login_url=views.login)
def updateStudy(request):
    data=request.POST.copy()
    data['type']='study';
    url = settings.WEBSERVICES_URL + 'update'

    try:
        r=requests.post(url, data=json.dumps(data))
    except Exception:
        return HttpResponse(json.dumps({"ERROR":{"messages":"Server is down","total":1}}))

    loaded = json.loads(r.content)
    loaded['field']=data['name']

    cache.delete('browse')
    pk=request.POST['pk']
    cache.delete(pk)

    return HttpResponse(json.dumps(loaded))


@decorators.login_required(login_url=views.login)
def browse(request, page=1):
    loaded=cache.get('browse')
    try:
        if loaded==None:
            r = requests.post(settings.WEBSERVICES_URL + 'retrieve/browse',
                          data=json.dumps({'username': request.user.username, 'page': page}))
            loaded = json.loads(r.content)

            if 'ERROR' in loaded:
                if (int)(page) != 1:
                    return redirect(browse,1)
                else:
                    return render_to_response("browse.html", {"data": loaded,'number_of_pages':0, 'current_page':0,
                                                              'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                                              context_instance=RequestContext(request))

            if 'INFO' in loaded:
                return render_to_response("browse.html", {"data": loaded,'number_of_pages':0, 'current_page':0,
                                                      'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                                      context_instance=RequestContext(request))

            cache.set('browse', loaded, None)

    except ValueError:
        return render_to_response("browse.html", {"data": {"ERROR":{"messages":"Results could not be retrieved","total":1}},'number_of_pages':0, 'current_page':0,
                                                  'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                                  context_instance=RequestContext(request))
    except Exception:
        return render_to_response("browse.html", {"data": {"ERROR":{"messages":"Server is down","total":1}},'number_of_pages':0, 'current_page':0,
                                                  'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                                  context_instance=RequestContext(request))


    results=json.loads(loaded['results'])
    blist = generateBreadcrumbs(request.path)
    request.breadcrumbs(blist)

    return render_to_response("browse.html", {"data": results,'number_of_pages':loaded['number_of_pages'], 'current_page':page,
                                              'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                              context_instance=RequestContext(request))

@decorators.login_required(login_url=views.login)
def investigation(request, invID=None):
    if invID == None:
        return redirect(browse)

    loaded=cache.get(invID)

    if loaded==None:
        try:
            r = requests.post(settings.WEBSERVICES_URL + 'retrieve/investigation',
                          data=json.dumps({'username': request.user.username, 'investigationID':invID}))

            loaded = json.loads(r.content)
            if 'ERROR' in loaded:
                return redirect(browse)

            i_studies=None
            browse_data=cache.get('browse')
            if browse_data!=None:
                results=json.loads(browse_data['results'])
                for inv in results['investigations']:
                    if inv['i_id']==invID:
                        i_studies=inv['i_studies']
                        break
            if i_studies == None:
                r = requests.post(settings.WEBSERVICES_URL + 'retrieve/investigation/studies',
                                  data=json.dumps({'username': request.user.username, 'investigationID':invID}))
                i_studies=json.loads(r.content)['i_studies']

            loaded.update({'i_studies':i_studies})
            cache.set(invID, loaded, None)

        except Exception:
            return render_to_response("browse.html", {"data": {"ERROR":{"messages":"Server is down","total":1}},'number_of_pages':0, 'current_page':0,
                                                      'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                                      context_instance=RequestContext(request))

    investigation = json.dumps(loaded).replace("'", "\\'")

    blist = generateBreadcrumbs(request.path)
    request.breadcrumbs(blist)

    return render_to_response("investigation.html", {"investigation": loaded, "investigation_json": investigation,
                                                     'pageNotice': 'Various fields can be edited by clicking'},
                              context_instance=RequestContext(request))


@decorators.login_required(login_url=views.login)
def study(request, invID=None, studyID=None):
    path=request.path
    if path.find('investigation',7,21)==-1:
        studyID=invID
    if studyID == None:
        return redirect(browse)

    loaded=cache.get(studyID)

    if loaded==None:
        try:
            r = requests.post(settings.WEBSERVICES_URL + 'retrieve/study',
                          data=json.dumps({'username': request.user.username, 'studyID':studyID}))

            loaded = json.loads(r.content)

            if 'ERROR' in loaded:
                return redirect(browse)

            s_assays=None
            studies=None
            browse_data=cache.get('browse')
            if browse_data!=None:
                results=json.loads(browse_data['results'])
                if invID!=studyID:
                    for inv in results['investigations']:
                        if inv['i_id']==invID:
                            studies=inv['i_studies']
                            break
                else:
                    studies=results['studies']

                for study in studies:
                    if study['s_id']==studyID:
                        s_assays=study['s_assays']
                        break

            if s_assays == None:
                r = requests.post(settings.WEBSERVICES_URL + 'retrieve/study/assays',
                                  data=json.dumps({'username': request.user.username, 'studyID':studyID}))
                s_assays=json.loads(r.content)['s_assays']

            loaded.update({'s_assays':s_assays})
            cache.set(studyID, loaded, None)

        except Exception:
            return render_to_response("browse.html", {"data": {"ERROR":{"messages":"Server is down","total":1}},'number_of_pages':0, 'current_page':0,
                                                      'pageNotice':'This page shows the accessible studies for your account, click on each to get more details'},
                                      context_instance=RequestContext(request))

    study = json.dumps(loaded).replace("'", "\\'")

    blist = generateBreadcrumbs(request.path)
    request.breadcrumbs(blist)

    return render_to_response("study.html", {"investigation": {"i_id": invID},"study": loaded, "study_json": study,
                                                     'pageNotice': 'Various fields can be edited by clicking'},
                              context_instance=RequestContext(request))


def generateBreadcrumbs(path=None):
    split = path.split('/')

    bPath = '/browse/'
    breadcrumbs = [('Browse the BII', bPath)]

    investigation = re.search('(?<=investigation/)[^/.]+', path)
    if (investigation):
        investigation = investigation.group(0)
        bPath += 'investigation/' + investigation + '/'
        breadcrumbs.append(('Investigation ' + investigation, bPath))

    study = re.search('(?<=study/)[^/.]+', path)
    if (study):
        study = study.group(0)
        bPath += 'study/' + study + '/'
        breadcrumbs.append(('Study ' + study, bPath))

    sample = re.search('(?<=sample/)[^/.]+', path)
    if (sample):
        sample = sample.group(0)
        bPath += 'sample/' + sample + '/'
        breadcrumbs.append(('Sample ' + sample, bPath))

    assay = re.search('(?<=assay/)[^/.]+', path)
    if (assay):
        assay = assay.group(0)
        bPath += 'assay/' + assay + '/'
        breadcrumbs.append(('Assay ' + assay, bPath))

    return breadcrumbs


@decorators.login_required(login_url=views.login)
def assay(request, invID=None, studyID=None, assayID=None):
    if studyID == None or assayID == None:
        return redirect(browse)

    json_data = open(common.SITE_ROOT + '/fixtures/assay.json')
    loaded = json.load(json_data)
    assay = json.dumps(loaded).replace("'", "\\'")
    json_data.close()

    blist = generateBreadcrumbs(request.path)
    request.breadcrumbs(blist)
    return render_to_response("assay.html",
                              {"investigation": {"i_id": None}, "study": {"s_id": studyID}, "assay": loaded,
                               "assay_json": assay}, context_instance=RequestContext(request))


@decorators.login_required(login_url=views.login)
def sample(request, invID=None, studyID=None, sample=-1):
    if studyID == -1 or sample == -1:
        return redirect(browse)

    blist = generateBreadcrumbs(request.path)
    request.breadcrumbs(blist)

    return render_to_response("sample.html", context_instance=RequestContext(request))
