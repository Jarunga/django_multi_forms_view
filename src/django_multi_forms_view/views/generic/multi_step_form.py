from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView
from django.views.generic.edit import FormView,ModelFormMixin
from django.views.generic.edit import ProcessFormView
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.http import HttpResponseRedirect

#-*-coding=utf8-*-
import re

class MultiDeletionMixin:
    """Provide the ability to delete objects."""
    success_url = None
    form_class_deletion=None

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object=self.form_classes[self.request.POST.get('action')]._meta.model.objects.filter(register_user_id=request.user.id)
        success_url = self.get_success_url(self.request.POST.get('action'))
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url(self.request.POST.get('action')))

    def post(self, request, *args, **kwargs):
        if self.form_class_deletion==self.request.POST.get('action'):
            return self.delete(request, *args, **kwargs)
        else:
            return super().post(request, *args, **kwargs)

class UserMixin:
    
   def get_initial(self, form_name):
       initial_method = 'get_%s_initial' % form_name
       if hasattr(self, initial_method):
           return getattr(self, initial_method)()
       else:
           return {'action': form_name,'user':self.request.user}

class MultiStepFormMixin(ContextMixin):

    form_classes = {} 
    prefixes = {}
    success_urls = {}
    
    initial = {}
    prefix = None
    success_url = None
    
    steps=[]
    current_step=None
    template_names={}
    
    def get_form_classes(self):
        if self.request.method=='GET':
            form_classes={n:self.form_classes[n] for n in self.form_display[self.steps[0]]}

        elif self.request.method=='POST':
            form_classes={n:self.form_classes[n] for n in self.form_display[self.request.POST.get('action')]}

        else:
            raise PermissionDenied()

        return form_classes

    def get_forms(self, form_classes):
        return dict([(key, self._create_form(key, class_name)) \
            for key, class_name in form_classes.items()])

    def get_form_kwargs(self, form_name):
        kwargs = {}
        kwargs.update({'initial':self.get_initial(form_name)})
        kwargs.update({'prefix':self.get_prefix(form_name)})
        if self.request.method in ('POST', 'PUT'):
            if form_name==self.request.POST.get('action'):
                kwargs.update({
                    'data': self.request.POST,
                    'files': self.request.FILES,
                })
            else:
                if hasattr(self, 'object'):
                    kwargs.update({'instance':self.object})
                
        return kwargs

    def forms_valid(self, forms, form_name):
        form_valid_method = '%s_form_valid' % form_name

        if hasattr(self, form_valid_method):
            return getattr(self, form_valid_method)(forms[form_name])
        else:
            if form_name in self.success_url:
                return HttpResponseRedirect(self.get_success_url(form_name))

            else:
                return self.render_to_response(self.get_context_data(forms=forms,form_name=form_name)) 

    def forms_invalid(self, forms):

        self.current_step=self.steps[0]

        return self.render_to_response(self.get_context_data(forms=forms))

    def get_initial(self, form_name):
        initial_method = 'get_%s_initial' % form_name
        if hasattr(self, initial_method):
            return getattr(self, initial_method)()
        else:
            return {'action': form_name}
        
    def get_prefix(self, form_name):
        return self.prefixes.get(form_name, self.prefix)

    def get_success_url(self, form_name=None):
        return self.success_urls.get(form_name, self.success_url)[form_name]

    def _create_form(self, form_name, form_class):
        form_kwargs = self.get_form_kwargs(form_name)
        form = form_class(**form_kwargs)
        return form

    def get_next_form_classes(self):
        if self.steps[-1]!=self.request.POST.get('action'):
            form_classes={n:self.form_classes[n] for n in self.form_display[self.steps[self.steps.index(self.current_step)]]}
        else:
            form_classes={}

        return form_classes

    def get_context_data(self, **kwargs):

        if self.extra_context is not None:
            kwargs.update(self.extra_context)

        if self.request.method=='POST':
            if kwargs['forms'][self.request.POST.get('action')].is_valid():
                next_forms = self.get_forms(self.get_next_form_classes())           
                kwargs['forms'].update(**next_forms)
                
        return kwargs
    
class ProcessMultipleStepFormsView(ProcessFormView):

    def get(self, request, *args, **kwargs):
        self.current_step=self.steps[0]
        form_classes = self.get_form_classes()
        forms = self.get_forms(form_classes)
        return self.render_to_response(self.get_context_data(forms=forms))
     
    def post(self, request, *args, **kwargs):
        if self.steps[-1]!=self.request.POST.get('action') and self.request.POST.get('action') in self.steps:
            self.current_step=self.steps[self.steps.index(self.request.POST.get('action'))+1]

        form_classes = self.get_form_classes()
        form_name = request.POST.get('action')
        
        return self._process_individual_form(form_name, form_classes)

    def _process_individual_form(self, form_name, form_classes):
        forms = self.get_forms(form_classes)
        form = forms.get(form_name)
        if not form:
            return HttpResponseForbidden()
        elif form.is_valid():
            return self.forms_valid(forms, form_name)
        else:
            return self.forms_invalid(forms)

class BaseMultipleStepFormsView(MultiStepFormMixin, ProcessMultipleStepFormsView):
    """
    A base view for displaying several forms.
    """
 
class MultiStepFormsView(MultiDeletionMixin,TemplateResponseMixin, BaseMultipleStepFormsView):
    """
    A view for displaying several forms, and rendering a template response.
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
    
class UserMultiStepFormsView(UserMixin,MultiStepFormsView):
    """
    """     

