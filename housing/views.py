from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from .forms import JobForm

@login_required
def job_list_view(request):
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.posted_by = request.user
            job.save()
            return redirect('jobs')
    else:
        form = JobForm()

    jobs = Job.objects.all().order_by('-created_at')

    context = {
        'form': form,
        'jobs': jobs,
    }
    return render(request, 'housing/job_list.html', context)

@login_required
def job_detail_view(request, pk):
    job = get_object_or_404(Job, pk=pk)
    context = {
        'job': job,
    }
    return render(request, 'housing/job_detail.html', context)


@login_required
@require_POST
def delete_job_view(request, pk):
    job = get_object_or_404(Job, pk=pk, posted_by=request.user)
    job.delete()
    return redirect('jobs')