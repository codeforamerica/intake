def serialize_page(page, serializer, many=True):
    page.object_list = serializer(page.object_list, many=many).data
    return page
