from behave import then


@then('I need to debug')
def test_debugging(context):
    print("\n---------------------------------")
    print("HTML in the browser")
    print(context.browser.page_source)
    print("\n---------------------------------")
    import ipdb; ipdb.set_trace()
    assert False