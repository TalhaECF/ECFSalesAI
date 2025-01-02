from django.urls import path
from .views import (UploadFileToSharePointView, OAuthRedirectView, WBSDocumentView,
                    DiscoveryQuestionnaireView, InitialFormResponseView, DiscoveryQuestionnaireAPIView,
                    PromptResponseAPIView, SharePointFileParserView)

urlpatterns = [
    path('upload-file/', UploadFileToSharePointView.as_view(), name='upload_file'),
    path('redirect/', OAuthRedirectView.as_view(), name='oauth_redirect'),
    path('discovery/', DiscoveryQuestionnaireView.as_view(), name='simple_discovery_questionnaire'),
    path('wbs/', WBSDocumentView.as_view(), name='wbs_document'),
    path('form_response/<str:project_id>/', InitialFormResponseView.as_view(), name='initial_form_with_transcript'),
    path("new_discovery_questionnaire/", DiscoveryQuestionnaireAPIView.as_view(), name="discovery-questionnaire"),
    path('prompt_response/', PromptResponseAPIView.as_view(), name='co-pilot-action'),
    path('taxonomy_json/', SharePointFileParserView.as_view(), name='taxonomy-parser-json'),
]
