from rest_framework.routers import SimpleRouter

from apps.learning.views import (
    ChapterViewSet,
    DomainViewSet,
    SubjectViewSet,
    TopicViewSet,
)

router = SimpleRouter()
router.register("domains", DomainViewSet, basename="domain")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("chapters", ChapterViewSet, basename="chapter")
router.register("topics", TopicViewSet, basename="topic")

urlpatterns = router.urls
