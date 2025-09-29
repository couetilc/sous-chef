from django.test import TestCase
from django.urls import reverse

# Create your tests here.
class HelloWorldTestCases(TestCase):
    def test_successful_response(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, "Hello, World!")

class HealthCheckTestCases(TestCase):
    def test_successful_response(self):
        response = self.client.get(reverse('health_check'))
        self.assertContains(response, "status")
        self.assertContains(response, "current_time")
        self.assertContains(response, "uptime")
