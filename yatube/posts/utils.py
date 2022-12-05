from django.core.paginator import Paginator


def pager_list(request, page_list, VIEW_LIST):
    '''Пейджинатор, то есть постраничное разбиение списка постов'''
    paginator = Paginator(page_list, VIEW_LIST)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
