from rest_framework import serializers

from .models import Project, ScopeOfWork, ProjectCategory


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ScopeOfWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScopeOfWork
        fields = "__all__"


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = "__all__"
