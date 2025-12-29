# servicenow/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import AssignmentGroup
from .forms import AssignmentGroupForm

@staff_member_required
def assignment_group_list(request):
    groups = AssignmentGroup.objects.all().order_by("name")
    return render(request, "admin/assignment_group_list.html", {
        "groups": groups
    })


@staff_member_required
def assignment_group_create(request):
    if request.method == "POST":
        form = AssignmentGroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment group created successfully.")
            return redirect("servicenow:assignment_group_list")
    else:
        form = AssignmentGroupForm()

    return render(request, "admin/assignment_group_form.html", {
        "form": form,
        "title": "Add Assignment Group"
    })

@staff_member_required
def assignment_group_update(request, pk):
    group = get_object_or_404(AssignmentGroup, pk=pk)

    if request.method == "POST":
        form = AssignmentGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment group updated successfully.")
            return redirect("servicenow:assignment_group_list")
    else:
        form = AssignmentGroupForm(instance=group)

    return render(request, "admin/assignment_group_form.html", {
        "form": form,
        "title": "Edit Assignment Group"
    })


@staff_member_required
def assignment_group_delete(request, pk):
    group = get_object_or_404(AssignmentGroup, pk=pk)
    group.delete()
    messages.success(request, "Assignment group deleted.")
    return redirect("servicenow:assignment_group_list")
