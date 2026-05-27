from django.shortcuts import render, redirect


def main(request):
    return render(request, "app_main/main.html", context={
        "title": "ArchitetIQ",
        "description": "ArchitetIQ description"})

