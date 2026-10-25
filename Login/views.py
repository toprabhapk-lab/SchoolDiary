



from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.http import HttpResponse

from Admin_Principal.models import Role_Model, Notice_model


def SchoolDiaryHeaderView(request):
    return render(request,"SchoolDiaryHeader.html")

def SchoolDiaryReadmoreView(request):
    return render(request,"SchoolDiaryReadmore.html")

def login(request):
    if request.method == "POST":
        uname = request.POST.get("username")
        pd = request.POST.get("password")

        user_obj = authenticate(username=uname, password=pd)

        if user_obj is not None:
            auth_login(request, user_obj)

            # ✅ Superuser check
            if user_obj.is_superuser:
                return redirect('/Admin_Principal')

            try:
                role_obj = Role_Model.objects.get(Login=user_obj.id)
                role_type = role_obj.user_type.lower()

                # ✅ Role-based redirection
                if role_type == 'student':
                    return redirect('/Student')

                elif role_type == 'teacher':
                    return redirect('/Teacher')

                elif role_type == 'parent':
                    return redirect('/Parent')

                else:
                    return HttpResponse("Unknown role")

            except Role_Model.DoesNotExist:
                return HttpResponse("Role not assigned")

        else:
            return HttpResponse(
                "<script>alert('Invalid Credential !!!');window.location='/';</script>"
            )

    return render(request, 'login.html')



