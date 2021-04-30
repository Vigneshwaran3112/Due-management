from django.db import models

import uuid

# Create your models here.
class BaseModel(models.Model):
    status = models.BooleanField(default=True)
    delete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Class(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Year(BaseModel):
    year = models.CharField(max_length=100)
    code = models.CharField(max_length=100)

    def __str__(self):
        return self.year


class Student(BaseModel):
    student_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    standard = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='student_class_name')
    phone = models.CharField(max_length=25, blank=True, null=True)

    def __str__(self):
        return '{0} -- {1}'.format(self.name, self.phone)


class YearPaidAmount(BaseModel):
    date = models.DateTimeField(auto_now_add=True)
    year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name='paid_amount_year', null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='year_paid_amount_student_name')
    standard = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='year_paid_amount_class_name')
    amount = models.PositiveIntegerField(default=0)
    payment_id = models.CharField(max_length=300, blank=True, null=True)

    def __str__(self):
        return '{0} -- {1}'.format(self.year, self.amount)


class DueAmount(BaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='due_amount_student_name')
    standard = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='due_amount_class_name')
    year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name='due_amount_year')
    amount = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.student.name


class PaidAmount(BaseModel):
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    date = models.DateTimeField(auto_now_add=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='paid_amount_student_name')
    standard = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='paid_amount_class_name')
    amount = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        paid_amount = int(self.amount)
        for i in range(1,4):
            due = DueAmount.objects.get(student=self.student, year__code=i, status=True, delete=False)
            if (due.amount != 0) and (due.amount >= paid_amount) and (paid_amount != 0):
                value = due.amount - paid_amount
                year_amount = YearPaidAmount.objects.create(year=Year.objects.get(code=str(i)), amount=paid_amount,
                                                            student=Student.objects.get(pk=(self.student).pk),
                                                            standard=Class.objects.get(pk=(self.student).standard.pk),
                                                            payment_id=self.payment_id)
                year_amount.save()
                paid_amount = 0
                due.amount = value


            elif (due.amount != 0) and (due.amount <= paid_amount) and (paid_amount != 0):
                value = paid_amount - due.amount
                year_amount = YearPaidAmount.objects.create(year=Year.objects.get(code=str(i)), amount=due.amount,
                                                            student=Student.objects.get(pk=(self.student).pk),
                                                            standard=Class.objects.get(pk=(self.student).standard.pk),
                                                            payment_id=self.payment_id)
                year_amount.save()
                paid_amount = value
                due.amount = 0

            due.save()

        super(PaidAmount, self).save(*args, **kwargs)

    def __str__(self):
        return '{0} -- {1}'.format(self.student, self.amount)


