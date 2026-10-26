from django.urls import path

from .views import (
    InternalDomainAuthorizationView, PagePreviewTokenView, PagePublishView, PageRevisionListView,
    PublicHostManifestView, PublicPagePreviewView, PublicRobotsView, PublicSitemapView, PublicSiteManifestView,
    CommerceTemplateView, SiteDetailView, SiteDomainListCreateView, SiteDomainVerifyView, SitePageDetailView, SitePageListCreateView,
)

urlpatterns = [
    path("businesses/<uuid:public_id>/site/", SiteDetailView.as_view()),
    path("businesses/<uuid:public_id>/site/templates/commerce/", CommerceTemplateView.as_view()),
    path("businesses/<uuid:public_id>/site/pages/", SitePageListCreateView.as_view()),
    path("businesses/<uuid:public_id>/site/pages/<uuid:page_id>/", SitePageDetailView.as_view()),
    path("businesses/<uuid:public_id>/site/pages/<uuid:page_id>/revisions/", PageRevisionListView.as_view()),
    path("businesses/<uuid:public_id>/site/pages/<uuid:page_id>/publish/", PagePublishView.as_view()),
    path("businesses/<uuid:public_id>/site/pages/<uuid:page_id>/preview/", PagePreviewTokenView.as_view()),
    path("businesses/<uuid:public_id>/site/domains/", SiteDomainListCreateView.as_view()),
    path("businesses/<uuid:public_id>/site/domains/<uuid:domain_id>/verify/", SiteDomainVerifyView.as_view()),
    path("public/<slug:slug>/site/", PublicSiteManifestView.as_view()),
    path("public/<slug:slug>/site/<slug:page_slug>/", PublicSiteManifestView.as_view()),
    path("public/site-preview/", PublicPagePreviewView.as_view()),
    path("public/site/resolve/", PublicHostManifestView.as_view()),
    path("public/site/sitemap.xml", PublicSitemapView.as_view()),
    path("public/site/robots.txt", PublicRobotsView.as_view()),
    path("internal/domains/authorize/", InternalDomainAuthorizationView.as_view()),
]

from .builder_bridge import BuilderWorkspaceView
urlpatterns.append(path("businesses/<uuid:public_id>/website-builder/", BuilderWorkspaceView.as_view()))
from .studio_bridge import HandoffView, exchange, gateway
urlpatterns += [path('businesses/<uuid:public_id>/studio/handoffs/', HandoffView.as_view()), path('studio-bridge/exchange/', exchange), path('studio-bridge/gateway/', gateway)]
