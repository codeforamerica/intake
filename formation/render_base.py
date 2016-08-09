from django.template import loader

class Renderable:
    """A class that implements rendering functionality
        Can be used by forms, fields, or anything else
        that needs to be displayed for a user.
    """
    template_name = ""

    def __init__(self, default_context=None):
        self.default_context = default_context or {}
        self._template = None

    def render(self, **extra_context):
        """Uses self and extra_context to render the compiled template
        """
        if not self._template:
            self.compile_template()
        return self._template.render(
            self.get_template_context(extra_context))

    def get_template_context(self, context_dict):
        """Combine `.default_context` with `context_dict` to create
        the final context dictionary for the template
        """
        context = self.default_context
        context.update(context_dict)
        return context

    def compile_template(self):
        """loads templates
        """
        self._template = loader.get_template(self.template_name)