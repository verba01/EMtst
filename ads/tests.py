from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from .models import Ad


class AuthTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='sanya',
            password='verbup9090'
        )

        self.login_url = reverse('user-login')
        self.logout_url = reverse('user-logout')
        self.ads_url = reverse('ad-list')

        self.ad = Ad.objects.create(
            user=self.user1,
            title='Test Ad',
            description='Test Description',
            category='electronics',
            condition='new'
        )

    def test_successful_login(self):
        """Тест успешного входа в систему"""
        data = {'username': 'sanya', 'password': 'verbup9090'}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = Token.objects.get(user=self.user1)
        self.assertEqual(response.data['token'], token.key)

    def test_failed_login(self):
        """Тест неудачного входа"""
        data = {'username': 'sanya', 'password': 'wrongpassword'}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid credentials')

    def test_successful_logout(self):
        """Тест успешного выхода из системы"""
        token = Token.objects.create(user=self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Successfully logged out.')

        with self.assertRaises(Token.DoesNotExist):
            Token.objects.get(user=self.user1)

    def test_logout_invalid_credentials(self):
        """Тест выхода с неверными учетными данными"""
        token = Token.objects.create(user=self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.post(self.logout_url, {'invalid': 'data'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertRaises(Token.DoesNotExist):
            Token.objects.get(user=self.user1)

    def test_logout_unauthenticated(self):
        """Тест выхода без авторизации"""
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_invalid_after_logout(self):
        """Проверка, что токен не работает после выхода"""
        token = Token.objects.create(user=self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        self.client.post(self.logout_url)
        response = self.client.get(self.ads_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_session_logout(self):
        """Тест стандартного Django logout (для Swagger UI)"""
        self.client.force_login(self.user1)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_token_auto_generation_on_login(self):
        """Тест автоматического создания токена при входе"""
        Token.objects.filter(user=self.user1).delete()
        data = {'username': 'sanya', 'password': 'verbup9090'}
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Token.objects.filter(user=self.user1).exists())