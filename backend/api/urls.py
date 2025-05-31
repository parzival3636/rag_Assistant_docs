



# api/urls.py
from django.urls import path
from .views import DocumentUploadView, list_documents, query

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='upload'),
    path('documents/', list_documents, name='documents'),
    path('query/', query, name='query'),
]