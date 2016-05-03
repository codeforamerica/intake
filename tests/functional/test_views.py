
from tests.base import FunctionalTestCase


class TestViews(FunctionalTestCase):

    def test_home_view(self):
        self.browser.get(self.live_server_url)
        self.assertIn('Clear My Record', self.browser.title)
    

if __name__ == '__main__':
    unittest.main(warnings='ignore')
