import pytest

from django.contrib.auth.models import Group

from todo.models import Task, TaskList


@pytest.fixture
def todo_setup(django_user_model):
    # Two groups with different users, two sets of tasks.

    g1 = Group.objects.create(name="Workgroup One")
    u1 = django_user_model.objects.create_user(
        email="u1@example.com",
        password="password",
        first_name="User",
        last_name="One",
        employee_id="E001",
    )
    u1.groups.add(g1)
    tlist1 = TaskList.objects.create(
        group=g1,
        name="Zip",
        slug="zip",
        created_by=u1,
        status="on_hold",
    )
    Task.objects.create(created_by=u1, title="Task 1", task_list=tlist1, priority=1)
    Task.objects.create(
        created_by=u1,
        title="Task 2",
        task_list=tlist1,
        priority=2,
        completed=True,
        completion_percentage=100,
        status="completed",
    )
    Task.objects.create(created_by=u1, title="Task 3", task_list=tlist1, priority=3)

    g2 = Group.objects.create(name="Workgroup Two")
    u2 = django_user_model.objects.create_user(
        email="u2@example.com",
        password="password",
        first_name="User",
        last_name="Two",
        employee_id="E002",
    )
    u2.groups.add(g2)
    tlist2 = TaskList.objects.create(
        group=g2,
        name="Zap",
        slug="zap",
        created_by=u2,
        status="on_hold",
    )
    Task.objects.create(created_by=u2, title="Task 1", task_list=tlist2, priority=1)
    Task.objects.create(
        created_by=u2,
        title="Task 2",
        task_list=tlist2,
        priority=2,
        completed=True,
        completion_percentage=100,
        status="completed",
    )
    Task.objects.create(created_by=u2, title="Task 3", task_list=tlist2, priority=3)


@pytest.fixture
def admin_user(django_user_model):
    """Return a superuser for admin client tests."""
    return django_user_model.objects.create_superuser(
        email="admin@example.com",
        password="password",
        first_name="Admin",
        last_name="User",
        employee_id="ADMIN",
    )


@pytest.fixture
def admin_client(admin_user, client):
    client.force_login(admin_user)
    return client
