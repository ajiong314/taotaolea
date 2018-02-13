from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
# Create your views here.


class RegisterView(View):

    def get(self,request):

        return render(request, 'register.html')

    def post(self,request):

        return HttpResponse('ceshi')

# def register(request):
#
#     # return HttpResponse('cs')
#
#     if request.method == 'GET':
#         return render(request, 'register.html')
#
#     if request.method == 'POST':
#
#         return HttpResponse('chuliqingqiu')
