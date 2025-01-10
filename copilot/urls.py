from django.urls import path
from .views import CopilotAgentChatAPIView


urlpatterns = [
    path('agent_chat/', CopilotAgentChatAPIView.as_view(), name='copilot'),
    ]
