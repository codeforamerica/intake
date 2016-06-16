

def get(url):
    return ('get', [url], {})

def click_on(text):
    return ('click_on', [text], {})

def fill_form(**answers):
    return ('fill_form', [], answers)