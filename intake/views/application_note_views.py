from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from intake import models, serializers
import intake.services.events_service as EventsService


class NoteViewMixin:
    queryset = models.ApplicationNote.objects.all()
    serializer_class = serializers.ApplicationNoteSerializer
    permission_classes = (IsAdminUser,)


class CreateNote(NoteViewMixin, generics.CreateAPIView):
    """Returns 201 if a note is successfully created
    """
    def perform_create(self, serializer):
        note = serializer.save()
        EventsService.note_added(self, note.submission)


class DestroyNote(NoteViewMixin, generics.DestroyAPIView):
    """Returns 204 if a note is successfully destroyed
    """

    def post(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


create_note = CreateNote.as_view()
destroy_note = DestroyNote.as_view()
