"""
This module handles queries to retrieve common statistics
"""
from datetime import datetime, timedelta
from collections import Counter
from intake import models, constants, utils
from user_accounts.models import Organization


TOTAL = 'Total'
ALL = (constants.Organizations.ALL, 'Total (All Organizations)')


def make_year_weeks():
    start_date = utils.get_start_date()
    year_weeks = []
    date_cursor = start_date
    last_date = utils.get_todays_date()
    year_week = as_year_week(date_cursor)
    while date_cursor <= last_date:
        year_week = as_year_week(date_cursor)
        row = (year_week, date_cursor, from_year_week(year_week))
        year_weeks.append(row)
        date_cursor += timedelta(days=7)
    return year_weeks


def from_year_week(year_week_string):
    return datetime.strptime(year_week_string, '%Y-%W-%w').date()


def as_year_week(dt):
    return dt.strftime('%Y-%W-1')


def get_app_dates_sub_ids_org_ids():
    return models.Application.objects.values_list(
        'form_submission__date_received', 'form_submission_id',
        'organization_id'
    ).order_by('-form_submission__date_received')


def rollup_subs(app_dates_sub_ids_org_ids):
    """Reduces results down to unique sub & datetime pairs
    """
    return set(
        (row[0], row[1])
        for row in app_dates_sub_ids_org_ids)


def counts_by_week(datetimes):
    return Counter(
        as_year_week(dt.astimezone(constants.PACIFIC_TIME))
        for dt in datetimes)


def make_weekly_totals(week_counter, year_weeks):
    return sorted([
        {
            'date': row[1].strftime('%Y-%m-%d'),
            'count': week_counter[row[0]]
        }
        for row in year_weeks
    ], key=lambda d: d['date'])


def get_org_data_dict():
    """
    [
      {
        'org': {
            'name': 'Total (All Organizations)'.
            'slug': 'all'
        },
        'total': 1501,
        'apps_this_week': 33,
        'weekly_totals': [
            {'date': '2016-04-24', 'count': 0}
        ]
      }
    ]
    """
    year_weeks = make_year_weeks()
    orgs = list(
        Organization.objects.filter(
            is_receiving_agency=True, is_live=True).values(
                'name', 'slug', 'id').order_by('name'))
    app_data = get_app_dates_sub_ids_org_ids()
    week_counter = counts_by_week(
        row[0] for row in rollup_subs(app_data))
    weekly_totals = make_weekly_totals(week_counter, year_weeks)
    org_data = [{
        'org': {'name': 'Total (All Organizations)', 'slug': 'all'},
        'total': models.FormSubmission.objects.count(),
        'apps_this_week': weekly_totals[-1]['count'],
        'apps_last_week': weekly_totals[-2]['count'],
        'weekly_totals': weekly_totals
    }]
    for org in orgs:
        org_datum = {'org': org}
        week_counter = counts_by_week(
            row[0] for row in app_data
            if row[2] == org['id'])
        org_datum['weekly_totals'] = make_weekly_totals(
            week_counter, year_weeks)
        org_datum['total'] = sum(week_counter.values())
        org_datum['apps_this_week'] = org_datum['weekly_totals'][-1]['count']
        org_datum['apps_last_week'] = org_datum['weekly_totals'][-2]['count']
        org_data.append(org_datum)
    return org_data
