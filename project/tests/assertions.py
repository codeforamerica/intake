from bs4 import BeautifulSoup


def assertInLogs(logging_context_manager, *log_strings):
    """
    asserts that each log_strings is present in at least one of the records in
        logging_context_manager.output
    """
    found = set()
    for search_term in log_strings:
        for record in logging_context_manager.output:
            if search_term in record:
                found.add(search_term)
                break
    unfound = set(log_strings) - found
    if unfound:
        raise AssertionError(
            "{} not found in log output".format(list(unfound)))


def assertInLogsCount(logging_context_manager, log_string_counts):
    """
    For each key=count pair, asserts that that number of log events
    are present in
        logging_context_manager.output
    """
    differences = []
    for search_term, expected in log_string_counts.items():
        count = 0
        for record in logging_context_manager.output:
            if search_term in record:
                count += 1
        if count != expected:
            message = "'{}': expected {} but found {}".format(
                search_term, expected, count)
            differences.append(message)
    if differences:
        raise AssertionError(
            "Unexpected string counts in logs: {}".format(
                '.'.join(differences)))


def assertInputHasValue(response, input_name, expected_value, msg=None):
    no_element_message = 'input[name="{}"] was not found in {}'.format(
        input_name, response.rendered_content)
    soup = BeautifulSoup(response.rendered_content)
    element = soup.find('input', {'name': input_name})
    if not element:
        raise ValueError(no_element_message)
    value = element['value']
    if not msg:
        msg = 'value of "{}" input was "{}", not "{}"'.format(
            input_name, value, expected_value)
    if expected_value != value:
        raise AssertionError(msg)
