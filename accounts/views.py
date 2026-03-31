import random

from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResendVerificationSerializer,
    SignupSerializer,
    UserProfileSerializer,
    VerifyEmailSerializer,
)

VERIFICATION_CODE_TTL_MINUTES = 10

def _generate_code():
    return f"{random.randint(0, 999999):06d}"


def _send_verification_email(user, code):
    subject = "Verify your email"
    message = f"Your verification code is {code}."
    send_mail(subject, message, None, [user.email], fail_silently=True)


def _send_password_reset_email(user, code):
    subject = "Reset your password"
    message = f"Your password reset code is {code}."
    send_mail(subject, message, None, [user.email], fail_silently=True)


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


@csrf_exempt
@extend_schema(request=SignupSerializer)
@api_view(["POST"])
def signup(request):

    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    full_name = serializer.validated_data["full_name"].strip()
    phone = serializer.validated_data.get("phone", "").strip()
    avatar_url = serializer.validated_data.get("avatar_url", "").strip()
    password = serializer.validated_data["password"]

    if User.objects.filter(email=email).exists():
        return Response(
            {"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST
        )

    user = User.objects.create_user(
        email=email,
        password=password,
        full_name=full_name,
        phone=phone,
        avatar_url=avatar_url,
    )
    code = _generate_code()
    user.email_verification_code = code
    user.email_verification_expires_at = timezone.now() + timezone.timedelta(
        minutes=VERIFICATION_CODE_TTL_MINUTES
    )
    user.save(update_fields=["email_verification_code", "email_verification_expires_at"])

    _send_verification_email(user, code)

    return Response(
        {"detail": "Account created. Verification code sent.", "email": user.email}
    )


@csrf_exempt
@extend_schema(request=LoginSerializer)
@api_view(["POST"])
def login_view(request):

    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    password = serializer.validated_data["password"]

    user = authenticate(request, email=email, password=password)
    if not user:
        return Response(
            {"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_email_verified:
        return Response(
            {"detail": "Email not verified."}, status=status.HTTP_403_FORBIDDEN
        )

    login(request, user)
    tokens = _issue_tokens(user)
    return Response({"detail": "Logged in successfully.", **tokens})


@csrf_exempt
@extend_schema(request=VerifyEmailSerializer)
@api_view(["POST"])
def verify_email(request):

    serializer = VerifyEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    code = serializer.validated_data["code"].strip()

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "Invalid email."}, status=status.HTTP_404_NOT_FOUND)

    if user.is_email_verified:
        return Response({"detail": "Email already verified."})

    if user.email_verification_expires_at and timezone.now() > user.email_verification_expires_at:
        return Response(
            {"detail": "Verification code expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if user.email_verification_code != code:
        return Response(
            {"detail": "Invalid verification code."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.is_email_verified = True
    user.email_verification_code = None
    user.email_verification_expires_at = None
    user.save(
        update_fields=[
            "is_email_verified",
            "email_verification_code",
            "email_verification_expires_at",
        ]
    )

    tokens = _issue_tokens(user)
    return Response({"detail": "Email verified successfully.", **tokens})


@csrf_exempt
@extend_schema(request=ResendVerificationSerializer)
@api_view(["POST"])
def resend_verification(request):

    serializer = ResendVerificationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "Invalid email."}, status=status.HTTP_404_NOT_FOUND)

    if user.is_email_verified:
        return Response({"detail": "Email already verified."})

    code = _generate_code()
    user.email_verification_code = code
    user.email_verification_expires_at = timezone.now() + timezone.timedelta(
        minutes=VERIFICATION_CODE_TTL_MINUTES
    )
    user.save(update_fields=["email_verification_code", "email_verification_expires_at"])

    _send_verification_email(user, code)

    return Response({"detail": "Verification code resent."})


@csrf_exempt
@extend_schema(request=PasswordResetRequestSerializer)
@api_view(["POST"])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "Invalid email."}, status=status.HTTP_404_NOT_FOUND)

    code = _generate_code()
    user.password_reset_code = code
    user.password_reset_expires_at = timezone.now() + timezone.timedelta(
        minutes=VERIFICATION_CODE_TTL_MINUTES
    )
    user.save(update_fields=["password_reset_code", "password_reset_expires_at"])
    _send_password_reset_email(user, code)

    return Response({"detail": "Password reset code sent."})


@csrf_exempt
@extend_schema(request=PasswordResetConfirmSerializer)
@api_view(["POST"])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"].strip().lower()
    code = serializer.validated_data["code"].strip()
    new_password = serializer.validated_data["new_password"]

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "Invalid email."}, status=status.HTTP_404_NOT_FOUND)

    if user.password_reset_expires_at and timezone.now() > user.password_reset_expires_at:
        return Response(
            {"detail": "Reset code expired."}, status=status.HTTP_400_BAD_REQUEST
        )

    if user.password_reset_code != code:
        return Response(
            {"detail": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.password_reset_code = None
    user.password_reset_expires_at = None
    user.save(update_fields=["password", "password_reset_code", "password_reset_expires_at"])

    return Response({"detail": "Password updated successfully."})


@extend_schema(request=UserProfileSerializer)
@api_view(["GET", "PUT", "PATCH"])
def me(request):
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == "GET":
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    serializer = UserProfileSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    for field in ["full_name", "phone", "avatar_url"]:
        if field in serializer.validated_data:
            setattr(request.user, field, serializer.validated_data[field])
    request.user.save(update_fields=["full_name", "phone", "avatar_url"])
    return Response(UserProfileSerializer(request.user).data)
