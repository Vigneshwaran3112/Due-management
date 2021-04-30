import datetime
from datetime import date
from datetime import timedelta

from django.shortcuts import render, redirect
from django.http import Http404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Sum ,Value as V, Prefetch, Q, query
from django.db.models.functions import Coalesce

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .models import *

from django.http import HttpResponse
import time, tablib


# Create your views here.
class Register(APIView):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        user_name = request.POST.get('uname')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')
        try:
            if password == cpassword:
                USERNAME_FIELD = user_name
                User.objects.create_user(USERNAME_FIELD, first_name=first_name, last_name=last_name,
                                                 email=email, password=password, is_staff = True, is_superuser = True)
                return render(request, 'entry_login.html')
        except:
            user = User.objects.get(username=user_name)
            msg = 'Username is already exist...'
            return render(request, 'register.html', {'msg': msg})


class login(APIView):

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        try:
            if user.is_authenticated:
                return render(request, 'entry_login.html', {'user':request.user})
        except:
            pass
        return redirect('/')


class StudentView(APIView):

    def get(self, request):
        standard = Class.objects.filter(status=True, delete=False)
        return render(request, 'student.html', {'standards':standard})

    def post(self, request):
        Student.objects.create(student_id=request.POST.get('student_id'), name=request.POST.get('name'), standard=Class.objects.get(pk=int(request.POST.get('standard'))))
        return render(request, 'home.html', {'user':request.user})


class ClassView(APIView):

    def get(self, request):
        return render(request, 'class.html')

    def post(self, request):
        Class.objects.create(name=request.POST.get('name'), code=request.POST.get('code'))
        return render(request, 'home.html', {'user':request.user})


class YearView(APIView):

    def get(self, request):
        return render(request, 'year.html')

    def post(self, request):
        Year.objects.create(year=request.POST.get('year'), code=request.POST.get('code'))
        return render(request, 'home.html', {'user':request.user})


class PaidAmountAddView(APIView):

    def get(self, request):
        student = Student.objects.filter(status=True, delete=False)
        return render(request, 'paid_amount_add.html', {'student': student})

    def post(self, request):
        PaidAmount.objects.create(student=Student.objects.get(pk=int(request.POST.get('student'))),
                                  standard=Student.objects.get(pk=int(request.POST.get('student'))).standard,
                                  amount=request.POST.get('amount'))
        return redirect('/home/')


class StudentDueOnTillDate(APIView):

    def get(self, request):
        data = []
        student = Student.objects.filter(status=True, delete=False)
        year = Year.objects.filter(status=True, delete=False)
        for stud in student:
            lis = []
            lis.append(stud.student_id)
            lis.append(stud.name)
            lis.append(stud.standard.name)
            today = date.today()
            yesterday = today - timedelta(days=1)
            for yr in year:
                due = DueAmount.objects.filter(student__pk=stud.pk, year__pk=yr.pk, status=True, delete=False)
                due_amount = due.aggregate(total_class_due=Coalesce(Sum('amount'), 0))
                year_wise_amount = due_amount['total_class_due']
                print('due_amount - {}'.format(due_amount['total_class_due']))
                year_paid_amount = YearPaidAmount.objects.filter(student__pk=stud.pk, year__pk=yr.pk, date__date=today, status=True, delete=False)
                final_amount = year_paid_amount.aggregate(total_year_wise_due=Coalesce(Sum('amount'), 0))
                amount = year_wise_amount + final_amount['total_year_wise_due']
                lis.append(amount)

            due_total = DueAmount.objects.filter(student__pk=stud.pk, status=True, delete=False)
            due_total_amount = due_total.aggregate(student_total_due=Coalesce(Sum('amount'), 0))
            year_wise_data = YearPaidAmount.objects.filter(student__pk=stud.pk, date__date=today,  status=True, delete=False)
            student_year_wise_total_amount = year_wise_data.aggregate(student_total_year_wise_due=Coalesce(Sum('amount'), 0))
            student_total_due_amount = due_total_amount['student_total_due'] + student_year_wise_total_amount['student_total_year_wise_due']
            lis.append(student_total_due_amount)

            data.append(lis)


        return render(request, 'student_due_on_yesterday.html', {'data': data, 'yesterday':yesterday.strftime("%d/%m/%y")})


class StudentTotalDue(APIView):

    def get(self, request, pk):
        due_total = DueAmount.objects.filter(student=pk, status=True, delete=False)
        due_total_amount = due_total.aggregate(student_total_due=Coalesce(Sum('amount'), 0))
        return Response(due_total_amount['student_total_due'])



class DueStudentWiseView(APIView):

    def get(self, request):
        data = []
        student = Student.objects.filter(status=True, delete=False)
        year = Year.objects.filter(status=True, delete=False)
        for stud in student:
            lis = []
            lis.append(stud.student_id)
            lis.append(stud.name)
            lis.append(stud.standard.name)
            for yr in year:
                due = DueAmount.objects.filter(student__pk=stud.pk, year__pk=yr.pk, status=True, delete=False)
                due_amount = due.aggregate(total_class_due=Coalesce(Sum('amount'), 0))
                lis.append(due_amount['total_class_due'])
                print('due_amount - {}'.format(due_amount['total_class_due']))
            due_total = DueAmount.objects.filter(student__pk=stud.pk, status=True, delete=False)
            due_total_amount = due_total.aggregate(student_total_due=Coalesce(Sum('amount'), 0))
            lis.append(due_total_amount['student_total_due'])
            data.append(lis)

        return render(request, 'due_student_wise.html', {'data': data})


class DueHomeView(APIView):

    def get(self, request):
        data = []
        year = Year.objects.filter(status=True, delete=False)
        for yr in year:
            lis = []
            lis.append(yr.year)
            due = DueAmount.objects.filter(year__year=yr.year, status=True, delete=False)
            due_amount = due.aggregate(total_year_due=Coalesce(Sum('amount'), 0))
            today = date.today()
            if YearPaidAmount.objects.filter(date__date=today, year__year=yr.year, status=True, delete=False):
                paid_amount = YearPaidAmount.objects.filter(date__date=today, year__year=yr.year, status=True, delete=False)
                paid_total_amount = paid_amount.aggregate(paid_year_due=Coalesce(Sum('amount'), 0))
                lis.append(paid_total_amount['paid_year_due'])
                lis.append(due_amount['total_year_due'])
                lis.append(due_amount['total_year_due'] + paid_total_amount['paid_year_due'])
            else:
                lis.append(0)
                lis.append(due_amount['total_year_due'])
                lis.append(due_amount['total_year_due'] + 0)

            data.append(lis)

        yesterday = today - timedelta(days=1)

        due_data = []
        standard = Class.objects.filter(status=True, delete=False)
        year = Year.objects.filter(status=True, delete=False)
        for std in standard:
            due_lis = []
            due_lis.append(std.name)
            for yr in year:
                due = DueAmount.objects.filter(standard__name=std.name, year__year=yr.year, status=True, delete=False)
                due_amount = due.aggregate(total_class_due=Coalesce(Sum('amount'), 0))
                due_lis.append(due_amount['total_class_due'])
            due_data.append(due_lis)

        return render(request, 'home.html', {'data': data, 'yesterday_date':yesterday.strftime("%d/%m/%y"), 'current_date':today.strftime("%d/%m/%y"), 'due_data' : due_data})


class PaidAmountView(APIView):

    def get(self, request):
        paid_amount = PaidAmount.objects.filter(status=True, delete=False).order_by('-date__time')
        data = []
        for paid in paid_amount:
            lis = []
            year_wise_amount = YearPaidAmount.objects.filter(payment_id=paid.payment_id, status=True, delete=False)
            date = paid.date

            lis.append(date.strftime("%d/%m/%y"))
            lis.append(paid.student.student_id)
            lis.append(paid.student.name)
            lis.append(paid.standard.name)
            lis.append(paid.amount)
            for year_wise in year_wise_amount:
                lis.append(year_wise.amount) if year_wise.year.year == '2019-2020' else lis.append(0)
                lis.append(year_wise.amount) if year_wise.year.year == '2020-2021' else lis.append(0)
                lis.append(year_wise.amount) if year_wise.year.year == '2021-2022' else lis.append(0)
            data.append(lis)
        return render(request, 'paid_amount_list.html', {'paid_amount': data})


class EntryLogin(APIView):

    def get(self, request):
        return render(request, 'entry_login.html')

    def post(self, request):
        name = request.POST.get('name')
        if Student.objects.get(name=name):
            return redirect('/paid_amount_add/')

        return render(request, 'home.html', {'user':request.user})


def StudentDataImport(req):
    if req.method == 'POST':
        dataset = tablib.Dataset()
        imported_data = dataset.load(req.FILES['excelfile'].read(), format='xlsx')
        id = 100
        for data in imported_data:
            id = id+1
            if data[1]=='JR.KG':
                standard = Class.objects.get(code='1')
            elif data[1]=='SR.KG':
                standard = Class.objects.get(code='2')
            elif data[1]=='GR-1':
                standard = Class.objects.get(code='3')
            elif data[1]=='GR-2':
                standard = Class.objects.get(code='4')
            elif data[1]=='GR-3':
                standard = Class.objects.get(code='5')
            elif data[1]=='GR-4':
                standard = Class.objects.get(code='6')
            elif data[1]=='GR-5':
                standard = Class.objects.get(code='7')
            Student.objects.create(student_id=id, name=data[0], standard=standard)
    return render(req, 'excel_import.html')



def DueAmountDataImport(req):
    if req.method == 'POST':
        dataset = tablib.Dataset()
        imported_data = dataset.load(req.FILES['excelfile'].read(), format='xlsx')
        id = 100
        for data in imported_data:
            if data[1]=='JR.KG':
                standard = Class.objects.get(code='1')
            elif data[1]=='SR.KG':
                standard = Class.objects.get(code='2')
            elif data[1]=='GR-1':
                standard = Class.objects.get(code='3')
            elif data[1]=='GR-2':
                standard = Class.objects.get(code='4')
            elif data[1]=='GR-3':
                standard = Class.objects.get(code='5')
            elif data[1]=='GR-4':
                standard = Class.objects.get(code='6')
            elif data[1]=='GR-5':
                standard = Class.objects.get(code='7')
            student = Student.objects.get(name=data[0], standard=standard)
            DueAmount.objects.create(student=student, standard=student.standard, year=Year.objects.get(code=3), amount=data[4])
    return render(req, 'excel_import.html')


