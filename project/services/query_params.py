from django.urls import reverse
from ..exceptions import InvalidQueryParamsError


def get_ids_from_query_params(request, key='ids', sep=','):
    string_value = request.GET.get(key, '')
    str_ids = string_value.split(sep)
    try:
        ids = [int(str_id) for str_id in str_ids]
    except ValueError as err:
        raise InvalidQueryParamsError(
            "Received invalid query params: {url}".format(
                url=request.get_full_path()))
    return ids


def get_url_for_ids(view_name, ids, key='ids'):
    url = reverse(view_name)
    params = '?' + key + '=' + ','.join(sorted([str(i) for i in ids]))
    return url + params
