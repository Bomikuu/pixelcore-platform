from datetime import timedelta
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from businesses.models import BusinessMembership
from .test_builder_bridge import SharedBuilderBridgeTests
from .models import StudioHandoff

@override_settings(STUDIO_CLIENT_SECRET='test-client-secret', STUDIO_FRONTEND_ORIGIN='http://localhost:4173')
class StudioBridgeTests(APITestCase):
    setUp=SharedBuilderBridgeTests.setUp
    setup_builder=SharedBuilderBridgeTests.setup_builder
    def issue(self):
        r=self.client.post(f'/api/businesses/{self.business.public_id}/studio/handoffs/',{'state':'a'*43,'audience':'http://localhost:4173'},format='json')
        self.assertEqual(r.status_code,200,r.data)
        return r.data
    def exchange(self,value):
        return self.client.post('/api/studio-bridge/exchange/',{**value,'audience':'http://localhost:4173'},format='json',HTTP_X_STUDIO_CLIENT='test-client-secret')
    def gateway(self,grant,operation='overview',args=None):
        return self.client.post('/api/studio-bridge/gateway/',{'grant':grant,'operation':operation,'args':args or {}},format='json',HTTP_X_STUDIO_CLIENT='test-client-secret')
    def test_one_use_exchange_and_verified_business(self):
        value=self.issue();first=self.exchange(value)
        self.assertEqual(first.status_code,200,first.data)
        self.assertEqual(first.data['business']['id'],str(self.business.public_id))
        self.assertEqual(self.exchange(value).status_code,403)
        data=self.gateway(first.data['grant']).data
        self.assertEqual(data['workspace']['name'],'Builder store')
        self.assertFalse(data['capabilities']['manageComponents'])
    def test_expired_wrong_state_or_audience_and_client(self):
        value=self.issue()
        self.assertEqual(self.exchange({**value,'state':'wrong'}).status_code,403)
        self.assertEqual(self.client.post('/api/studio-bridge/exchange/',value,format='json').status_code,403)
        StudioHandoff.objects.update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.exchange(value).status_code,403)
    def test_membership_rechecked_and_grant_revocation(self):
        grant=self.exchange(self.issue()).data['grant']
        BusinessMembership.objects.filter(business=self.business,user=self.owner).update(status='inactive')
        self.assertEqual(self.gateway(grant).status_code,404)
        BusinessMembership.objects.filter(business=self.business,user=self.owner).update(status='active')
        self.assertEqual(self.gateway(grant,'revoke').status_code,200)
        self.assertEqual(self.gateway(grant).status_code,403)
    def test_builder_gateway_preserves_versions_and_blocks_unscoped_paths(self):
        setup=self.setup_builder();grant=self.exchange(self.issue()).data['grant']
        self.assertEqual(self.gateway(grant,'builder',{'route':f'sites/{setup["id"]}/','method':'GET'}).status_code,200)
        response=self.gateway(grant,'builder',{'route':f'sites/{setup["id"]}/','method':'PUT','body':{'document':setup['document'],'expectedVersion':0}})
        self.assertEqual(response.status_code,409,response.data)
        for route in ['csrf/','reviews/exchange/','../auth/me/','https://example.com']:
            self.assertEqual(self.gateway(grant,'builder',{'route':route}).status_code,403)
    def test_open_uses_existing_host_source(self):
        grant=self.exchange(self.issue()).data['grant']
        response=self.gateway(grant,'open',{'kind':'page','sourceId':str(self.page.public_id)})
        self.assertEqual(response.status_code,200,response.data)
        self.assertIn('Existing heading',str(response.data['document']))
    def test_gateway_library_history_and_review_operations_remain_host_owned(self):
        import uuid
        from website_builder.models import Website
        setup=self.setup_builder();grant=self.exchange(self.issue()).data['grant']
        for suffix in ['revisions/','globals/','sections/','templates/']:
            response=self.gateway(grant,'builder',{'route':f'sites/{setup["id"]}/{suffix}','method':'GET'})
            self.assertEqual(response.status_code,200,response.data)
        self.assertEqual(self.gateway(grant,'builder',{'route':f'sites/{setup["id"]}/media/','method':'GET'}).status_code,405)
        review=self.gateway(grant,'builder',{'route':f'sites/{setup["id"]}/reviews/','method':'POST','body':{'expectedVersion':setup['version']}})
        self.assertEqual(review.status_code,200,review.data)
        self.assertIn('/website-review',review.data['url'])
        other=Website.objects.create(tenant=str(uuid.uuid4()),key='page:other')
        self.assertEqual(self.gateway(grant,'builder',{'route':f'sites/{other.id}/','method':'GET'}).status_code,403)
    def test_overview_search_source_pagination_and_summary_are_business_scoped(self):
        from .models import SitePage
        setup=self.setup_builder();grant=self.exchange(self.issue()).data['grant']
        for number in range(105): SitePage.objects.create(site=self.page.site,title=f'Audit page {number:03}',slug=f'audit-page-{number}')
        first=self.gateway(grant,args={'sourceKind':'page','sourcelimit':'20'}).data
        self.assertEqual(first['sourcePage']['total'],106)
        self.assertEqual(len(first['sources']),20)
        last=self.gateway(grant,args={'sourceKind':'page','sourceQ':'Audit page 104'}).data
        self.assertEqual(len(last['sources']),1)
        self.assertEqual(last['sources'][0]['title'],'Audit page 104')
        self.assertEqual(last['summary']['websites'],1)
    def test_review_owner_and_design_summary_queries_survive_the_restricted_gateway(self):
        setup=self.setup_builder();grant=self.exchange(self.issue()).data['grant']
        route=f'sites/{setup["id"]}/'
        response=self.gateway(grant,'builder',{'route':route+'templates/','method':'POST','body':{'name':'Audit template','document':setup['document']}})
        self.assertEqual(response.status_code,200,response.data)
        summary=self.gateway(grant,'builder',{'route':route+'templates/','query':{'summary':'1','q':'Audit'},'method':'GET'})
        self.assertEqual(summary.status_code,200,summary.data)
        self.assertEqual(len(summary.data['templates']),1)
        self.assertNotIn('document',summary.data['templates'][0])
        created=self.gateway(grant,'builder',{'route':route+'reviews/','method':'POST','body':{'expectedVersion':setup['version'],'canComment':False,'lifetimeDays':2}})
        self.assertEqual(created.status_code,200,created.data)
        links=self.gateway(grant,'builder',{'route':route+'reviews/','method':'GET'})
        self.assertEqual(links.status_code,200,links.data)
        identifier=links.data['reviews'][0]['id']
        read=self.gateway(grant,'builder',{'route':route+f'reviews/{identifier}/','method':'GET'})
        self.assertEqual(read.status_code,200,read.data)
        self.assertFalse(read.data['canComment'])
