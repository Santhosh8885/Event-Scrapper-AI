from django.urls import path
from .views import SaveEntityView

urlpatterns = [
    path('api/save-entity',SaveEntityView.as_view(), name='save-entity')
]