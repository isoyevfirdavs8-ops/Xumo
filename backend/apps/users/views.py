from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import Throttled
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from .services import (
    is_account_locked,
    record_failed_login,
    clear_failed_logins,
)
from .throttles import LoginThrottle, RegisterThrottle


from .serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileUpdateSerializer,
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterThrottle]



class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ProfileUpdateSerializer
        return UserSerializer


class LoginView(TokenObtainPairView):
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get("phone_number", "")

        if not isinstance(phone_number, str):
            return Response(
                {"detail": "Telefon raqami noto'g'ri."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        phone_number = phone_number.strip()

        if is_account_locked(phone_number):
            raise Throttled(
                wait=900,
                detail="Juda ko'p noto'g'ri urinish. Keyinroq qayta urinib ko'ring.",
            )

        try:
            response = super().post(request, *args, **kwargs)


        except (AuthenticationFailed, InvalidToken):

            record_failed_login(phone_number)

            raise

            if isinstance(exc, AuthenticationFailed):
                record_failed_login(phone_number)

            raise

        if response.status_code == 200:
            clear_failed_logins(phone_number)

        return response

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token majburiy."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)

            if str(token["user_id"]) != str(request.user.pk):
                return Response(
                    {"detail": "Token foydalanuvchiga tegishli emas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token.blacklist()

        except Exception:
            return Response(
                {"detail": "Refresh token noto'g'ri yoki eskirgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)