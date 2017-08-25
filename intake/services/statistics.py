"""
This module handles queries to retrieve common statistics
"""
from datetime import datetime, timedelta
from intake import models, constants, utils
from user_accounts.models import Organization
from django.db.models.aggregates import Count
from django.db.models.functions import ExtractYear
from django.db.models.functions import Extract
from django.db.models import DateTimeField
from pytz import timezone


@DateTimeField.register_lookup
class ExtractWeek(Extract):
    lookup_name = 'week'


TOTAL = 'Total'
ALL = (constants.Organizations.ALL, 'Total (All Organizations)')


def make_year_weeks():
    start_date = utils.get_start_date()
    year_weeks = []
    date_cursor = start_date
    last_date = utils.get_todays_date()
    while date_cursor <= last_date:
        year_week = as_year_week(date_cursor)
        year_weeks.append(year_week)
        date_cursor += timedelta(days=7)
    return year_weeks


def as_year_week(dt):
    return dt.strftime('%Y-%W-1')


def get_org_data_dict():
    """
    Generates a data dictionary for displaying both total and
    organization-specific statistics.

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
      },
    ]

    :return: list of data dicts including one for aggregate totals and one for
    each organization we serve.
    """

    # Figure out all the weeks of the year since we started
    year_weeks = make_year_weeks()

    # Get all the organizations receiving applications
    orgs = list(Organization.objects.filter(
        is_receiving_agency=True, is_live=True
    ).values('name', 'slug', 'id').order_by('name'))

    # Get overall counts of applications by weeks of the year
    total_app_data = models.Application.objects.annotate(
        wk=ExtractWeek('form_submission__date_received',
                       tzinfo=timezone('US/Pacific')),
        yr=ExtractYear('form_submission__date_received',
                       tzinfo=timezone('US/Pacific'))
    ).values('yr', 'wk').annotate(
        fs_count=Count('form_submission_id', distinct=True)
    ).values('yr', 'wk', 'fs_count').order_by('yr', 'wk')

    # Convert the db results to a dict keyed by the week of the year in
    # datetime format. The '-1' at the end indicates weeks starting on Mondays.
    total_app_data_by_week = {
        '%d-%d-1' % (row['yr'], row['wk']): row['fs_count'] for row in
        total_app_data}

    # Transform the totals data into something formatted for charting purposes
    # with the grand total and weekly time-series data and add it to the
    # results we will return for display.
    display_data = [total_display_data(total_app_data_by_week, year_weeks)]

    # Get counts of applications by organization and week of year
    org_app_data = models.Application.objects.annotate(
        wk=ExtractWeek('form_submission__date_received',
                       tzinfo=timezone('US/Pacific')),
        yr=ExtractYear('form_submission__date_received',
                       tzinfo=timezone('US/Pacific'))
    ).values('organization_id', 'yr', 'wk').annotate(
        fs_count=Count('form_submission_id')
    ).values('organization_id', 'yr', 'wk', 'fs_count').order_by('yr', 'wk')

    # Convert the db results to a dict of dicts keyed by org_id and week of the
    # year in datetime format. The '-1' at the end indicates weeks starting on
    # Mondays.
    org_app_data_by_week = {}
    for row in org_app_data:
        current_org_app_data_by_week = org_app_data_by_week.setdefault(
            row['organization_id'], {})
        current_org_app_data_by_week['%d-%d-1' % (row['yr'], row['wk'])] = row[
            'fs_count']

    # Transform the org-specific data into something formatted for charting
    # purposes with the grand total and weekly time-series data and add it to
    # the results we will return for display.
    display_data_by_org = orgs_display_data(org_app_data_by_week, orgs,
                                            year_weeks)
    display_data += display_data_by_org

    return display_data


def orgs_display_data(org_app_data_by_week, orgs, year_weeks):
    """
    Generate a list of dictionaries of data suitable for our view to render
    stats for each individual organization which receives applications. Each
    dictionary includes metadata about the organization whose stats are being
    displayed, a cumulative total of applications, a count of applications for
    the current and previous weeks, and time-series data representing
    applications for each week since launch.

    :param org_app_data_by_week: dict of dicts data structured as
    {organization_id: {%Y-%W-%w: count}}
    :param orgs: list of all organizations.
    :param year_weeks: list of year-weeks to generate display data for, in the
    format %Y-%W-%w.
    :return: dict of data suitable for rendering statistics.
    """

    # Iterate over each organization, calculate its overall total plus a weekly
    # time-series data-set for charting
    org_data = []
    org_totals = {}
    org_weekly_totals = {}

    for org in orgs:
        org_id = org['id']
        current_org_app_data_by_week = org_app_data_by_week.get(org_id, None)
        if current_org_app_data_by_week is None:
            continue

        # Iterate over each week of the year for the current organization
        for year_week in year_weeks:
            # Get the actual start date for the week
            date = datetime.strptime(year_week, "%Y-%W-%w")

            # Add the counts if we have a data point for the week, otherwise 0
            org_apps = current_org_app_data_by_week.get(year_week, None)
            if org_apps is not None:
                current_org_total = org_totals.setdefault(org_id, 0)
                org_totals[org_id] = current_org_total + org_apps

                current_org_weekly_totals = org_weekly_totals.setdefault(
                    org_id, [])
                current_org_weekly_totals.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': org_apps
                })
            else:
                current_org_weekly_totals = org_weekly_totals.setdefault(
                    org_id, [])
                current_org_weekly_totals.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'count': 0
                })

        # Add the data for this org formatted for display
        org_data.append({
            'org': org,
            'total': org_totals[org_id],
            'weekly_totals': org_weekly_totals[org_id],
            'apps_this_week': org_weekly_totals[org_id][-1]['count'] if len(
                org_weekly_totals[org_id]) > 0 else 0,
            'apps_last_week': org_weekly_totals[org_id][-2]['count'] if len(
                org_weekly_totals[org_id]) > 1 else 0,
        })

    return org_data


def total_display_data(total_app_data_by_week, year_weeks):
    """
    Generate a dictionary of data suitable for our view to render total stats
    across all organizations that receive applications. It includes metadata
    about the organization whose stats are being displayed, a cumulative total
    of applications, a count of applications for the current and previous
    weeks, and time-series data representing applications for each week since
    launch.

    :param total_app_data_by_week: dict of data where the key is week of the
    year and the value is the count of applications submitted that week
    :param year_weeks: list of year-weeks to generate display data for, in the
    format %Y-%W-%w.
    :return: dict of data suitable for rendering statistics.
    """

    # Iterate over the weekly data, calculate the overall total plus a weekly
    # time-series data-set for charting
    total_count = 0
    weekly_totals = []
    for year_week in year_weeks:
        # Get the actual start date for the week
        date = datetime.strptime(year_week, "%Y-%W-%w")

        # Add the counts if we have a data point for the week, otherwise add 0
        total_apps = total_app_data_by_week.get(year_week, None)
        if total_apps is not None:
            total_count += total_apps
            weekly_totals.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': total_apps
            })
        else:
            weekly_totals.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': 0
            })

    # Return the total data formatted for display
    return {
        'org': {'name': 'Total (All Organizations)', 'slug': 'all'},
        'total': total_count,
        'apps_this_week': weekly_totals[-1]['count'] if len(
            weekly_totals) > 0 else 0,
        'apps_last_week': weekly_totals[-2]['count'] if len(
            weekly_totals) > 1 else 0,
        'weekly_totals': weekly_totals
    }
