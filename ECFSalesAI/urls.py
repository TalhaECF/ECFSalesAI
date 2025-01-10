from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('ai_app/', include('ai_app.urls')),
    path('copilot/', include('copilot.urls')),
]
