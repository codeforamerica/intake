from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.utils import IntegrityError
from intake.exceptions import UserCannotBeNoneError

import intake.services.tags as TagsService


def parse_tag_post_data(data):
    submission_id = data.get('submission', None)
    tags_text = data.get('tags', '')
    if submission_id:
        submission_id = int(submission_id)
    return submission_id, tags_text


class TagAPIViewBase(APIView):
    permission_classes = [IsAdminUser]


class AddTags(TagAPIViewBase):

    def post(self, request):
        try:
            submission_id, tags_text = parse_tag_post_data(request.POST)
        except ValueError:
            return Response(status=400)
        if not isinstance(submission_id, int):
            return Response(status=400)
        try:
            updated_tags = TagsService.update_tags_for_submission(
                request.user.id, submission_id, tags_text)
        except IntegrityError:
            return Response(status=400)
        except UserCannotBeNoneError:
            return Response(status=403)
        return Response(data=updated_tags, status=201)


class RemoveTag(TagAPIViewBase):

    def post(self, request, tag_id, submission_id):
        submission_id = int(submission_id)
        tag_id = int(tag_id)
        count, details = TagsService.remove_tag_from_submission(
            tag_id, submission_id)
        if not count:
            # bad input
            return Response(status=400)
        return Response(status=204)


add_tags = AddTags.as_view()
remove_tag = RemoveTag.as_view()
