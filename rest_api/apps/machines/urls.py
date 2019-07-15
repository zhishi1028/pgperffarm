from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter
from machines import views

router = DefaultRouter()
router.register(r'machines', views.MachineViewSet)
 
urlpatterns = [
	url(r'^', include(router.urls))
]