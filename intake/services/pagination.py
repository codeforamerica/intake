from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_page(qset, page_index, max_count_per_page=25, min_count_per_page=5):
    paginator = Paginator(
        qset, max_count_per_page, orphans=min_count_per_page)
    try:
        return paginator.page(page_index)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        if int(page_index) <= 0:
            return paginator.page(1)
        else:
            return paginator.page(paginator.num_pages)


def get_serialized_page(qset, serializer, page_index, **kwargs):
    page = get_page(qset, page_index, **kwargs)
    page.object_list = serializer(page.object_list, many=True).data
    return page
