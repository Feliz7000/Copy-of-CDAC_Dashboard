from django.urls import path
from .views import EmbedConfigView

urlpatterns = [
    path('embed-config/', EmbedConfigView.as_view(), name='powerbi_embed_config'),
]
