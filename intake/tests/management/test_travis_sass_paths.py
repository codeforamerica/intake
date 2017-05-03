import subprocess
from django.test import TestCase


class TestTravisSassPaths(TestCase):

    def test_path_to_ruby_executable(self):
        result = subprocess.run(
            ['which', 'ruby'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        print("Ruby path result")
        self.assertEqual('intentional break', output)

    def test_path_to_sass_executable(self):
        result = subprocess.run(
            ['which', 'sass'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        print("Sass path result")
        self.assertEqual('intentional break', output)
