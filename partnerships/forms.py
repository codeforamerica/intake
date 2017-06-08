from django.forms import ModelForm, widgets
from partnerships.models import PartnershipLead


def with_classes(widget_class, *classes, **kwargs):
    attrs = kwargs.get('attrs', {})
    class_ = attrs.get('class', '')
    class_ += ' '.join(classes)
    attrs.update({'class': class_})
    kwargs.update({'attrs': attrs})
    return widget_class(**kwargs)


class PotentialPartnerLeadForm(ModelForm):

    class Meta:
        model = PartnershipLead
        fields = ['name', 'email', 'organization_name', 'message']
        widgets = {
            'email': with_classes(
                widgets.EmailInput, 'text-input', 'form-width--long'),
            'name': with_classes(
                widgets.TextInput, 'text-input', 'form-width--long'),
            'organization_name': with_classes(
                widgets.TextInput, 'text-input', 'form-width--long'),
            'message': with_classes(
                widgets.Textarea, 'textarea')
        }
