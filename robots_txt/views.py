from django.http import HttpResponse


def robots_view(allow):
    allow_txt = '\n'.join(['Allow: %s' % d for d in allow])
    robots_txt = "User-agent: *\n%s\nDisallow:/" % (allow_txt)
    return lambda r: HttpResponse(robots_txt, content_type='text/plain')
