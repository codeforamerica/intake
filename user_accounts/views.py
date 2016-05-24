from django.shortcuts import redirect
from allauth.account.views import SignupView

class CustomSignupView(SignupView):

    def closed(self):
        return redirect('intake-home')