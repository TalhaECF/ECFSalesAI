from django.urls import path
from .views import (UploadFileToSharePointView, OAuthRedirectView, WBSDocumentView,
                    DiscoveryQuestionnaireView, InitialFormResponseView)

urlpatterns = [
    path('upload-file/', UploadFileToSharePointView.as_view(), name='upload_file'),
    path('redirect/', OAuthRedirectView.as_view(), name='oauth_redirect'),
    path('discovery/<str:project_id>/', DiscoveryQuestionnaireView.as_view(), name='discovery_questionnaire'),
    path('wbs/<str:project_id>/', WBSDocumentView.as_view(), name='wbs_document'),
    path('form_response/<str:project_id>/', InitialFormResponseView.as_view(), name='initial_form_with_transcript')
]
