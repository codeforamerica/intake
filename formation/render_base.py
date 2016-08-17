from django.template import loader
from django.utils.safestring import mark_safe

class Renderable:
    """A class that implements rendering functionality
        Can be used by forms, fields, or anything else
        that needs to be displayed for a user.
    """
    template_name = ""
    display_template_name = ""

    def __init__(self, default_context=None):
        self.default_context = default_context or {}
        self._template = None
        self._display_template = None
        self.display_only = False

    def render(self, display=False, **extra_context):
        """Uses self and extra_context to render the compiled template
        """
        display = display or self.display_only
        template_attr = "_display_template" if display else "_template"
        if not getattr(self, template_attr):
            self.compile_template(template_attr)
        return mark_safe(getattr(self, template_attr).render(
            self.get_template_context(extra_context)))

    def display(self, **extra_context):
        return self.render(display=True, **extra_context)

    def get_template_context(self, context_dict):
        """Combine `.default_context` with `context_dict` to create
        the final context dictionary for the template
        """
        context = self.default_context
        context.update(context_dict)
        return context

    def compile_template(self, template_attr="_template"):
        """loads templates
        """
        name_attr = template_attr[1:] + "_name"
        setattr(self, template_attr,
            loader.get_template(
                getattr(self, name_attr)
                )
            )

    def __html__(self):
        return self.render()


