from django.shortcuts import render, redirect


def main(request):
    return render(request, "app_main/index.html", context={
        "title": "ArchitetIQ",
        "description": "ArchitetIQ description"})

