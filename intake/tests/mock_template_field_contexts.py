
def status_notification_context(**kwargs):
    context = dict(
        organization_contact_info=str(
            'call (559) 600-3546 or email publicdefender@co.yolo.ca.us'),
        county='Yolo County',
        personal_statement_link=str(
            'https://clearmyrecord.codeforamerica.org/personal-statement/'),
        letters_of_rec_link=str(
            'https://clearmyrecord.codeforamerica.org/letters-of-rec/')
    )
    org = kwargs.get('organization', None)
    county = kwargs.get('county', None)
    if org:
        context.update(
            organization_contact_info=org.get_contact_info_message())
    if county:
        context.update(
            county=county.name + " County")
    return context
