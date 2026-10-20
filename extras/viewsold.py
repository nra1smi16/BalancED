from django.shortcuts import render
from django.http import HttpResponse


def say_hello(request):
    # 1. Grab the name if submitted in the form
    user_name = request.GET.get('your_name', '')
    
    # 2. Package it into a dictionary container
    context = {
        'user_name': user_name
    }
    
    # 3. This tells Django the name of the file to load.
    return render(request, 'core/welcome.html', context) 


#def caculate():
    #x=1
    #y=2
    #return x

#def say_hello(request):
    #x=caculate()
    #return render(request, 'hello.html', {'name': 'Mosh'})


