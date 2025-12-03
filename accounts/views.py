from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import RegisterForm

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("bingo:lobby")  # 👈 antes seguramente era waiting_room
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})
