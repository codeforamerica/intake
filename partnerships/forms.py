from django.forms import ModelForm, widgets
from partnerships.models import PotentialPartnerLead


class PotentialPartnerLeadForm(ModelForm):

    class Meta:
        model = PotentialPartnerLead
        fields = ['name', 'email', 'organization_name', 'message']
        widgets = {
            'name': widgets.TextInput(),
            'organization_name': widgets.TextInput(),
        }
