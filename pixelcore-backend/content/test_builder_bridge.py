from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from businesses.models import Business, BusinessMembership, BusinessAsset
from content.models import Site, SitePage
from content.services import create_revision,publish_revision
from content.builder_bridge import initial_document

class SharedBuilderBridgeTests(APITestCase):
    def setUp(self):
        self.owner=get_user_model().objects.create_user(username='builder-owner',email='builder@example.test',password='BuilderTests123!')
        self.business=Business.objects.create(display_name='Builder store',slug='builder-store',created_by=self.owner)
        BusinessMembership.objects.create(business=self.business,user=self.owner,role='owner',status='active')
        self.site=Site.objects.create(business=self.business,name='Builder site')
        self.page=SitePage.objects.create(site=self.site,title='Home',slug='home',page_type='home')
        revision=create_revision(self.page,{'schema_version':1,'blocks':[{'id':'hero','type':'hero','version':1,'settings':{'heading':'Existing heading','body':'Existing copy'}}]},self.owner)
        publish_revision(self.page,revision,self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.owner).access_token}')
    def setup_builder(self):
        response=self.client.post(f'/api/businesses/{self.business.public_id}/website-builder/',{'kind':'page','sourceId':str(self.page.public_id)},format='json')
        self.assertEqual(response.status_code,200,response.data)
        return response.data
    def test_workspace_uses_existing_content_without_changing_publication(self):
        setup=self.setup_builder()
        self.assertIn('Existing heading',str(setup['document']))
        self.page.refresh_from_db();self.assertEqual(self.page.status,'published')
        self.assertIsNotNone(self.page.published_revision)
    def test_jwt_native_shared_api_and_draft_public_separation(self):
        setup=self.setup_builder();self.client.get('/api/website-builder/csrf/')
        token=self.client.cookies['csrftoken'].value
        doc=setup['document'];doc['children'][0]['children'][0]['props']['text']='Visual heading'
        response=self.client.put(f'/api/website-builder/sites/{setup["id"]}/',{'document':doc,'expectedVersion':setup['version']},format='json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code,200,response.content)
        before=self.client.get(f'/api/public/{self.business.slug}/site/')
        self.assertEqual(before.status_code,200)
        self.assertNotIn('builder',before.data)
        published=self.client.post(f'/api/website-builder/sites/{setup["id"]}/publish/',{'expectedVersion':response.json()['version']},format='json',HTTP_X_CSRFTOKEN=token)
        self.assertEqual(published.status_code,200,published.content)
        from content.builder_bridge import public_payload
        from rest_framework.test import APIRequestFactory
        payload=public_payload(APIRequestFactory().get('/'),self.business,'page',self.page)
        self.assertIn('Visual heading',str(payload['document']))
        live=self.client.get(f'/api/public/{self.business.slug}/site/')
        self.assertEqual(live.status_code,200)
        self.assertIn('Visual heading',str(live.data['builder']['document']))
    def test_other_tenant_cannot_open_shared_api(self):
        setup=self.setup_builder()
        other=get_user_model().objects.create_user(username='other-builder',password='OtherBuilder123!')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(other).access_token}')
        response=self.client.get(f'/api/website-builder/sites/{setup["id"]}/')
        self.assertEqual(response.status_code,403)
    def test_new_legacy_draft_keeps_live_publication(self):
        create_revision(self.page,{'schema_version':1,'blocks':[]},self.owner)
        self.page.refresh_from_db();self.assertEqual(self.page.status,'published')

    def test_old_signed_preview_keeps_its_original_revision(self):
        from content.services import make_preview_token
        self.page.refresh_from_db()
        token=make_preview_token(self.page,self.page.draft_revision)
        create_revision(self.page,{"schema_version":1,"blocks":[]},self.owner)
        response=self.client.get("/api/public/site-preview/",{"token":token})
        self.assertEqual(response.status_code,200)
        self.assertIn("Existing heading",str(response.data["page"]["content"]))

    def test_event_layout_stays_published_while_event_data_changes(self):
        from datetime import timedelta
        from django.utils import timezone
        from scheduling.models import VenueEvent, EventSchedule, EventStoryBlock
        from website_builder.services.revisions import publish
        event = VenueEvent.objects.create(business=self.business, title="Autumn launch", event_type="wedding", status="open", starts_at=timezone.now()+timedelta(days=30), organizer_name="Launch team", created_by=self.owner)
        schedule = EventSchedule.objects.create(event=event, title="Doors open", starts_at=event.starts_at, venue_name="Main hall")
        EventStoryBlock.objects.create(event=event, title="Our beginning", body="A real story")
        response = self.client.post(f"/api/businesses/{self.business.public_id}/website-builder/", {"kind":"event", "sourceId":str(event.public_id)}, format="json")
        self.assertEqual(response.status_code,200,response.data)
        setup = response.data
        self.assertEqual(setup["data"]["schedule"][0]["location"],"Main hall")
        self.assertIn("Our beginning",str(setup["document"]))
        site = publish(setup["id"],setup["version"])
        from content.builder_bridge import after_publish
        from rest_framework.test import APIRequestFactory
        request = APIRequestFactory().post("/");request.user=self.owner
        after_publish(request,site)
        schedule.title="Welcome reception";schedule.save(update_fields=["title"])
        event.title="Updated launch";event.save(update_fields=["title"])
        self.client.credentials()
        public = self.client.get(f"/api/public/events/{event.public_id}/website/")
        self.assertEqual(public.status_code,200,public.data)
        self.assertEqual(public.data["event"]["builder"]["data"]["event"]["title"],"Updated launch")
        self.assertEqual(public.data["event"]["builder"]["data"]["schedule"][0]["title"],"Welcome reception")
        self.assertEqual(public.data["event"]["builder"]["document"],setup["document"])

    def test_guest_can_comment_but_cannot_resolve_or_view_withdrawn_media(self):
        from urllib.parse import urlsplit
        from businesses.models import BusinessAsset
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft
        from rest_framework.test import APIClient
        asset=BusinessAsset.objects.create(business=self.business,asset_type="image",title="Review image",file="demo/review.png",size_bytes=68,mime_type="image/png",uploaded_by=self.owner)
        setup=self.setup_builder()
        doc=setup["document"]
        doc["children"][0]["children"].append({"id":"review-image", "type":"image", "props":{"assetId":str(asset.public_id),"alt":"Review image"}, "children":[],"style":{},"responsive":{}})
        site=save_draft(setup["id"],doc,setup["version"],self.owner)
        share=self.client.post(f"/api/website-builder/sites/{site.id}/reviews/",{"expectedVersion":site.version},format="json")
        self.assertEqual(share.status_code,200,share.content)
        share_id=share.json()["shareId"]
        guest=APIClient(enforce_csrf_checks=True)
        guest.get("/api/website-builder/csrf/")
        headers={"HTTP_X_CSRFTOKEN":guest.cookies["csrftoken"].value}
        opened=guest.post("/api/website-builder/reviews/exchange/",{"token":urlsplit(share.json()["url"]).fragment},format="json",**headers)
        self.assertEqual(opened.status_code,200,opened.content)
        self.assertFalse(opened.json()["canResolve"])
        self.assertTrue(opened.json()["canComment"])
        comments_url=f"/api/website-builder/reviews/{share_id}/comments/"
        commented=guest.post(comments_url,{"name":"Guest reviewer","body":"Please adjust the image.","anchor":{"nodeId":"review-image","x":.4,"y":.6}},format="json",**headers)
        self.assertEqual(commented.status_code,200,commented.content)
        thread=commented.json()["threads"][0]
        denied=guest.post(f"/api/website-builder/reviews/{share_id}/threads/{thread['id']}/",{"resolved":True},format="json",**headers)
        self.assertIn(denied.status_code,[401,403])
        owner=self.client.post(f"/api/website-builder/reviews/{share_id}/threads/{thread['id']}/",{"resolved":True},format="json")
        self.assertEqual(owner.status_code,200,owner.content)
        asset.processing_status="rejected";asset.save(update_fields=["processing_status"])
        self.assertEqual(guest.get(f"/api/website-builder/reviews/{share_id}/").status_code,403)
        self.assertEqual(guest.get(comments_url).status_code,403)

    def test_explicit_legacy_publication_selects_legacy_renderer_again(self):
        from website_builder.services.revisions import publish
        from website_builder.models import Website
        setup=self.setup_builder();publish(setup["id"],setup["version"])
        from content.builder_bridge import retire_publication, public_payload
        from rest_framework.test import APIRequestFactory
        retire_publication(self.business,"page",self.page)
        self.assertIsNone(public_payload(APIRequestFactory().get("/"),self.business,"page",self.page))
        self.assertIsNotNone(Website.objects.get(pk=setup["id"]).draft_id)

    def test_global_frame_drafts_and_publications_are_independent_of_page_publication(self):
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft
        setup=self.setup_builder()
        self.assertEqual(setup['capabilities']['workspace']['sourceId'],str(self.page.public_id))
        self.assertEqual(setup['data']['frame']['owner'],'host')
        layout=self.client.post(f'/api/businesses/{self.business.public_id}/website-builder/',{'kind':'layout','sourceId':str(self.site.public_id)},format='json')
        self.assertEqual(layout.status_code,200,layout.data)
        frame=layout.data;doc=frame['document'];doc['children'][0]['style']['backgroundColor']='#123456'
        changed=save_draft(frame['id'],doc,frame['version'],self.owner)
        before=self.client.get(f'/api/public/{self.business.slug}/site/')
        self.assertNotEqual(before.data['builderFrame']['regions'][0]['style']['backgroundColor'],'#123456')
        published=self.client.post(f'/api/website-builder/sites/{changed.id}/publish/',{'expectedVersion':changed.version},format='json')
        self.assertEqual(published.status_code,200,published.content)
        public=self.client.get(f'/api/public/{self.business.slug}/site/')
        self.assertEqual(public.data['builderFrame']['regions'][0]['style']['backgroundColor'],'#123456')
        self.assertNotIn('builder',public.data)
        self.assertIsNone(Website.objects.get(pk=setup['id']).published_id)
        self.assertEqual(len(frame['capabilities']['workspace']['affectedPages']),1)

    def test_saved_section_library_is_tenant_scoped_and_validated(self):
        setup=self.setup_builder()
        path=f'/api/website-builder/sites/{setup["id"]}/sections/'
        created=self.client.post(path,{'name':'Intro','node':setup['document']['children'][0]},format='json')
        self.assertEqual(created.status_code,200,created.content)
        invalid=self.client.post(path,{'name':'Unsafe','node':{'type':'section','props':{'html':'<script>'}}},format='json')
        self.assertEqual(invalid.status_code,400)
        self.client.credentials()
        self.assertEqual(self.client.get(path).status_code,401)

    def test_published_rsvp_uses_existing_invitation_and_private_headers(self):
        from datetime import timedelta
        from django.utils import timezone
        from scheduling.models import VenueEvent,EventGuest
        from scheduling.services import issue_event_access_token
        from website_builder.services.revisions import publish
        from content.builder_bridge import after_publish
        from rest_framework.test import APIRequestFactory
        event=VenueEvent.objects.create(business=self.business,title='Existing wedding',event_type='wedding',status='open',starts_at=timezone.now()+timedelta(days=30),organizer_name='Organizers',created_by=self.owner,public_rsvp_enabled=True,max_guests=10)
        guest=EventGuest.objects.create(event=event,full_name='Private invited guest',dietary_notes='Private dietary note')
        token=issue_event_access_token(guest,'invite_token_digest')
        setup=self.client.post(f'/api/businesses/{self.business.public_id}/website-builder/',{'kind':'event','sourceId':str(event.public_id)},format='json').data
        site=publish(setup['id'],setup['version']);request=APIRequestFactory().post('/');request.user=self.owner;after_publish(request,site)
        self.client.credentials()
        path=f'/api/public/events/{event.public_id}/rsvp/{token}/'
        opened=self.client.get(path)
        self.assertEqual(opened.status_code,200)
        self.assertIn('no-store',opened['Cache-Control'])
        self.assertEqual(opened['Referrer-Policy'],'no-referrer')
        self.assertIn('pixelcore.event-rsvp',str(opened.data['event']['builder']['document']))
        self.assertNotIn('Private dietary note',str(opened.data['event']['builder']['data']))
        response=self.client.patch(path,{'response':'accepted','party_size':1},format='json')
        self.assertEqual(response.status_code,200,response.data)
        guest.refresh_from_db();self.assertEqual(guest.response,'accepted')
        denied=self.client.get(f'/api/public/events/{event.public_id}/rsvp/wrong-token/')
        self.assertEqual(denied.status_code,403)
        self.assertIn('no-store',denied['Cache-Control'])

    def test_page_publish_keeps_global_draft_private_and_review_freezes_frame(self):
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft,create_review
        from website_builder.services.reviews import add_comment
        from content.builder_bridge import resolve_data,review_data
        from rest_framework.test import APIRequestFactory
        setup=self.setup_builder()
        request=APIRequestFactory().get('/');request.user=self.owner
        site=Website.objects.select_related('draft').get(pk=setup['id'])
        share,_=create_review(site.id,site.version,resolve_data(request,site,review=True))
        original=share.data_snapshot['frame']['regions'][0]['style']['backgroundColor']
        layout=self.client.post(f'/api/businesses/{self.business.public_id}/website-builder/',{'kind':'layout','sourceId':str(self.site.public_id)},format='json').data
        doc=layout['document'];doc['children'][0]['style']['backgroundColor']='#987654'
        changed=save_draft(layout['id'],doc,layout['version'],self.owner)
        page_publish=self.client.post(f'/api/website-builder/sites/{site.id}/publish/',{'expectedVersion':site.version},format='json')
        self.assertEqual(page_publish.status_code,200,page_publish.content)
        self.assertIsNone(Website.objects.get(pk=changed.id).published_id)
        public=self.client.get(f'/api/public/{self.business.slug}/site/')
        self.assertEqual(public.data['builderFrame']['regions'][0]['style']['backgroundColor'],original)
        layout_publish=self.client.post(f'/api/website-builder/sites/{changed.id}/publish/',{'expectedVersion':changed.version},format='json')
        self.assertEqual(layout_publish.status_code,200,layout_publish.content)
        self.assertEqual(review_data(request,share)['frame']['regions'][0]['style']['backgroundColor'],original)
        thread=add_comment(share.id,display_name='Reviewer',body='Header feedback',anchor={'nodeId':'host-header'})
        self.assertEqual(thread.node_id,'host-header')

    def test_page_cannot_publish_a_widget_without_its_event_context(self):
        from website_builder.services.revisions import save_draft
        from website_builder.models import Website
        setup=self.setup_builder();doc=setup['document']
        doc['children'].append({'id':'unbound-rsvp','type':'widget','props':{'widgetId':'pixelcore.event-rsvp','source':'event'},'style':{},'responsive':{},'children':[]})
        site=save_draft(setup['id'],doc,setup['version'],self.owner)
        response=self.client.post(f'/api/website-builder/sites/{site.id}/publish/',{'expectedVersion':site.version},format='json')
        self.assertEqual(response.status_code,400,response.content)
        self.assertIsNone(Website.objects.get(pk=site.id).published_id)

    def test_shared_template_library_uses_business_permissions_and_preserves_source_data(self):
        from rest_framework.test import APIClient
        setup = self.setup_builder()
        path = f'/api/website-builder/sites/{setup["id"]}/templates/'
        self.client.get('/api/website-builder/csrf/')
        headers = {'HTTP_X_CSRFTOKEN': self.client.cookies['csrftoken'].value}
        document = setup['document']
        document['children'][0]['style']['fontFamily'] = 'Arial'
        response = self.client.post(path, {'name': 'Reusable home', 'document': document}, format='json', **headers)
        self.assertEqual(response.status_code, 200, response.content)
        template = response.json()['template']
        self.assertNotIn('fontFamily', template['document']['children'][0]['style'])
        self.assertNotIn('context', template['document'])
        library = self.client.get(path)
        self.assertEqual(library.json()['templates'][0]['id'], template['id'])
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, 'published')
        other = get_user_model().objects.create_user(username='template-outsider', password='OtherBuilder123!')
        outsider = APIClient()
        outsider.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(other).access_token}')
        self.assertEqual(outsider.get(path).status_code, 403)
        self.assertEqual(outsider.post(path, {'name': 'Forbidden', 'document': document}, format='json').status_code, 403)
        guest = APIClient()
        self.assertEqual(guest.get(path).status_code, 401)

    def test_live_global_repeaters_resolve_published_products_and_ready_assets(self):
        from businesses.models import BusinessAsset
        from catalog.models import Offering
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft, publish
        from website_builder.services.globals import create_section, publish_section, update_section
        from rest_framework.test import APIRequestFactory
        from content.builder_bridge import public_payload, resolve_data
        setup = self.setup_builder(); site = Website.objects.select_related('draft').get(pk=setup['id'])
        image = BusinessAsset.objects.create(business=self.business, asset_type='image', title='Catalog image', file='demo/catalog.png', size_bytes=68, mime_type='image/png', uploaded_by=self.owner)
        unlisted = BusinessAsset.objects.create(business=self.business, asset_type='image', title='Unlisted draft image', file='demo/unlisted-draft.png', size_bytes=68, mime_type='image/png', uploaded_by=self.owner)
        product = Offering.objects.create(business=self.business, name='Live product', slug='live-product', offering_type='physical', base_price='250', status='published')
        product.assets.add(image)
        Offering.objects.create(business=self.business, name='Private draft', offering_type='physical', base_price='100', status='draft')
        from content.builder_bridge import make_node
        card = make_node('container', children=[make_node('heading', {'text': {'source': 'item', 'path': 'name'}}), make_node('image', {'assetId': {'source': 'item', 'path': 'assetId'}, 'alt': {'source': 'item', 'path': 'name'}}), make_node('button', {'text': 'View', 'href': {'source': 'item', 'path': 'href'}})])
        shared_node = make_node('section', children=[make_node('repeater', {'source': 'products', 'limit': 6}, [card])])
        shared = create_section(site, 'Live catalog', shared_node, self.owner)
        publish_section(shared.id, site.tenant, shared.version)
        doc = setup['document']; doc['children'] = [make_node('global-section', {'sectionId': str(shared.id)}, [shared_node])]
        site = save_draft(site.id, doc, site.version, self.owner); publish(site.id, site.version)
        request = APIRequestFactory().get('/'); request.user = self.owner
        public = public_payload(request, self.business, 'page', self.page)
        self.assertEqual([row['name'] for row in public['data']['products']], ['Live product'])
        self.assertIn(str(image.public_id), public['data']['assets'])
        self.assertNotIn(str(unlisted.public_id), public['data']['assets'])
        self.assertEqual(public['data']['globalSections'][str(shared.id)]['version'], 1)
        edited = update_section(shared.id, site, shared_node, 1, actor=self.owner)
        self.assertEqual(resolve_data(request, site)['globalSections'][str(shared.id)]['version'], 2)
        self.assertEqual(public_payload(request, self.business, 'page', self.page)['data']['globalSections'][str(shared.id)]['version'], 1)
        product.name = 'Updated live product'; product.save(update_fields=['name'])
        self.assertEqual(public_payload(request, self.business, 'page', self.page)['data']['products'][0]['name'], 'Updated live product')

    def test_global_review_freezes_content_and_revalidates_media_withdrawal(self):
        from businesses.models import BusinessAsset
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft, create_review
        from website_builder.services.globals import create_section, update_section
        from content.builder_bridge import make_node, resolve_data, review_data
        from django.core.exceptions import PermissionDenied
        from rest_framework.test import APIRequestFactory
        setup = self.setup_builder(); site = Website.objects.select_related('draft').get(pk=setup['id'])
        image = BusinessAsset.objects.create(business=self.business, asset_type='image', title='Global review image', file='demo/global-review.png', size_bytes=68, mime_type='image/png', uploaded_by=self.owner)
        node = make_node('section', children=[make_node('image', {'assetId': str(image.public_id), 'alt': 'Shared image'})])
        shared = create_section(site, 'Media', node, self.owner)
        doc = setup['document']; doc['children'] = [make_node('global-section', {'sectionId': str(shared.id)}, [node])]
        site = save_draft(site.id, doc, site.version, self.owner)
        request = APIRequestFactory().get('/'); request.user = self.owner
        share, _ = create_review(site.id, site.version, resolve_data(request, site, review=True))
        update_section(shared.id, site, make_node('section'), 1, actor=self.owner)
        self.assertEqual(review_data(request, share)['globalSections'][str(shared.id)]['version'], 1)
        image.processing_status = 'rejected'; image.save(update_fields=['processing_status'])
        with self.assertRaises(PermissionDenied): review_data(request, share)

    def test_capability_catalog_is_public_and_recovery_is_user_scoped(self):
        setup = self.setup_builder()
        sources = setup['capabilities']['dataSources']
        self.assertEqual({row['id'] for row in sources}, {'identity', 'products', 'services'})
        self.assertIn({'path': 'base_price', 'label': 'Price', 'type': 'currency'}, next(row for row in sources if row['id'] == 'products')['fields'])
        self.assertNotIn('guests', str(sources))
        path = f'/api/website-builder/sites/{setup["id"]}/'
        first = self.client.get(path).json()['capabilities']['workspace']['recoveryScope']
        manager = get_user_model().objects.create_user(username='builder-manager', password='ManagerBuilder123!')
        BusinessMembership.objects.create(business=self.business, user=manager, role='manager', status='active')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(manager).access_token}')
        second = self.client.get(path).json()['capabilities']['workspace']['recoveryScope']
        self.assertNotEqual(first, second)

    def test_global_event_content_cannot_publish_into_storefront(self):
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft, publish
        from website_builder.services.globals import create_section, update_section, publish_section
        from content.builder_bridge import make_node
        setup = self.setup_builder(); site = Website.objects.select_related('draft').get(pk=setup['id'])
        node = make_node('section', children=[make_node('text', {'text': 'Initial'})])
        shared = create_section(site, 'Shared', node, self.owner); publish_section(shared.id, site.tenant, 1)
        doc = setup['document']; doc['children'] = [make_node('global-section', {'sectionId': str(shared.id)}, [node])]
        site = save_draft(site.id, doc, site.version, self.owner); publish(site.id, site.version)
        node['children'] = [make_node('widget', {'widgetId': 'pixelcore.event-rsvp', 'source': 'event'})]
        update_section(shared.id, site, node, 1, actor=self.owner)
        response = self.client.post(f'/api/website-builder/sites/{site.id}/globals/{shared.id}/publish/', {'expectedVersion': 2}, format='json')
        self.assertEqual(response.status_code, 400, response.content)
        shared.refresh_from_db(); self.assertEqual(shared.published.number, 1)

    def test_anonymous_manifest_removes_unpublished_global_fallback_text(self):
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft, publish
        from website_builder.services.globals import create_section, publish_section, update_section
        from content.builder_bridge import make_node
        setup = self.setup_builder(); site = Website.objects.select_related('draft').get(pk=setup['id'])
        original = make_node('section', children=[make_node('text', {'text': 'Approved public banner'})])
        shared = create_section(site, 'Banner', original, self.owner); publish_section(shared.id, site.tenant, 1)
        draft = make_node('section', children=[make_node('text', {'text': 'Secret unpublished promotion'})])
        update_section(shared.id, site, draft, 1, actor=self.owner)
        doc = setup['document']; doc['children'] = [make_node('global-section', {'sectionId': str(shared.id)}, [draft])]
        site = save_draft(site.id, doc, site.version, self.owner); publish(site.id, site.version)
        self.client.credentials()
        response = self.client.get(f'/api/public/{self.business.slug}/site/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn('Approved public banner', response.content.decode())
        self.assertNotIn('Secret unpublished promotion', response.content.decode())
        site.refresh_from_db(); self.assertIn('Secret unpublished promotion', str(site.published.document))

    def test_page_publication_validates_live_globals_instead_of_unpublished_fallbacks(self):
        from website_builder.models import Website
        from website_builder.services.revisions import save_draft
        from website_builder.services.globals import create_section, publish_section, update_section
        from content.builder_bridge import make_node
        setup = self.setup_builder(); site = Website.objects.select_related('draft').get(pk=setup['id'])
        approved = make_node('section', children=[make_node('text', {'text': 'Public banner'})])
        shared = create_section(site, 'Banner', approved, self.owner); publish_section(shared.id, site.tenant, 1)
        draft = make_node('section', children=[make_node('widget', {'widgetId': 'pixelcore.event-rsvp', 'source': 'event'})])
        update_section(shared.id, site, draft, 1, actor=self.owner)
        doc = setup['document']; doc['children'] = [make_node('global-section', {'sectionId': str(shared.id)}, [draft])]
        site = save_draft(site.id, doc, site.version, self.owner)
        response = self.client.post(f'/api/website-builder/sites/{site.id}/publish/', {'expectedVersion': site.version}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        blocked = self.client.post(f'/api/website-builder/sites/{site.id}/globals/{shared.id}/publish/', {'expectedVersion': 2}, format='json')
        self.assertEqual(blocked.status_code, 400, blocked.content)
        shared.refresh_from_db(); self.assertEqual(shared.published.number, 1)

    def test_builder_upload_uses_business_storage_and_rejects_guest_or_invalid_files(self):
        import tempfile
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        setup = self.setup_builder(); path = f'/api/website-builder/sites/{setup["id"]}/media/'
        def upload():
            stream = BytesIO(); Image.new('RGB', (1400, 800), 'navy').save(stream, 'PNG')
            return SimpleUploadedFile('photo.png', stream.getvalue(), content_type='image/png')
        with tempfile.TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            response = self.client.post(path, {'file': upload(), 'alt': 'Product photo'}, format='multipart')
            self.assertEqual(response.status_code, 200, response.content)
            asset = BusinessAsset.objects.get(public_id=response.json()['asset']['id'])
            self.assertEqual(asset.business, self.business); self.assertEqual(asset.uploaded_by, self.owner)
            self.assertEqual(asset.mime_type, 'image/webp'); self.assertEqual(len(asset.metadata['builderRenditions']), 2)
            self.assertIn(f'businesses/{self.business.public_id}/library/', asset.file.name)
            self.assertTrue(asset.file.storage.exists(asset.file.name))
            self.assertEqual(self.client.get(f'/api/website-builder/sites/{setup["id"]}/').json()['data']['assets'][str(asset.public_id)]['width'], 1400)
            invalid = self.client.post(path, {'file': SimpleUploadedFile('fake.png', b'<script/>', content_type='image/png')}, format='multipart')
            self.assertEqual(invalid.status_code, 400)
            self.client.credentials()
            self.assertEqual(self.client.post(path, {'file': upload()}, format='multipart').status_code, 401)
            self.assertEqual(BusinessAsset.objects.count(), 1)

    def test_published_page_metadata_social_assets_and_host_indexing_policy(self):
        from website_builder.services.revisions import save_draft
        from content.builder_bridge import hidden_builder_pages
        asset = BusinessAsset.objects.create(business=self.business, title='Social image', file='demo/social.webp', mime_type='image/webp', size_bytes=100, asset_type='image', uploaded_by=self.owner)
        setup = self.setup_builder(); doc = setup['document']
        doc['seo'] = {'title': 'Builder search title', 'description': 'Builder description', 'socialTitle': 'Social title', 'socialImage': str(asset.public_id), 'canonical': 'https://example.test/store', 'noIndex': True}
        site = save_draft(setup['id'], doc, setup['version'], self.owner)
        response = self.client.post(f'/api/website-builder/sites/{site.id}/publish/', {'expectedVersion': site.version}, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        self.client.credentials(); payload = self.client.get(f'/api/public/{self.business.slug}/site/').data
        self.assertEqual(payload['seo']['title'], 'Builder search title')
        self.assertEqual(payload['seo']['socialTitle'], 'Social title'); self.assertEqual(payload['seo']['robots'], 'noindex,nofollow')
        self.assertIn(str(asset.public_id), payload['builder']['data']['assets'])
        self.assertIn(f'page:{self.page.public_id}', hidden_builder_pages(self.business))
        from content.builder_bridge import public_seo
        self.assertEqual(public_seo({'document': {'seo': {'noIndex': False}}, 'data': {}}, {'robots': 'noindex,nofollow'})['robots'], 'noindex,nofollow')


    def test_asset_renditions_cannot_reference_other_storage_paths(self):
        from content.builder_bridge import asset_payload
        asset = BusinessAsset.objects.create(business=self.business, title='Photo', file='businesses/own/image.webp', mime_type='image/webp', size_bytes=100, asset_type='image', uploaded_by=self.owner,
            metadata={'width': 'bad', 'height': True, 'builderRenditions': [{'name': 'businesses/other/private.webp', 'width': 640}, {'name': 'businesses/own/image-640.webp', 'width': 640}]})
        payload = asset_payload(asset)
        self.assertIsNone(payload['width']); self.assertIsNone(payload['height'])
        self.assertEqual(len(payload['renditions']), 1)
        self.assertNotIn('other', str(payload))

        for malformed in [[], {'builderRenditions': None}, {'builderRenditions': 'invalid'}, {'width': {}}]:
            asset.metadata = malformed
            self.assertEqual(asset_payload(asset)['renditions'], [])
