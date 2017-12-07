import logging
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from clips.models import Clip

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClipCreateView(CreateView):
    model = Clip
    fields = ['title', 'query', ]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.has_perm('clips.add_clip'):
            return HttpResponseForbidden()
        return super(ClipCreateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ClipCreateView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['clips'] = Clip.objects.all().order_by('title')
        return context


class ClipUpdateView(UpdateView):
    model = Clip
    fields = ['title', 'query', ]
    template_name_suffix = '_update_form'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.has_perm('clips.change_clip'):
            return HttpResponseForbidden()
        return super(ClipUpdateView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ClipUpdateView, self).get_context_data(**kwargs)
        logger.info('%s (pk=%d) ran this query %s' % (
            self.request.user.username,
            self.request.user.pk,
            self.object.query,
        ))
        return context


class ClipDeleteView(DeleteView):
    model = Clip

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.has_perm('clips.delete_clip'):
            return HttpResponseForbidden()
        return super(ClipDeleteView, self).dispatch(*args, **kwargs)
