from django import forms
from django.contrib.auth.models import User, Group 
from django.forms import ModelForm
from jobsite.models import Jobsite
from .models import Project, ScopeOfWork, Device, Wire, Hardware, Software, License, Travel
from todo.models import Task, TaskList

class ProjectForm(ModelForm):
    job_num         = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    revision        = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    site_contact    = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    date_requested  = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    due_date        = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    finished_date   = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    burden          = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    markup          = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    estimated_cost  = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    contract_value  = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    site_contact    = forms.CharField(widget=forms.widgets.TextInput(), required=False)
    site_contact    = forms.CharField(widget=forms.widgets.TextInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.fields["jobsite"].widget. attrs = {
            "id": "id_jobsite",
            "class": "custom-select mb-3",
            "name": "jobsite",
        }
        self.fields["job_name"].widget.attrs = {
            "id": "id_job_name",
            "class": "form-control mb-3",
            "name": "job_name",
        }
        self.fields["install_overview"].widget.attrs = {
            "id": "id_install_overview",
            "class": "form-control mb-3",
            "name": "install_overview",
        }
        self.fields["pricing_disclaim"].widget.attrs = {
            "id": "id_pricing_disclaim",
            "class": "form-control mb-3",
            "name": "pricing_disclaim",
        }
        self.fields["job_status"].widget.attrs = {
            "id": "id_job_status",
            "class": "form-control mb-3",
            "name": "job_status",
        }
        self.fields["tax_status"].widget.attrs = {
            "id": "id_tax_status",
            "class": "form-control mb-3",
            "name": "tax_status",
        }
        self.fields["estimator"].widget.attrs = {
            "id": "id_estimator",
            "class": "form-control mb-3",
            "name": "estimator",
        }
        self.fields["projectmanager"].widget.attrs = {
            "id": "id_projectmanager",
            "class": "form-control mb-3",
            "name": "projectmanager",
        }
        self.fields["foremen"].widget.attrs = {
            "id": "id_foremen",
            "class": "form-control mb-3",
            "name": "foremen",
        }
        self.fields["lead"].widget.attrs = {
            "id": "id_lead",
            "class": "form-control mb-3",
            "name": "lead",
        }
        self.fields["workers"].widget.attrs = {
            "id": "id_workers",
            "class": "form-control mb-3",
            "name": "workers",
        }
    class Meta:
        model = Project
        fields = [  'job_num', 
                    'jobsite', 
                    'job_name', 
                    'revision', 
                    'install_overview',
                    'pricing_disclaim', 
                    'site_contact', 
                    'date_requested', 
                    'due_date', 
                    'finished_date',
                    'paid_date', 
                    'job_status',
                    'tax_status',
                    'division_status',
                    'type_status',
                    'estimator',
                    'projectmanager',
                    'foremen',
                    'lead',
                    'workers',
                    'burden',
                    'markup',
                    'licmarkup',
                    'estimated_cost',
                    'contract_value']
        exclude = []

class ScopeOfWorkForm(ModelForm):
    area = forms.CharField(widget=forms.widgets.TextInput(), required=True)

    def __init__(self, *args, **kwargs):
        super(ScopeOfWorkForm, self).__init__(*args, **kwargs)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["system_type"].widget. attrs = {
            "id": "id_system_type",
            "class": "custom-select mb-3",
            "name": "system_type",
        }
        self.fields["priority"].widget. attrs = {
            "id": "id_priority",
            "class": "custom-select mb-3",
            "name": "priority",
        }
    class Meta:
        model = ScopeOfWork
        fields = [  'project',
                    'area',  
                    'priority',
                    'system_type', ]
        exclude = [ 'lastmodification', 
                    'dateofcreation' ]

class DeviceForm(ModelForm):
    purchased_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    onsite_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    installed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def __init__(self, proj, *args, **kwargs):
        super(DeviceForm, self).__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().filter(job_num=proj)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["task"].queryset = Task.objects.all().filter(task_list__scope__project__job_num=proj)
        self.fields["task"].widget. attrs = {
            "id": "id_task",
            "class": "custom-select mb-3",
            "name": "task",
        }
        self.fields["device"].widget. attrs = {
            "id": "id_device",
            "class": "custom-select mb-3",
            "name": "device",
        }
        self.fields["qty"].widget. attrs = {
            "id": "id_qty",
            "class": "custom-select mb-3",
            "name": "qty",
        }
        self.fields["cost"].widget. attrs = {
            "id": "id_cost",
            "class": "custom-select mb-3",
            "name": "cost",
        }
        self.fields["device_status"].widget. attrs = {
            "id": "id_device_status",
            "class": "custom-select mb-3",
            "name": "device_status",
        }

    class Meta:
        model = Device
        fields = [  'project',
                    'task',  
                    'device',
                    'purchased_date',
                    'onsite_date',
                    'installed_date',
                    'qty',
                    'cost',
                    'device_status', ]
        exclude = [ 'lastmodification',
                    'dateofcreation' ]

class WireForm(ModelForm):
    purchased_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    onsite_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    installed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def __init__(self, proj, *args, **kwargs):
        super(WireForm, self).__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().filter(job_num=proj)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["task"].queryset = Task.objects.all().filter(task_list__scope__project__job_num=proj)
        self.fields["task"].widget. attrs = {
            "id": "id_task",
            "class": "custom-select mb-3",
            "name": "task",
        }
        self.fields["wire"].widget. attrs = {
            "id": "id_wire",
            "class": "custom-select mb-3",
            "name": "wire",
        }
        self.fields["length"].widget. attrs = {
            "id": "id_length",
            "class": "custom-select mb-3",
            "name": "length",
        }
        self.fields["cost_per_foot"].widget. attrs = {
            "id": "id_cost_per_foot",
            "class": "custom-select mb-3",
            "name": "cost_per_foot",
        }
        self.fields["wire_status"].widget. attrs = {
            "id": "id_wire_status",
            "class": "custom-select mb-3",
            "name": "wire_status",
        }

    class Meta:
        model = Wire
        fields = [  'project',
                    'task',  
                    'wire',
                    'purchased_date',
                    'onsite_date',
                    'installed_date',
                    'length',
                    'cost_per_foot',
                    'wire_status', ]
        exclude = [ 'lastmodification',
                    'dateofcreation' ]

class HardwareForm(ModelForm):
    purchased_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    onsite_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    installed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def __init__(self, proj, *args, **kwargs):
        super(HardwareForm, self).__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().filter(job_num=proj)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["task"].queryset = Task.objects.all().filter(task_list__scope__project__job_num=proj)
        self.fields["task"].widget. attrs = {
            "id": "id_task",
            "class": "custom-select mb-3",
            "name": "task",
        }
        self.fields["hardware"].widget. attrs = {
            "id": "id_hardware",
            "class": "custom-select mb-3",
            "name": "hardware",
        }
        self.fields["qty"].widget. attrs = {
            "id": "id_qty",
            "class": "custom-select mb-3",
            "name": "qty",
        }
        self.fields["cost"].widget. attrs = {
            "id": "id_cost",
            "class": "custom-select mb-3",
            "name": "cost",
        }
        self.fields["hardware_status"].widget. attrs = {
            "id": "id_hardware_status",
            "class": "custom-select mb-3",
            "name": "hardware_status",
        }

    class Meta:
        model = Hardware
        fields = [  'project',
                    'task',  
                    'hardware',
                    'purchased_date',
                    'onsite_date',
                    'installed_date',
                    'qty',
                    'cost',
                    'hardware_status', ]
        exclude = [ 'dateofcreation',
                    'lastmodification' ]

class SoftwareForm(ModelForm):
    purchased_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    onsite_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    installed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    
    def __init__(self, proj, *args, **kwargs):
        super(SoftwareForm, self).__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().filter(job_num=proj)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["task"].queryset = Task.objects.all().filter(task_list__scope__project__job_num=proj)
        self.fields["task"].widget. attrs = {
            "id": "id_task",
            "class": "custom-select mb-3",
            "name": "task",
        }
        self.fields["software"].widget. attrs = {
            "id": "id_software",
            "class": "custom-select mb-3",
            "name": "software",
        }
        self.fields["qty"].widget. attrs = {
            "id": "id_qty",
            "class": "custom-select mb-3",
            "name": "qty",
        }
        self.fields["cost"].widget. attrs = {
            "id": "id_cost",
            "class": "custom-select mb-3",
            "name": "cost",
        }
        self.fields["software_status"].widget. attrs = {
            "id": "id_software_status",
            "class": "custom-select mb-3",
            "name": "software_status",
        }

    class Meta:
        model = Software
        fields = [  'project',
                    'task',  
                    'software',
                    'purchased_date',
                    'onsite_date',
                    'installed_date',
                    'qty',
                    'cost',
                    'software_status', ]
        exclude = [ 'dateofcreation',
                    'lastmodification' ]

class LicenseForm(ModelForm):
    purchased_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    onsite_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    installed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def __init__(self, proj, *args, **kwargs):
        super(LicenseForm, self).__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().filter(job_num=proj)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["task"].queryset = Task.objects.all().filter(task_list__scope__project__job_num=proj)
        self.fields["task"].widget. attrs = {
            "id": "id_task",
            "class": "custom-select mb-3",
            "name": "task",
        }
        self.fields["license"].widget. attrs = {
            "id": "id_license",
            "class": "custom-select mb-3",
            "name": "license",
        }
        self.fields["qty"].widget. attrs = {
            "id": "id_qty",
            "class": "custom-select mb-3",
            "name": "qty",
        }
        self.fields["cost"].widget. attrs = {
            "id": "id_cost",
            "class": "custom-select mb-3",
            "name": "cost",
        }
        self.fields["license_status"].widget. attrs = {
            "id": "id_license_status",
            "class": "custom-select mb-3",
            "name": "license_status",
        }

    class Meta:
        model = License
        fields = [  'project',
                    'task',  
                    'license',
                    'purchased_date',
                    'onsite_date',
                    'installed_date',
                    'qty',
                    'cost',
                    'license_status', ]
        exclude = [ 'lastmodification',
                    'dateofcreation' ]

class TravelForm(ModelForm):
    purchased_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    onsite_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)
    installed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def __init__(self, proj, *args, **kwargs):
        super(TravelForm, self).__init__(*args, **kwargs)
        self.fields["project"].queryset = Project.objects.all().filter(job_num=proj)
        self.fields["project"].widget. attrs = {
            "id": "id_project",
            "class": "custom-select mb-3",
            "name": "project",
        }
        self.fields["task"].queryset = Task.objects.all().filter(task_list__scope__project__job_num=proj)
        self.fields["task"].widget. attrs = {
            "id": "id_task",
            "class": "custom-select mb-3",
            "name": "task",
        }
        self.fields["travel_name"].widget. attrs = {
            "id": "id_travel_name",
            "class": "custom-select mb-3",
            "name": "travel_name",
        }
        self.fields["hotel_name"].widget. attrs = {
            "id": "id_hotel_name",
            "class": "custom-select mb-3",
            "name": "hotel_name",
        }
        self.fields["gas_estimate"].widget. attrs = {
            "id": "id_gas_estimate",
            "class": "custom-select mb-3",
            "name": "gas_estimate",
        }
        self.fields["cost"].widget. attrs = {
            "id": "id_cost",
            "class": "custom-select mb-3",
            "name": "cost",
        }
        self.fields["hotel_status"].widget. attrs = {
            "id": "id_hotel_status",
            "class": "custom-select mb-3",
            "name": "hotel_status",
        }

    class Meta:
        model = Travel
        fields = [  'project',
                    'task',
                    'travel_name',
                    'hotel_name',
                    'cost',
                    'hotel_status',
                    'gas_estimate',
                    'purchased_date', ]
        exclude = [ 'lastmodification',
                    'dateofcreation' ]
