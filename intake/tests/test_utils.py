from unittest import TestCase
from django.core.paginator import Paginator
from intake import utils
from django.test.testcases import _AssertNumQueriesContext
from django.test import RequestFactory


class TestGetPageNavigationCounter(TestCase):

    def run_case(self, full_range, wing_size, pages):
        page_size = 5
        fake_objects = list(range(len(full_range) * page_size))
        paginator = Paginator(fake_objects, page_size)
        for page_number, expected_result in pages.items():
            page = paginator.page(page_number)
            result = utils.get_page_navigation_counter(page, wing_size)
            self.assertEqual(result, expected_result)

    def test_target_situation(self):
        self.run_case(
            full_range=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
            wing_size=4,
            pages={
                1: [1, 2, 3, 4, 5, 6, 7, 'jump', 13],
                2: [1, 2, 3, 4, 5, 6, 7, 'jump', 13],
                3: [1, 2, 3, 4, 5, 6, 7, 'jump', 13],
                4: [1, 2, 3, 4, 5, 6, 7, 'jump', 13],
                5: [1, 2, 3, 4, 5, 6, 7, 'jump', 13],
                6: [1, 'jump', 4, 5, 6, 7, 8, 'jump', 13],
                7: [1, 'jump', 5, 6, 7, 8, 9, 'jump', 13],
                8: [1, 'jump', 6, 7, 8, 9, 10, 'jump', 13],
                9: [1, 'jump', 7, 8, 9, 10, 11, 12, 13],
                10: [1, 'jump', 7, 8, 9, 10, 11, 12, 13],
                11: [1, 'jump', 7, 8, 9, 10, 11, 12, 13],
                12: [1, 'jump', 7, 8, 9, 10, 11, 12, 13],
                13: [1, 'jump', 7, 8, 9, 10, 11, 12, 13]
            }
        )

    def test_even_steven(self):
        self.run_case(
            full_range=[1, 2, 3, 4, 5, 6, 7, 8],
            wing_size=3,
            pages={
                1: [1, 2, 3, 4, 5, 'jump', 8],
                2: [1, 2, 3, 4, 5, 'jump', 8],
                3: [1, 2, 3, 4, 5, 'jump', 8],
                4: [1, 2, 3, 4, 5, 'jump', 8],
                5: [1, 'jump', 4, 5, 6, 7, 8],
                6: [1, 'jump', 4, 5, 6, 7, 8],
                7: [1, 'jump', 4, 5, 6, 7, 8],
                7: [1, 'jump', 4, 5, 6, 7, 8]
            }
        )

    def test_not_long_enough(self):
        self.run_case(
            full_range=[1, 2, 3, 4, 5, 6, 7],
            wing_size=0,
            pages={
                1: [1, 2, 3, 4, 5, 6, 7],
                2: [1, 2, 3, 4, 5, 6, 7],
                3: [1, 2, 3, 4, 5, 6, 7],
                4: [1, 2, 3, 4, 5, 6, 7],
                5: [1, 2, 3, 4, 5, 6, 7],
                6: [1, 2, 3, 4, 5, 6, 7],
                7: [1, 2, 3, 4, 5, 6, 7],
            }
        )


class AssertNumQueriesLessThanContext(_AssertNumQueriesContext):

    def __exit__(self, exc_type, exc_value, traceback):
        super(_AssertNumQueriesContext, self).__exit__(
            exc_type, exc_value, traceback)
        if exc_type is not None:
            return
        executed = len(self)
        self.test_case.assertLessEqual(
            executed, self.num,
            "%d queries executed, %d expected\nCaptured queries were:\n%s" % (
                executed, self.num,
                '\n'.join(
                    query['sql'] for query in self.captured_queries
                )
            )
        )


class TestGetFormDataFromSession(TestCase):

    def test_get_old_formatted_form_data_from_session(self):
        old_session_data = {
            'counties': ['alameda', 'contracosta'],
            'confirm_county_selection': 'yes'}
        request = RequestFactory().get('/apply')
        request.session = {'form_in_progress': old_session_data}
        # store this @ session key before calling get_form_data_from_session
        fetched = utils.get_form_data_from_session(
            request, 'form_in_progress')
        self.assertEqual(fetched['confirm_county_selection'], 'yes')
        self.assertEqual(
            fetched.getlist('counties'), ['alameda', 'contracosta'])
