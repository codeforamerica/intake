from tests import base


class TestWorkflows(base.ScreenSequenceTestCase):
    dimensions = base.SMALL_MOBILE

    def test_application_submission_workflow(self):
        # self.host = 'https://clearmyrecord.codeforamerica.org'
        sequence = [
            '/',
            '/sanfrancisco/',
            '/thanks/',
            ]
        sizes = {
            'Apply on a common mobile phone': base.COMMON_MOBILE,
            'Apply on a small mobile phone': base.SMALL_MOBILE,
            'Apply on a small desktop computer': base.SMALL_DESKTOP
        }
        for prefix, size in sizes.items():
            self.run_sequence(sequence, prefix=prefix, size=size)
