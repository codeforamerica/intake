from django.db.models import Count
from taggit.models import Tag
from intake.models import SubmissionTagLink, FormSubmission
from intake.exceptions import UserCannotBeNoneError
from intake.serializers import TagSerializer


def update_tags_for_submission(user_id, submission_id, tags_input_string):
    """Updates the set of tags tied to a submission.

        Returns the updated set of tags tag names for the submission
    """
    if not user_id:
        raise UserCannotBeNoneError(
            "Adding tags to a submission requires a user_id")
    tag_names = [
        name.strip().lower()
        for name in tags_input_string.split(',')
        if name.strip().lower()
    ]
    if tag_names:
        existing_tag_objs = Tag.objects.filter(name__in=tag_names)
        existing_tag_names = set(tag.name for tag in existing_tag_objs)
        new_tags = [
            Tag(name=tag_name) for tag_name in tag_names
            if tag_name not in existing_tag_names]
        for tag in new_tags:
            tag.save()
        tag_objs = [*existing_tag_objs, *new_tags]
        existing_through_models = SubmissionTagLink.objects.filter(
            content_object_id=submission_id,
            tag__name__in=existing_tag_names)
        existing_through_tag_ids = set(
            through.tag_id for through in existing_through_models)
        new_through_models = (
            SubmissionTagLink(
                content_object_id=submission_id,
                tag_id=tag.id,
                user_id=user_id) for tag in tag_objs
            if tag.id not in existing_through_tag_ids)
        SubmissionTagLink.objects.bulk_create(new_through_models)
    tags_for_submission = FormSubmission.objects.get(
        id=submission_id).tags.all()
    return TagSerializer(tags_for_submission, many=True).data


def get_all_used_tag_names():
    """Returns any tag names that are linked to form submissions
    """
    return Tag.objects.annotate(
            link_count=Count('intake_submissiontaglink_items')
        ).filter(link_count__gt=0).values_list('name', flat=True)


def remove_tag_from_submission(tag_id, submission_id):
    """Deletes links to tags based on user_id and submission_id

        returns the deletion result as a tuple:
            (int(total_deletions), dict(deletion_counts_by_model))
    """
    return SubmissionTagLink.objects.filter(
            tag_id=tag_id, content_object_id=submission_id).delete()
