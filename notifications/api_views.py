from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related(
            "booking", "proposal__learning_request", "learning_request"
        )


class NotificationReadAPIView(APIView):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        if notification.read_at is None:
            notification.read_at = timezone.now()
            notification.save(update_fields=("read_at",))
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllAPIView(APIView):
    def post(self, request):
        Notification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationPreferencesAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        preference, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return preference
