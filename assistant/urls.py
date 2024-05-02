from django.urls import include, path
from rest_framework import routers

from assistant.assistant_app import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('hello/', views.HelloApiView.as_view(), name="test"),
    path('init-assistant/', views.InitAssistant.as_view(), name="init_assistant"),
    path('ask-anything/', views.AskAnything.as_view(), name="ask_anything"),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]