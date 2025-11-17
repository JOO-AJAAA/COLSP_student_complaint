from django.shortcuts import render

def index(request):
  context = {
    'title': 'COLSP - Student Complaint Service',
    'header': 'COLSP',
  }
  return render(request, 'index.html', context)