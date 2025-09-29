from django.test import TestCase
from django.urls import reverse

# Create your tests here.
class HelloWorldTestCases(TestCase):
    def test_successful_response(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, "Hello, World!")
