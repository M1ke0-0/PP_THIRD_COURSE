from rest_framework.routers import DefaultRouter

from .views import AttemptViewSet, TestViewSet

router = DefaultRouter()
router.register('tests', TestViewSet, basename='test')
router.register('attempts', AttemptViewSet, basename='attempt')

urlpatterns = router.urls
