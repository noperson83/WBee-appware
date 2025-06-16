from rest_framework import serializers

from .models import Project, ScopeOfWork


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ScopeOfWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScopeOfWork
        fields = "__all__"
