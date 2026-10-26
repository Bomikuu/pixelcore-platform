"""Restricted, revocable Studio delegation. Host membership is checked on every call."""
import hashlib
import json
import re
import secrets
from datetime import timedelta
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.http import Http404
from django.test import RequestFactory
from django.urls import resolve, Resolver404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.test import force_authenticate
from rest_framework.views import APIView
from businesses.views import member_business
from .models import StudioHandoff, StudioGrant

def digest(value): return hashlib.sha256(value.encode()).hexdigest()

def client_allowed(request):
    expected = getattr(settings, 'STUDIO_CLIENT_SECRET', '')
    supplied = request.headers.get('X-Studio-Client', '')
    if not expected or not secrets.compare_digest(expected, supplied):
        raise PermissionDenied('Studio connection is not configured or the client is invalid.')

def member(grant):
    if not grant.user.is_active or grant.business.status != 'active': raise PermissionDenied('This platform connection is no longer available.')
    return member_business(grant.user, grant.business.public_id, roles=('owner','admin','manager'))

class HandoffView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, public_id):
        if not getattr(settings, 'STUDIO_CLIENT_SECRET', ''): raise PermissionDenied('Studio connection is not configured.')
        business = member_business(request.user, public_id, roles=('owner','admin','manager'))
        state, audience = request.data.get('state',''), request.data.get('audience','')
        if not isinstance(state,str) or not re.fullmatch(r'[A-Za-z0-9_-]{32,128}',state) or audience != settings.STUDIO_FRONTEND_ORIGIN:
            return Response({'error':{'message':'Invalid Studio connection state or audience.'}},status=400)
        code = secrets.token_urlsafe(32)
        StudioHandoff.objects.create(digest=digest(code),user=request.user,business=business,state=state,audience=audience,expires_at=timezone.now()+timedelta(seconds=60))
        return Response({'code':code,'state':state})

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@never_cache
def exchange(request):
    client_allowed(request)
    value=request.data
    with transaction.atomic():
        handoff=StudioHandoff.objects.select_related('user','business').filter(digest=digest(str(value.get('code',''))),state=value.get('state'),audience=settings.STUDIO_FRONTEND_ORIGIN,expires_at__gt=timezone.now(),consumed_at__isnull=True).first()
        if not handoff or value.get('audience') != settings.STUDIO_FRONTEND_ORIGIN: raise PermissionDenied('The platform connection expired or has already been used.')
        member(handoff)
        if not StudioHandoff.objects.filter(pk=handoff.pk,consumed_at__isnull=True).update(consumed_at=timezone.now()): raise PermissionDenied('This connection was already used.')
        raw=secrets.token_urlsafe(48)
        grant=StudioGrant.objects.create(digest=digest(raw),user=handoff.user,business=handoff.business,expires_at=timezone.now()+timedelta(days=7))
    origin=settings.PIXELCORE_FRONTEND_URL.rstrip('/')
    user=handoff.user
    return Response({'issuer':'pixelcore','subject':str(user.pk),'business':{'id':str(handoff.business.public_id),'name':handoff.business.display_name},'user':{'displayName':user.get_full_name() or user.username,'email':user.email,'avatarUrl':'','settingsUrl':origin+'/settings'},'grant':raw,'expiresAt':grant.expires_at.isoformat()})

def overview(grant, params=None):
    from website_builder.models import Website
    from website_builder.services.workspace import website_summary
    from .models import SitePage, Site
    from scheduling.models import VenueEvent
    business=grant.business
    from website_builder.services.discovery import website_page, window
    params=params or {}
    query=str(params.get('sourceQ',''))[:100].strip()
    kind=params.get('sourceKind','all')
    sources=[]
    offset,limit=window(params,'source')
    remaining=offset
    total=0
    for source_kind,rows,title_field in [('page',SitePage.objects.filter(site__business=business),'title'),('event',VenueEvent.objects.filter(business=business),'title'),('layout',Site.objects.filter(business=business),'name')]:
        if kind not in ('all',source_kind): continue
        if query: rows=rows.filter(**{title_field+'__icontains':query})
        rows=rows.order_by(title_field,'public_id')
        count=rows.count(); total+=count
        if remaining>=count: remaining-=count; continue
        available=limit-len(sources)
        if available>0:
            sources += [{'kind':source_kind,'id':str(row.public_id),'title':getattr(row,title_field)} for row in rows[remaining:remaining+available]]
        remaining=0
    discovered=website_page(str(business.public_id),params)
    page_ids=[row['sourceKey'].split(':',1)[1] for row in discovered['sites'] if row['sourceKey'].startswith('page:')]
    page_routes={str(p.public_id):('' if p.page_type=='home' else '/'+p.slug) for p in SitePage.objects.filter(site__business=business,public_id__in=page_ids)}
    for row in discovered['sites']:
        source_kind,_,identifier=row['sourceKey'].partition(':')
        path='/event/'+identifier if source_kind=='event' else '/site/'+business.slug+page_routes.get(identifier,'')
        if row['published']: row['publicUrl']=settings.PIXELCORE_FRONTEND_URL.rstrip('/')+path
    return {'workspace':{'id':str(business.public_id),'name':business.display_name,'source':'pixelcore'},**discovered,'summary':website_summary(str(business.public_id)),'sources':sources,'sourcePage':{'total':total,'offset':offset,'limit':limit,'nextOffset':offset+limit if offset+limit<total else None},'capabilities':{'editWebsite':True,'manageComponents':False}}

def builder_request(grant, args):
    from website_builder.models import Website, ReviewShare
    route=args.get('route','')
    method=args.get('method','GET')
    if not isinstance(route,str) or len(route)>300 or not re.fullmatch(r'[a-zA-Z0-9/-]+',route) or method not in {'GET','POST','PUT','DELETE'}: raise PermissionDenied('This builder operation is unavailable.')
    try: match=resolve('/'+route,urlconf='website_builder.urls')
    except Resolver404: raise PermissionDenied('This builder operation is unavailable.')
    website_id=match.kwargs.get('website_id')
    if website_id:
        if not Website.objects.filter(pk=website_id,tenant=str(grant.business.public_id)).exists(): raise PermissionDenied('This website belongs to another workspace.')
    elif match.kwargs.get('share_id'):
        if not ReviewShare.objects.filter(pk=match.kwargs['share_id'],revision__website__tenant=str(grant.business.public_id)).exists(): raise PermissionDenied('This review belongs to another workspace.')
    else: raise PermissionDenied('Only business website operations are supported.')
    data=args.get('body',{})
    factory=RequestFactory()
    if 'file' in args:
        import base64
        file=args['file']
        raw=base64.b64decode(file['data'],validate=True)
        if len(raw)>20_000_000: raise PermissionDenied('The media file is too large.')
        request=factory.post('/api/website-builder/'+route,{'file':SimpleUploadedFile(file['name'][:120],raw,content_type=file.get('type','application/octet-stream')),'alt':str(args.get('alt',''))[:300]})
    else:
        encoded=json.dumps(data)
        if len(encoded.encode())>600_000: raise PermissionDenied('The builder request is too large.')
        from urllib.parse import urlencode
        query=args.get('query',{})
        if not isinstance(query,dict) or len(query)>12: raise PermissionDenied('Invalid query.')
        request=factory.generic(method,'/api/website-builder/'+route+('?' + urlencode(query) if query else ''),encoded,content_type='application/json')
    request.user=grant.user
    response=match.func(request,**match.kwargs)
    try: value=json.loads(response.content)
    except (ValueError,UnicodeError): value={'error':{'message':'This request method is unavailable for the selected builder operation.'}}
    return Response(value,status=response.status_code)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
@never_cache
def gateway(request):
    client_allowed(request)
    if int(request.META.get('CONTENT_LENGTH') or 0)>28_000_000: return Response({'error':{'message':'The request is too large.'}},status=413)
    grant=StudioGrant.objects.select_related('user','business').filter(digest=digest(str(request.data.get('grant',''))),revoked_at__isnull=True,expires_at__gt=timezone.now()).first()
    if not grant: raise PermissionDenied('Reconnect your platform to continue.')
    member(grant)
    operation=request.data.get('operation')
    if operation=='revoke':
        grant.revoked_at=timezone.now();grant.save(update_fields=['revoked_at']);return Response({'revoked':True})
    if operation=='overview': return Response(overview(grant,request.data.get('args',{})))
    if operation=='open':
        from .builder_bridge import BuilderWorkspaceView
        raw=RequestFactory().post('/',json.dumps(request.data.get('args',{})),content_type='application/json')
        force_authenticate(raw,user=grant.user)
        return BuilderWorkspaceView.as_view()(raw,public_id=grant.business.public_id)
    if operation=='builder': return builder_request(grant,request.data.get('args',{}))
    if operation=='analytics':
        from website_builder.analytics import analytics_operation
        return Response(analytics_operation(grant.user,str(grant.business.public_id),request.data.get('args',{})))
    raise PermissionDenied('This Studio operation is unavailable.')
