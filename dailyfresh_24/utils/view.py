from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from functools import wraps
from django.db import transaction


class LoginRequiredMixin(object):

    @classmethod
    def as_view(cls, **initkwargs):

        view = super().as_view(**initkwargs)
        return login_required(view)




def login_json_required(view_fun):
    @wraps(view_fun)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated():
            return JsonResponse({'code':1, 'message':'用户未登录'})
        else:

            return view_fun()

    return wrapper


class LoginRequireJSONdMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_json_required(view)
