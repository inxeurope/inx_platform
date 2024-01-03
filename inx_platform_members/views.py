from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.generic.list import ListView
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from .models import User
from .forms import CustomUserCreationForm


def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a success page or any other desired page after successful user creation
            return redirect('index')
    else:
        form = CustomUserCreationForm()

    return render(request, 'authenticate/create_user.html', {'form': form})


def login_user(request):
    if request.method == "POST":
        email = request.POST["login_email"]
        password = request.POST["login_password"]
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, ('You were successfully logged in'))
            # Check if there is a 'next' parameter in the URL
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('index')
        else:
            messages.success(request, ("There was an error loggin in ..."))
            return redirect('login')
    else:
        return render (request, 'authenticate/login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You were logged out"))
    return redirect('index')

class UserListView(ListView):
    model = User
    template_name = "list_users.html"
    context_object_name = "users"

class UserUpdateView(UpdateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'authenticate/edit_user.html'
    success_url = reverse_lazy('list_users')
    