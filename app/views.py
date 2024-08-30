from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse


def index(request):
    context = {"test": "Rodney"}
    return render(request, "app/index.html", context)
