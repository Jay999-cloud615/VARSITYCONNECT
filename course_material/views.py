import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.views.decorators.http import require_POST
from .models import Resource
from .forms import ResourceUploadForm

@login_required
def course_material_view(request):
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.save()
            return redirect('course_material')
    else:
        form = ResourceUploadForm()

    resources = Resource.objects.all()
    context = {
        'resources': resources,
        'form': form,
    }
    return render(request, 'course_material/material.html', context)


@login_required
@require_POST
def delete_resource_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk, uploaded_by=request.user)
    pdf_file = resource.pdf_file
    image = resource.image
    resource.delete()
    pdf_file.delete(save=False)
    if image:
        image.delete(save=False)
    return redirect('course_material')


@login_required
def download_resource_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    filename = os.path.basename(resource.pdf_file.name)
    return FileResponse(
        resource.pdf_file.open('rb'),
        as_attachment=True,
        filename=filename,
        content_type='application/pdf',
    )