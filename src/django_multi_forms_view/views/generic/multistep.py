from .multi import *
from django.core.exceptions import PermissionDenied
from django.views.generic import CreateView
from django.views.generic.edit import FormView,ModelFormMixin
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

class RequestMixin:
    
   def get_initial(self, form_name):
       initial_method = 'get_%s_initial' % form_name
       if hasattr(self, initial_method):
           return getattr(self, initial_method)()
       else:
           return {'action': form_name,'request':self.request}

class MultiStepFormsMixin:

    steps=[]
    current_step=None
    template_names={}

    def forms_valid(self, forms, form_name):
        """If the forms are valid, save the associated model."""
        obj = forms.get(form_name)
        self.object = obj.save(request=self.request)

        if form_name in self.success_url:
            return HttpResponseRedirect(self.get_success_url(form_name))

        else:
            return self.render_to_response(self.get_context_data(forms=forms,form_name=form_name))

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
                kwargs.update({'instance':self.object})
                
        return kwargs

    def get_success_url(self, form_name=None):
        return self.success_urls.get(form_name, self.success_url)[form_name]

    def get_next_form_classes(self):
        if self.steps[-1]!=self.request.POST.get('action'):
            form_classes={n:self.form_classes[n] for n in self.form_display[self.steps[self.steps.index(self.current_step)]]}
        else:
            form_classes={}

        return form_classes

    def get_form_classes(self):
        if self.request.method=='GET':
            form_classes={n:self.form_classes[n] for n in self.form_display[self.steps[0]]}

        elif self.request.method=='POST':
            form_classes={n:self.form_classes[n] for n in self.form_display[self.request.POST.get('action')]}

        else:
            raise PermissionDenied()

        return form_classes

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

    def get(self, request, *args, **kwargs):
        self.current_step=self.steps[0]
        return super().get(request, *args, **kwargs)
     
    def post(self, request, *args, **kwargs):
        if self.steps[-1]!=self.request.POST.get('action') and self.request.POST.get('action') in self.steps:
            self.current_step=self.steps[self.steps.index(self.request.POST.get('action'))+1]
            
        return super().post(request, *args, **kwargs)

    def get_context_data(self,*args,**kwargs):
        context=super().get_context_data(*args,**kwargs)
        context['objects']={re.sub('_form$','',form_class):obj.instance for form_class,obj in context['forms'].items()}

        if self.request.method=='POST':
            context['forms']=self.get_forms(self.get_next_form_classes())
            
        return context
    
class BaseMultipleFormsCreateView(ModelMultiFormMixin, ProcessMultipleFormsView):
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
   pass

class MultiStepFormsView(MultiDeletionMixin,MultiStepFormsMixin,SingleObjectTemplateResponseMixin, BaseMultipleFormsCreateView):
   pass

class MultiStepRequestFormsView(RequestMixin,MultiStepFormsMixin,SingleObjectTemplateResponseMixin, BaseMultipleFormsCreateView):
   pass
