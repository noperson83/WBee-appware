from django.shortcuts import render, redirect
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
import datetime
from datetime import datetime as dtime, date, time, timedelta
from django.views.generic.dates import WeekArchiveView
from django.contrib.auth.decorators import login_required, user_passes_test


def is_employee(user):
    return user.is_authenticated and user.is_active and getattr(user, "is_employee", False)


class EmployeeRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_employee(self.request.user)

from .models import TimeCard
from .forms import TimeCardForm

from schedule.models import Event

class TimeCardWeekArchiveView(EmployeeRequiredMixin, LoginRequiredMixin, WeekArchiveView):
    queryset = TimeCard.objects.all()
    date_field = "date"
    week_format = "%U"
    allow_future = True

@login_required
@user_passes_test(is_employee)
def index(request):
    template_name = 'timecard.html'
    tadai = datetime.datetime.now()
    year, week, dow = tadai.isocalendar()
    week = week - 2
    # Find the first day of the week.
    if dow == 1:
        # Since we want to start with Sunday, let's test for that condition.
        start_date = tadai
    else:
        # Otherwise, subtract `dow` number days to get the first day
        start_date = tadai - timedelta(dow)

    # Now, add 6 for the last day of the week (i.e., count up to Saturday)
    end_date = start_date + timedelta(6)
    worker_address = request.user
    this_week = TimeCard.objects.filter(worker=worker_address).filter(date__range=[start_date, end_date])
    
    week_total = datetime.timedelta(0,0,0)
    
    for timecard in this_week:
        week_total += timecard.day_total
    days_to_hours = week_total.days * 24
    sec_to_hours = (week_total.seconds) / 3600
    overall_hours = days_to_hours + sec_to_hours
    if overall_hours >= 40:
        over_time = 0
        over_time = overall_hours - 40
    else :
        over_time = 0

    return render(
        request,
        template_name,
        context={
            'this_week':this_week,
            'tadai':tadai,
            'start_date':start_date,
            'end_date':end_date,
            'worker_address':worker_address,
            'week_total':week_total,
            'overall_hours':overall_hours,
            'over_time':over_time,
            'year':year,
            'week':week,
            },
    )

class TimeCardCreate(EmployeeRequiredMixin, LoginRequiredMixin, CreateView):
    """Create view using the modern TimeCardForm."""
    model = TimeCard
    form_class = TimeCardForm

    def form_valid(self, form):
        form.instance.worker = self.request.user
        return super().form_valid(form)

    success_url = reverse_lazy('timecard:list')

class TimeCardUpdate(EmployeeRequiredMixin, LoginRequiredMixin, UpdateView):
    model = TimeCard
    form_class = TimeCardForm
    template_name_suffix = '_update_form'
    success_url = reverse_lazy('timecard:list')

class TimeCardDelete(EmployeeRequiredMixin, LoginRequiredMixin, DeleteView):
    model = TimeCard
    success_url = reverse_lazy('timecard:list')


class TimeCardListView(EmployeeRequiredMixin, LoginRequiredMixin, generic.ListView):
    """List view showing recent timecards for the logged-in user."""
    model = TimeCard
    template_name = 'timecard/timecard_list.html'
    paginate_by = 50

    def get_queryset(self):
        return (
            TimeCard.objects.filter(worker=self.request.user)
            .order_by('-date', '-start_time')
        )

@login_required
@user_passes_test(is_employee)
def TimeCardCreater(request):
    template_name = 'scheduling_timecard.html'
    heading_message = 'Time Card Test'
    
    tadai = datetime.datetime.now()
    year, week, dow = tadai.isocalendar()

    # Find the first day of the week.
    if dow == 1:
        # Since we want to start with Sunday, let's test for that condition.
        start_date = tadai
    else:
        # Otherwise, subtract `dow` number days to get the first day
        start_date = tadai - timedelta(dow)

    # Now, add 6 for the last day of the week (i.e., count up to Saturday)
    end_date = start_date + timedelta(6)
    worker_address = request.user
    this_week = TimeCard.objects.filter(date__range=[start_date, end_date]).filter(worker=worker_address)
    
    return render(request, template_name, {
        'this_week':this_week,
        'tadai':tadai,
        'start_date':start_date,
        'end_date':end_date,
        'worker_address':worker_address,
        'heading': heading_message
    })