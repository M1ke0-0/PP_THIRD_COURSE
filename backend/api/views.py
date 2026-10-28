from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from attempts import services
from attempts.models import Attempt
from attempts.security import is_kiosk_request
from testing.models import Test

from .permissions import IsStudent
from .serializers import AnswerInputSerializer, AttemptSerializer, EventInputSerializer, TestSerializer


class TestViewSet(viewsets.ReadOnlyModelViewSet):
    """Тесты, доступные студенту: опубликованные и назначенные его группе."""

    serializer_class = TestSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return Test.objects.available_for(self.request.user).select_related('teacher')

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        attempt, created = services.start_attempt(
            self.get_object(), request.user, from_kiosk=is_kiosk_request(request)
        )
        return Response(
            AttemptSerializer(attempt).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class AttemptViewSet(viewsets.GenericViewSet):
    serializer_class = AttemptSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        # Чужая попытка не найдётся — студент получит 404, а не чужие данные.
        return Attempt.objects.filter(student=self.request.user).select_related('test')

    def get_object(self):
        attempt = super().get_object()
        services.expire_if_overdue(attempt)
        return attempt

    def retrieve(self, request, pk=None):
        return Response(AttemptSerializer(self.get_object()).data)

    @action(detail=True, methods=['post'], serializer_class=AnswerInputSerializer)
    def answer(self, request, pk=None):
        data = self._validated(AnswerInputSerializer)
        services.save_answer(
            self.get_object(), data['question'], data['options'], from_kiosk=is_kiosk_request(request)
        )
        return Response({'detail': 'Ответ сохранён.'})

    @action(detail=True, methods=['post'], serializer_class=None)
    def finish(self, request, pk=None):
        attempt = services.finish_by_student(self.get_object(), from_kiosk=is_kiosk_request(request))
        return Response(AttemptSerializer(attempt).data)

    @action(detail=True, methods=['post'], serializer_class=EventInputSerializer)
    def events(self, request, pk=None):
        data = self._validated(EventInputSerializer)
        services.record_client_event(self.get_object(), data['event_type'], data['details'])
        return Response({'detail': 'Событие записано.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='time-left')
    def time_left(self, request, pk=None):
        attempt = self.get_object()
        return Response({'status': attempt.status, 'seconds_left': services.seconds_left(attempt)})

    def _validated(self, serializer_class):
        serializer = serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data
