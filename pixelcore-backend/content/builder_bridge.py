"""Host adapter for the separately maintained website-builder package."""
import json
import uuid
from urllib.parse import urljoin, urlsplit
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from businesses.models import Business, BusinessAsset
from businesses.views import member_business
from businesses.services import record_audit
from scheduling.models import VenueEvent
from .models import SitePage, Site

FONTS={"Manrope","Newsreader","Georgia","Arial","Verdana","Trebuchet MS","Bodoni Moda","Cormorant Garamond","Italiana","system-ui"}
COLORS={"background":"#ffffff","surface":"#f4f6f8","text":"#19252e","muted":"#53616d","primary":"#125b50","onPrimary":"#ffffff","accent":"#ba5a30","border":"#d8dfe4"}

def enabled():
    return "website_builder" in settings.INSTALLED_APPS

def public_url(file):
    if not file:return ""
    origin=urlsplit(settings.PIXELCORE_PUBLIC_API_URL)
    return urljoin(f"{origin.scheme}://{origin.netloc}/",file.url)

def target(website):
    business=Business.objects.filter(public_id=website.tenant,status="active").first()
    if not business:raise PermissionDenied("This business website is unavailable.")
    kind,identifier=website.key.split(":",1)
    model=VenueEvent if kind=="event" else Site if kind=="layout" else SitePage
    query={"business":business} if kind in {"event","layout"} else {"site__business":business}
    item=model.objects.filter(public_id=identifier,**query).first()
    if not item:raise PermissionDenied("This website source is unavailable.")
    return business,kind,item

def authorize(request,website,action):
    user=getattr(request,"user",None)
    if not getattr(user,"is_authenticated",False):
        try:
            authenticated=JWTAuthentication().authenticate(request)
            if authenticated:
                request.user=authenticated[0]
                user=authenticated[0]
        except AuthenticationFailed:
            return False
    if not getattr(user,"is_authenticated",False):return False
    try:
        business,kind,item=target(website)
        member_business(user,business.public_id,roles=("owner","admin","manager"))
    except (Http404,PermissionDenied):return False
    return True

def brand_kit(business,event=None):
    branding=business.branding or {}
    colors={k:v for k,v in {"primary":branding.get("primary_color"),"accent":branding.get("accent_color")}.items() if isinstance(v,str) and len(v)==7 and v.startswith('#')}
    typography=branding.get("typography",{})
    heading=typography.get("heading_font","Georgia")
    body=typography.get("body_font","Manrope")
    if event:
        colors.update({"background":event.theme_background,"text":event.theme_text,"accent":event.theme_accent})
        heading,body=event.heading_font,event.body_font
    return {"version":1,"colors":colors,"headingFont":heading if heading in FONTS else "Georgia","bodyFont":body if body in FONTS else "Manrope"}

def capabilities(request,website):
    business,kind,item=target(website)
    sources=[{"value":"identity.name","label":"Business name"},{"value":"identity.description","label":"Business introduction"},{"value":"identity.address","label":"Business address"},{"value":"identity.phone","label":"Business phone"}]
    if kind=="event":sources += [{"value":"event.title","label":"Event title"},{"value":"event.date","label":"Event date"},{"value":"event.venue","label":"Event venue"}]
    features=(['event','rsvp','wishes'] if kind=='event' else ['products','services'])
    pages=[{'sourceId':str(page.public_id),'title':page.title,'kind':'page'} for page in business.site.pages.all()] if hasattr(business,'site') else []
    if kind=='event':pages=[{'sourceId':str(item.public_id),'title':item.title,'kind':'event'}]
    affected=[p['title'] for p in pages] if kind=='layout' else []
    return {'dataSources':data_sources(kind),'features':features,'sources':sources,'brandKit':brand_kit(business,item if kind=='event' else None),'kind':kind,'sourceId':str(item.public_id),
      'workspace':{'version':1,'mediaUpload':True,'rsvpState':('invitation-required' if item.public_rsvp_enabled else 'disabled') if kind=='event' else None,'publicUrl':settings.PIXELCORE_FRONTEND_URL.rstrip('/')+(f'/event/{item.public_id}' if kind=='event' else f'/site/{business.slug}'+('' if kind=='layout' or item.page_type=='home' else '/'+item.slug)),'kind':kind,'purpose':'event' if kind=='event' else 'storefront','sourceId':str(item.public_id),'sourceName':item.title if kind in {'event','page'} else item.name,'pages':pages,'layoutSourceId':str(business.site.public_id) if hasattr(business,'site') else None,'affectedPages':affected,'headerVariants':['left'] if business.branding.get('storefront',{}).get('layout')=='marketplace' else ['left','center'],'footerVariants':['columns'] if business.branding.get('storefront',{}).get('layout')=='marketplace' else ['compact','columns','wedding']},
      'publicUrl':f'/event/{item.public_id}' if kind=='event' else f'/site/{business.slug}'}

def iter_nodes(document):
    yield document
    for child in document.get("children",[]):yield from iter_nodes(child)

def resolved_for_document(request,website,document,include_library=False,global_stage="published"):
    business,kind,item=target(website)
    assets={str(a.public_id):asset_payload(a) for a in business.assets.filter(processing_status="ready",asset_type__in=("image","video"))}
    if business.logo:assets['brand-logo']={'url':public_url(business.logo),'alt':business.display_name,'version':business.logo.name,'type':'image'}
    if business.cover_image:assets["hero"]={"url":public_url(business.cover_image),"alt":business.display_name,"version":business.cover_image.name,"type":"image"}
    identity={"name":business.display_name,"description":business.description,"address":", ".join(filter(None,[business.city,business.region])),"phone":business.contact_phone,"email":business.contact_email,"logo":public_url(business.logo) if business.logo else '',"homeUrl":f'/site/{business.slug}',"socials":business.branding.get('socials',[])}
    result={"identity":identity,"assets":assets,"locale":getattr(business,"locale","en-PH") or "en-PH","currency":business.currency,"products":[],"services":[]}
    site=getattr(business,'site',None)
    result['navigation']=[{'label':n.get('label',''),'href':f"/site/{business.slug}"+('' if n.get('path')=='/' else n.get('path',''))} for n in (site.navigation if site else []) if isinstance(n,dict)]
    if kind=='page' and site:result['frame']=frame_data(business,site,draft=False)
    from website_builder.services.globals import resolve_global_sections
    result = resolve_global_sections(website.tenant, document, result, stage=global_stage)
    nodes = list(iter_nodes(document))
    for linked in result.get('globalSections', {}).values(): nodes.extend(iter_nodes(linked['node']))
    need_products=include_library or any(n.get('type')=='products' or n.get('props',{}).get('source')=='products' for n in nodes)
    need_services=include_library or any(n.get('type')=='services' or n.get('props',{}).get('source')=='services' for n in nodes)
    for offering in business.offerings.filter(status="published").prefetch_related("ordered_media__asset","assets")[:200]:
        is_service=offering.offering_type=="service"
        if not (need_services if is_service else need_products):continue
        first=next((m.asset for m in offering.ordered_media.all() if m.asset.processing_status=='ready' and m.asset.asset_type=='image'),None)
        if first is None:first=next((a for a in offering.assets.all() if a.processing_status=='ready' and a.asset_type=='image'),None)
        row={"id":str(offering.public_id),"slug":offering.slug,"name":offering.name,"summary":offering.summary,"base_price":str(offering.base_price),"assetId":str(first.public_id) if first else "","href":f"/site/{business.slug}/{'services' if is_service else 'product'}/{offering.slug}"}
        result["services" if is_service else "products"].append(row)
    if kind=="event":
        event=item
        result['event']={"title":event.title,"date":timezone.localtime(event.starts_at).strftime('%B %d, %Y · %I:%M %p'),"venue":event.location.name if event.location_id else "","description":event.description}
        from zoneinfo import ZoneInfo
        try:event_zone=ZoneInfo(event.timezone or 'Asia/Manila')
        except (ValueError,KeyError):event_zone=timezone.get_current_timezone()
        local=timezone.localtime(event.starts_at,event_zone)
        sections=event.sections_config or {}
        rsvp=sections.get('rsvp',{})
        from scheduling.views import event_rsvp_deadline
        deadline=event_rsvp_deadline(event)
        result['event'].update({'date':local.strftime('%B %d, %Y · %I:%M %p'),'startsAt':event.starts_at.isoformat(),'timezone':event.timezone,'countdownDays':max(0,(event.starts_at-timezone.now()).days),'rsvp':rsvp,'rsvpOpen':bool(event.public_rsvp_enabled and event.status=='open' and (not deadline or timezone.now()<deadline)),
          'people':[{'name':v.name,'role':v.role,'body':v.subtitle} for v in event.participants.all()],
          'stories':[{'title':v.title,'body':v.body} for v in event.story_blocks.all()],
          'notes':sections.get('event_notes',{}).get('items',[]) if sections.get('event_notes',{}).get('enabled') else [],
          'gifts':[],
          'wishes':[{'id':str(v.public_id),'name':v.full_name,'message':v.guest_message} for v in event.guests.filter(wish_approved=True).exclude(guest_message='')[:30]],
          'venueAddress':event.location.address if event.location_id else '',
          'mapUrl':next((v.map_url for v in event.schedule_entries.all() if v.map_url),'')})
        dress=sections.get('dress_code',{})
        if dress.get('enabled'):result['event']['notes']=[{'title':dress.get('heading','Dress code'),'body':dress.get('description','')}]+result['event']['notes']
        result['navigation']=[{'label':'The day','href':'#programme'}]+([{'label':'RSVP','href':'#rsvp'}] if event.public_rsvp_enabled else [])
        result['schedule']=[{"id":str(entry.public_id),"time":timezone.localtime(entry.starts_at,event_zone).strftime('%I:%M %p') if getattr(entry,'starts_at',None) else getattr(entry,'time_text',''),"title":entry.title,"description":getattr(entry,'description',''),"location":getattr(entry,'venue_name','')} for entry in event.schedule_entries.all()]
        for media in event.media.all():assets[f"event-{media.public_id}"]={"url":public_url(media.image),"alt":media.alt_text,"type":"image","version":media.image.name}
        lead=next(iter(event.media.filter(placement='hero')),None)
        if lead:assets['hero']={"url":public_url(lead.image),"alt":lead.alt_text,"version":lead.image.name,"type":"image"}
        elif event.thumbnail:assets['hero']={"url":public_url(event.thumbnail),"alt":event.title,"version":event.thumbnail.name,"type":"image"}
    if not include_library:
        used={'brand-logo'} if business.logo else set()
        for region in result.get('frame',{}).get('regions',[]):nodes.extend(iter_nodes(region))
        for n in nodes:
            props=n.get('props',{});used.update(props.get('assetIds',[]))
            if isinstance(props.get('assetId'),str):used.add(props['assetId'])
            if isinstance(props.get('assetId'),dict):
                binding=props['assetId']
                if binding.get('source') == 'item':
                    # Repeater values may use only media referenced by approved public rows.
                    for collection in ('products', 'services'):
                        used.update(row['assetId'] for row in result.get(collection, []) if row.get('assetId'))
                else:
                    value=result
                    for key in (str(binding.get('source',''))+'.'+str(binding.get('path',''))).split('.'):
                        if isinstance(value,dict): value=value.get(key)
                        elif isinstance(value,list) and key.isdigit() and int(key)<len(value):value=value[int(key)]
                        else:value=None;break
                    if isinstance(value,str) and value in assets:used.add(value)
            if n.get('type') == 'repeater':
                source=props.get('source')
                if source in {'products','services'}:
                    used.update(row['assetId'] for row in result[source] if row.get('assetId'))
            for style in [n.get('style',{}),*n.get('responsive',{}).values()]:
                bg=style.get('background',{})
                used.update(v for v in [bg.get('assetId'),bg.get('posterId')] if v)
            if n.get('type') in {'products','services'}:
                used.update(row['assetId'] for row in result[n['type']][:props.get('limit',6)] if row['assetId'])
        used.add(document.get('seo', {}).get('socialImage'))
        for n in iter_nodes(document):
            if isinstance(n.get('props', {}).get('posterId'), str): used.add(n['props']['posterId'])
        result['assets']={k:v for k,v in assets.items() if k in used}
    return result

def resolve_data(request,website,review=False):
    return resolved_for_document(request,website,website.draft.document if website.draft_id else {"children":[]},include_library=not review,global_stage="draft")

def review_data(request,share):
    current=resolved_for_document(request,share.revision.website,share.revision.document,include_library=True)
    frozen=share.data_snapshot
    for identifier,asset in frozen.get('assets',{}).items():
        if identifier not in current['assets'] or current['assets'][identifier].get('version')!=asset.get('version'):
            raise PermissionDenied("A reviewed image was changed or withdrawn. Request a new preview.")
    for kind in ['products','services']:
        available={row['id'] for row in current.get(kind,[])}
        if any(row['id'] not in available for row in frozen.get(kind,[])):
            raise PermissionDenied("A reviewed item is no longer public. Request a new preview.")
    available_wishes={row['id'] for row in current.get('event',{}).get('wishes',[])}
    if any(row.get('id') and row['id'] not in available_wishes for row in frozen.get('event',{}).get('wishes',[])):
        raise PermissionDenied('A reviewed guest message is no longer public. Request a new preview.')
    return frozen

def after_publish(request,website):
    business,kind,item=target(website)
    from website_builder.services.globals import public_document
    document=public_document(website.tenant,website.draft.document)
    data=resolved_for_document(request,website,document,include_library=True,global_stage='published')
    nodes=list(iter_nodes(document))
    for linked in data.get('globalSections',{}).values():nodes.extend(iter_nodes(linked['node']))
    if kind!='event' and any(n.get('type')=='event-schedule' or str(n.get('props',{}).get('widgetId','')).startswith('pixelcore.event-') or isinstance(n.get('props',{}).get('text'),dict) and n['props']['text'].get('source')=='event' for n in nodes):
        from django.core.exceptions import ValidationError
        raise ValidationError('Connect this layout to an event before publishing event elements.')
    if kind=='layout':
        from django.core.exceptions import ValidationError
        if sorted(n['type'] for n in website.draft.document['children'])!=['footer','header']:raise ValidationError('A site-wide layout must contain exactly one header and footer. Edit page content in its own workspace.')
        item.cache_version+=1;item.save(update_fields=['cache_version','updated_at'])
    elif kind=='event':
        if any(n.get('props',{}).get('widgetId')=='pixelcore.event-rsvp' for n in nodes) and not item.public_rsvp_enabled:
            from django.core.exceptions import ValidationError
            raise ValidationError('RSVP is disabled in the event settings. Enable it there before publishing an RSVP block.')
        item.website_enabled=True
        item.website_published_at=item.website_published_at or timezone.now()
        item.save(update_fields=['website_enabled','website_published_at','updated_at'])
    else:
        item.status='published';item.published_at=timezone.now();item.save(update_fields=['status','published_at','updated_at'])
        item.site.status='published';item.site.cache_version+=1;item.site.save(update_fields=['status','cache_version','updated_at'])
    record_audit(business,request.user,'site.visual_builder_published',kind,item.public_id,{'revision':website.version})

def public_payload(request,business,kind,item):
    if not enabled():return None
    from website_builder.models import Website
    site=Website.objects.select_related('published').filter(tenant=str(business.public_id),key=f'{kind}:{item.public_id}',published__isnull=False).first()
    if site is None:return None
    from website_builder.services.globals import public_document
    document=public_document(site.tenant,site.published.document)
    return {'document':document,'data':resolved_for_document(request,site,document,global_stage='published'),'baseUrl':f'/site/{business.slug}'}

def make_node(kind,props=None,children=None,identifier=None):
    return {'id':identifier or str(uuid.uuid4()),'type':kind,'props':props or {},'children':children or [],'style':{},'responsive':{}}

def initial_document(business,kind,item):
    kit=brand_kit(business,item if kind=='event' else None)
    root=make_node('page',identifier=str(item.public_id));root.update(schemaVersion=1,title=item.name if kind=='layout' else item.title,mode='live',theme={'colors':{**COLORS,**kit['colors']},'headingFont':kit['headingFont'],'bodyFont':kit['bodyFont'],'baseSize':16,'scale':1.25,'radius':4})
    def section(name,children):return make_node('section',{'name':name},children)
    def heading(value,level=2):return make_node('heading',{'text':value,'level':level})
    def text(value):return make_node('text',{'text':value})
    if kind=='layout':
        root['children']=default_regions(business,item)
        return root
    if kind=='event':
        root['children']=[section('Invitation',[heading({'source':'event','path':'title'},1),text({'source':'event','path':'date'}),text({'source':'event','path':'venue'}),make_node('image',{'assetId':'hero','alt':item.title})]),section('Programme',[heading('The programme'),make_node('event-schedule',{'source':'schedule','limit':20})])]
        for story in item.story_blocks.all():
            root['children'].append(section(story.title or 'Our story',[heading(story.title or 'Our story'),text(story.body)]))
        media=[f'event-{m.public_id}' for m in item.media.all()]
        if media:root['children'].append(section('Gallery',[make_node('gallery',{'assetIds':media[:50]})]))
        if item.public_rsvp_enabled:root['children'].append(section('RSVP',[make_node('widget',{'widgetId':'pixelcore.event-rsvp','variant':'inline','source':'event'})]))
    else:
        revision=item.draft_revision or item.published_revision
        for block in revision.content.get('blocks',[]) if revision else []:
            s=block.get('settings',{});type_=block.get('type');children=[]
            if s.get('heading'):children.append(heading(s['heading'],1 if type_ in {'hero','commerce_hero'} else 2))
            if s.get('body'):children.append(text(s['body']))
            if s.get('message'):children.append(text(s['message']))
            if type_ in {'product_grid','featured_products','product_rail'}:children.append(make_node('products',{'source':'products','limit':min(int(s.get('limit',6)),50)}))
            elif type_=='service_grid':children.append(make_node('services',{'source':'services','limit':min(int(s.get('limit',6)),50)}))
            elif type_=='gallery':children.append(make_node('gallery',{'assetIds':s.get('asset_ids',[])[:50]}))
            elif type_ in {'text','policy'}:
                document=s.get('document',[])
                if isinstance(document,list):children += [text(v if isinstance(v,str) else v.get('text','')) for v in document]
            for key in ['primary','secondary']:
                if s.get(f'{key}_label'):children.append(make_node('button',{'text':s[f'{key}_label'],'href':f'/site/{business.slug}'+s.get(f'{key}_path','')}))
            if s.get('asset_id'):children.append(make_node('image',{'assetId':str(s['asset_id']),'alt':s.get('heading','')}))
            elif type_ in {'hero','commerce_hero'}:children.append(make_node('image',{'assetId':'hero','alt':business.display_name}))
            for item_ in s.get('items',[]):
                if isinstance(item_,dict):
                    if item_.get('heading') or item_.get('question'):children.append(heading(item_.get('heading') or item_['question'],3))
                    if item_.get('body') or item_.get('answer'):children.append(text(item_.get('body') or item_['answer']))
            if children:root['children'].append(section(type_.replace('_',' ').title(),children))
        if not root['children']:root['children']=[section('Introduction',[heading(business.display_name,1),text(business.description)])]
    return root

class BuilderWorkspaceView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,public_id):
        if not enabled():return Response({'error':{'code':'BUILDER_NOT_INSTALLED','message':'Install the sibling website-builder repository and restart the backend.'}},status=503)
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft
        from website_builder.views import website_payload
        business=member_business(request.user,public_id,roles=('owner','admin','manager'))
        kind=serializers.ChoiceField(choices=['page','event','layout']).run_validation(request.data.get('kind','page'))
        identifier=serializers.UUIDField().run_validation(request.data.get('sourceId'))
        if kind=='event':
            from django.shortcuts import get_object_or_404
            item=get_object_or_404(VenueEvent,business=business,public_id=identifier)
        elif kind=='layout':
            from django.shortcuts import get_object_or_404
            item=get_object_or_404(Site,business=business,public_id=identifier)
        else:
            from django.shortcuts import get_object_or_404
            item=get_object_or_404(SitePage,site__business=business,public_id=identifier)
        site,_=Website.objects.get_or_create(tenant=str(business.public_id),key=f'{kind}:{item.public_id}')
        if not site.draft_id:site=save_draft(site.id,initial_document(business,kind,item),0,request.user)
        return Response(website_payload(request._request,site))


def retire_publication(business,kind,item):
    """An explicit publication from the legacy editor selects that renderer again."""
    if enabled():
        from website_builder.models import Website
        Website.objects.filter(tenant=str(business.public_id),key=f"{kind}:{item.public_id}").update(published=None)


def default_regions(business,site):
    branding=business.branding or {};footer=branding.get('storefront',{}).get('footer',{})
    header=make_node('header',{'name':'Header','variant':'left'},identifier='host-header')
    end=make_node('footer',{'name':'Footer','variant':'columns'},identifier='host-footer')
    header['style']={'backgroundColor':branding.get('background_color',COLORS['background']),'color':branding.get('text_color',COLORS['text'])}
    end['style']={k:v for k,v in {'backgroundColor':footer.get('background_color',branding.get('background_color',COLORS['background'])),'color':footer.get('text_color',branding.get('text_color',COLORS['text']))}.items() if isinstance(v,str) and len(v)==7 and v.startswith('#')}
    return [header,end]

def frame_data(business,site,*,draft=False):
    from website_builder.models import Website
    layout=Website.objects.select_related('draft','published').filter(tenant=str(business.public_id),key=f'layout:{site.public_id}').first()
    revision=(layout.draft if draft else layout.published) if layout else None
    import copy
    regions=copy.deepcopy(revision.document['children']) if revision else default_regions(business,site)
    if revision:
        colors=revision.document['theme']['colors']
        for region in regions:
            for key in ['color','backgroundColor']:
                if key in region.get('style',{}):region['style'][key]=colors.get(region['style'][key],region['style'][key])
    return {'owner':'host','sourceId':str(site.public_id),'revisionId':str(revision.id) if revision else None,'regions':regions}



def data_sources(kind):
    """Explicit public fields; private invitation records are never a binding source."""
    def source(key, label, fields, collection=False):
        return {'id': key, 'label': label, 'kind': 'collection' if collection else 'record',
                'fields': [{'path': path, 'label': title, 'type': type_} for path, title, type_ in fields]}
    catalog = [source('identity', 'Business', [('name', 'Name', 'text'), ('description', 'Description', 'text'), ('address', 'Address', 'text'), ('phone', 'Phone', 'text'), ('homeUrl', 'Home link', 'url')])]
    if kind == 'event':
        catalog += [source('event', 'Event', [('title', 'Title', 'text'), ('date', 'Date', 'text'), ('venue', 'Venue', 'text'), ('description', 'Description', 'text')]),
                    source('schedule', 'Programme', [('title', 'Title', 'text'), ('time', 'Time', 'text'), ('location', 'Location', 'text'), ('description', 'Description', 'text')], True),
                    source('event.people', 'Event people', [('name', 'Name', 'text'), ('role', 'Role', 'text'), ('body', 'Description', 'text')], True),
                    source('event.stories', 'Event stories', [('title', 'Title', 'text'), ('body', 'Story', 'text')], True)]
    else:
        fields = [('name', 'Name', 'text'), ('summary', 'Summary', 'text'), ('href', 'Detail link', 'url'), ('assetId', 'Image', 'asset'), ('base_price', 'Price', 'currency')]
        catalog += [source('products', 'Published products', fields, True), source('services', 'Published services', fields, True)]
    return catalog


def validate_global_publish(request, source_site, section):
    """Validate global live changes without publishing or modifying page drafts."""
    from website_builder.models import Website
    from website_builder.services.globals import linked_ids
    from django.core.exceptions import ValidationError
    for site in Website.objects.filter(tenant=source_site.tenant).select_related('published'):
        if not site.published_id or str(section.id) not in linked_ids(site.published.document): continue
        business, kind, item = target(site)
        nodes = list(iter_nodes(section.published.node))
        if kind != 'event' and any(n.get('type') == 'event-schedule' or str(n.get('props', {}).get('widgetId', '')).startswith('pixelcore.event-') or any(isinstance(v, dict) and (v.get('source') == 'event' or str(v.get('source', '')).startswith('event.')) for v in n.get('props', {}).values()) or str(n.get('props', {}).get('source', '')).startswith('event') for n in nodes):
            raise ValidationError('This global section uses event data on a page without an event context.')
        if kind == 'event' and not item.public_rsvp_enabled and any(n.get('props', {}).get('widgetId') == 'pixelcore.event-rsvp' for n in nodes):
            raise ValidationError('Enable RSVP in every affected event before publishing this global section.')


def asset_payload(asset):
    storage = asset.file.storage
    origin = urlsplit(settings.PIXELCORE_PUBLIC_API_URL)
    def url(name): return urljoin(f'{origin.scheme}://{origin.netloc}/', storage.url(name))
    metadata = asset.metadata if isinstance(asset.metadata, dict) else {}
    candidates = metadata.get('builderRenditions', [])
    if not isinstance(candidates, list): candidates = []
    stem = asset.file.name.rsplit('.', 1)[0]
    # Generic asset metadata is editable by the host. Only this asset's generated
    # filenames may become public rendition URLs; never arbitrary storage paths.
    renditions = [{'url': url(r['name']), 'width': r['width']} for r in candidates[:10]
                  if isinstance(r, dict) and type(r.get('width')) is int and r['width'] in (640, 1280)
                  and r.get('name') == f"{stem}-{r['width']}.webp"]
    def dimension(key):
        value = metadata.get(key)
        return value if type(value) is int and 0 < value <= 2400 else None
    return {'url': public_url(asset.file), 'alt': asset.alt_text or asset.title, 'type': asset.asset_type,
            'version': asset.file.name, 'width': dimension('width'), 'height': dimension('height'), 'renditions': renditions}


def upload_media(request, website, prepared, alt):
    from website_builder.services.media import persist_image
    business, _, _ = target(website)
    asset = BusinessAsset(business=business, title=alt[:160] or 'Website image', alt_text=alt,
        asset_type='image', mime_type='image/webp', size_bytes=len(prepared['content']), uploaded_by=request.user)
    prefix = asset.file.field.generate_filename(asset, 'image.webp').rsplit('/', 1)[0]
    metadata = persist_image(prepared, asset.file.storage, prefix)
    asset.file.name = metadata['name']
    asset.metadata = {'width': metadata['width'], 'height': metadata['height'], 'builderRenditions': metadata['renditions']}
    try: asset.save()
    except Exception:
        for name in [metadata['name'], *[r['name'] for r in metadata['renditions']]]: asset.file.storage.delete(name)
        raise
    record_audit(business, request.user, 'asset.uploaded', 'business_asset', asset.public_id)
    return {'id': str(asset.public_id), **asset_payload(asset)}


def public_seo(visual, fallback):
    """Published document metadata with stricter host indexing preserved."""
    seo = visual['document'].get('seo', {})
    result = {**fallback}
    for key in ('title', 'description', 'canonical'):
        if seo.get(key): result[key] = seo[key]
    if seo.get('noIndex') or 'noindex' in fallback.get('robots', ''): result['robots'] = 'noindex,nofollow'
    result['socialTitle'] = seo.get('socialTitle') or result.get('title', '')
    result['socialDescription'] = seo.get('socialDescription') or result.get('description', '')
    result['socialImage'] = visual['data'].get('assets', {}).get(seo.get('socialImage'), {}).get('url', '')
    return result


def hidden_builder_pages(business):
    if not enabled(): return set()
    from website_builder.models import Website
    return set(Website.objects.filter(tenant=str(business.public_id), key__startswith='page:', published__document__seo__noIndex=True).values_list('key', flat=True))
