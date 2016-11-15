import json
from django.http import HttpResponseNotFound, HttpResponse, JsonResponse, HttpResponseForbidden
from django.views import View


class JsonView(View):
    def get_json_data(self, **kwargs):
        return {}

    def get(self, request, *args, **kwargs):
        json_data = self.get_json_data(**kwargs)
        json_data = json.dumps(json_data, ensure_ascii=False, indent=4)
        return HttpResponse(json_data, content_type='application/json; charset=utf-8')

    def post(self, request, *args, **kwargs):
        json_data = self.get_json_data(**kwargs)
        json_data = json.dumps(json_data, ensure_ascii=False, indent=4)
        return HttpResponse(json_data, content_type='application/json; charset=utf-8')


class PaginateMixin(object):
    model = None
    queryset = None
    data_key = 'data'

    def get_queryset(self, **kwargs):
        if self.queryset:
            return self.queryset
        if self.model:
            return self.model.objects.all()
        raise NotImplementedError('get_queryset must be implemented')

    @staticmethod
    def extract_params(query_dict):
        size = query_dict.get('size', '10')
        page = query_dict.get('page', '1')
        try:
            size, page = int(size), int(page)
        except (TypeError, ValueError):
            size, page = 10, 1
        page = page if page > 0 else 1
        size = size if size >= 0 else 10
        return size, page

    def get_pages_cnt(self, size, **kwargs):
        queryset = self.get_queryset(**kwargs)
        all_cnt = queryset.count()
        if size == 0:
            return 0, all_cnt
        whole_pages = all_cnt // size
        rem_pages = 0 if all_cnt % size == 0 else 1
        return whole_pages + rem_pages, all_cnt

    def get_json_data(self, page, size, all_pages, all_cnt, **kwargs):
        json_data = super(PaginateMixin, self).get_json_data(**kwargs)
        json_data.update({
            'page': page,
            'size': size,
            'all_pages': all_pages,
            'all_cnt': all_cnt
        })
        json_data[self.data_key] = list()
        queryset = self.get_queryset(**kwargs)
        for item in queryset[(page-1)*size:page*size]:
            json_data[self.data_key].append(item.as_dict())
        return json_data

    def get(self, request, *args, **kwargs):
        size, page = self.extract_params(request.GET)
        if size == 0:
            return JsonResponse({})

        all_pages, all_cnt = self.get_pages_cnt(size, **kwargs)
        if page > all_pages:
            return HttpResponseNotFound()
        return super(PaginateMixin, self).get(request, page=page, size=size, all_pages=all_pages, all_cnt=all_cnt,
                                              *args, **kwargs)


class LoginRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if user.is_anonymous():
            return HttpResponseForbidden()
        return super(LoginRequiredMixin, self).dispatch(request, user=user, *args, **kwargs)