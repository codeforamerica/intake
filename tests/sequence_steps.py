

def get(sequence_step_name, url):
    return (sequence_step_name, 'get', [url], {})

def click_on(sequence_step_name, text):
    return (sequence_step_name, 'click_on', [text], {})

def fill_form(sequence_step_name, **answers):
    return (sequence_step_name, 'fill_form', [], answers)

def check_email(sequence_step_name):
    return (sequence_step_name, 'print_email', [], {})