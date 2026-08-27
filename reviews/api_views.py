from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from bookings.models import Booking, Session
from profiles.models import TeacherProfile

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewReplySerializer, ReviewSerializer
from .services import create_review, create_review_response


class PublicTeacherReviewListAPIView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        teacher = get_object_or_404(
            TeacherProfile.objects.filter(is_public=True, user__is_active=True),
            public_id=self.kwargs["teacher_id"],
        )
        return Review.objects.filter(
            subject=teacher.user,
            status=Review.Status.PUBLISHED,
        ).select_related("reviewer", "response")


class ReviewCreateAPIView(generics.GenericAPIView):
    serializer_class = ReviewCreateSerializer

    def post(self, request, booking_id):
        booking = get_object_or_404(
            Booking.objects.filter(Q(learner=request.user) | Q(teacher=request.user)),
            public_id=booking_id,
            status=Booking.Status.COMPLETED,
        )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = create_review(
                session=get_object_or_404(Session, booking=booking),
                reviewer=request.user,
                **serializer.validated_data,
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response(
            ReviewSerializer(review, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class TeacherReviewListAPIView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewSerializer

    def get(self, request, *args, **kwargs):
        if request.user.account_type != "TEACHER":
            raise PermissionDenied("Réservé aux enseignants.")
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if self.request.user.account_type != "TEACHER":
            return Review.objects.none()
        return Review.objects.filter(subject=self.request.user).select_related("reviewer", "response")


class TeacherReputationAPIView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.account_type != "TEACHER":
            raise PermissionDenied("Réservé aux enseignants.")
        snapshot = request.user.teacher_profile.trust_score_snapshots.first()
        if snapshot is None:
            return Response({"overall": 0, "clarity": 0, "pace": 0, "engagement": 0})
        components = snapshot.components
        return Response({
            "overall": snapshot.score,
            "clarity": components.get("reviews", 0),
            "pace": components.get("delivery", 0),
            "engagement": components.get("attendance", 0),
            "components": components,
        })


class ReviewReplyCreateAPIView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewReplySerializer

    def post(self, request, review_id):
        review = get_object_or_404(Review, public_id=review_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reply = create_review_response(
                review=review,
                author=request.user,
                content=serializer.validated_data["message"],
            )
        except DjangoPermissionDenied as error:
            raise PermissionDenied(str(error)) from None
        except DjangoValidationError as error:
            raise ValidationError(error.messages) from None
        return Response({"id": reply.pk, "message": reply.content, "created_at": reply.created_at}, status=201)
