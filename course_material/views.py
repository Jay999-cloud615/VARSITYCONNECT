from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from .models import Resource
from .forms import ResourceUploadForm

@login_required
def course_material_view(request):
    if request.method == 'GET':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=True)
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
def download_resource_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    return FileResponse(resource.pdf_file.open(), as_attachment=False, filename=resource.pdf_file.name.split('_')[-11])