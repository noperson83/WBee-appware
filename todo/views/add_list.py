from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.text import slugify
from project.models import Project
from todo.forms import AddTaskListForm
from todo.utils import staff_check

@login_required
@user_passes_test(staff_check)
def add_list(request, proj=None, scop=None) -> HttpResponse:
    """Allow staff users to create a new :class:`TaskList`.

    ``proj`` and ``scop`` are optional to make the view usable from the tests
    where no specific project context is supplied.
    """
    # Only staffers can add lists, regardless of TODO_STAFF_USER setting.
    if not request.user.is_staff:
        raise PermissionDenied

    if request.POST:
        form = AddTaskListForm(request.user, proj, request.POST)
        if form.is_valid():
            try:
                newlist = form.save(commit=False)
                newlist.slug = slugify(newlist.name)
                newlist.save()
                messages.success(request, "A new list has been added.")
                if scop:
                    return HttpResponseRedirect("/project/scope/detail/" + str(scop))
                return redirect("todo:lists")

            except IntegrityError:
                messages.warning(
                    request,
                    "There was a problem saving the new list. "
                    "Most likely a list with the same name in the same group already exists.",
                )
    else:
        initial = {}
        if request.user.groups.all().count() == 1:
            initial["group"] = request.user.groups.all()[0]
        if scop:
            initial["scope"] = scop
        form = AddTaskListForm(request.user, proj, initial=initial)

    context = {"form": form, "proj": proj}

    return render(request, "todo/add_list.html", context)
