from django.views.generic.edit import FormView,ModelFormMixin
from . import ProcessMultipleStepFormsView,MultiStepFormMixin,UserMixin
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.http import HttpResponseRedirect

class ModelMultiStepFormsMixin(MultiStepFormMixin,ModelFormMixin):

    def get_context_data(self, **kwargs):

        if self.extra_context is not None:
            kwargs.update(self.extra_context)
            
        if hasattr(self, 'object'):
            kwargs.update({'object':self.object})

        if self.request.method=='POST':
            if kwargs['forms'][self.request.POST.get('action')].is_valid():
                next_forms = self.get_forms(self.get_next_form_classes())           
                kwargs['forms'].update(**next_forms)
                
        return kwargs

    def forms_valid(self, forms, form_name):
        """If the forms are valid, save the associated model."""
        obj = forms.get(form_name)
        self.object = obj.save()
 
        if form_name in self.success_url:
            return HttpResponseRedirect(self.get_success_url(form_name))

        else:
            return self.render_to_response(self.get_context_data(forms=forms,form_name=form_name))

class BaseMultipleFormsCreateView(ModelMultiStepFormsMixin, ProcessMultipleStepFormsView):
    """
    Base view for updating an existing object.

    Using this base class requires subclassing to provide a response mixin.
    """
    def get(self, request, *args, **kwargs):
        self.object = None
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = None
        return super().post(request, *args, **kwargs)
   
class MultiFormsCreateView(SingleObjectTemplateResponseMixin, BaseMultipleFormsCreateView):
    """
    """

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response() is overridden.
        """
        self.template_name=self.template_names[self.current_step]
        
        if self.template_name is None:
            raise ImproperlyConfigured(
                "TemplateResponseMixin requires either a definition of "
                "'template_name' or an implementation of 'get_template_names()'")
        else:
            return [self.template_name]

class UserModelMultiStepFormsView(UserMixin, MultiFormsCreateView):
    """
    """
