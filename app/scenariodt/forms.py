from django import forms
from rdflib import Dataset
from django.contrib.gis import forms as geoforms
from leaflet.forms.widgets import LeafletWidget
from django.contrib.auth.models import User

 
class ScenarioSharingForm(forms.Form):

    scenario = forms.ChoiceField()
    users = forms.MultipleChoiceField()
    
    def __init__(self, options, *args, **kwargs):
        super(ScenarioSharingForm, self).__init__(*args, **kwargs)
        self.fields['scenario'].choices = options
        self.fields['users'].choices = [(user.id, user.username) for user in User.objects.all()]

class ScenarioComparisonForm(forms.Form):

    scenarios = forms.MultipleChoiceField()
    
    def __init__(self, options, *args, **kwargs):
        super(ScenarioComparisonForm, self).__init__(*args, **kwargs)
        self.fields['scenarios'].choices = options

class ScenarioSelectionForm(forms.Form):

    scenario = forms.ChoiceField()
    
    def __init__(self, options, *args, **kwargs):
        super(ScenarioSelectionForm, self).__init__(*args, **kwargs)
        self.fields['scenario'].choices = options

class ScenarioConfigForm(forms.Form):
    scenario_condition = forms.CharField(max_length=100, label='Scenario Condition')
    scenario_description = forms.CharField(max_length=500, label='Scenario Description', 
                                           widget=forms.Textarea)
    scenario_region = geoforms.MultiPolygonField(widget=LeafletWidget())
    affected_metrics = forms.MultipleChoiceField(
        label='Scenario Parameters (Affected Metrics)', widget=forms.CheckboxSelectMultiple())

    def __init__(self, options, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['affected_metrics'].choices = options
        for option in self.fields['affected_metrics'].choices:
            self.fields[option[0]] = forms.DecimalField(
                label=option[1] + ' Impact Factor', required=False, min_value=0, 
                max_value=10, initial=1.0, decimal_places=2, widget=forms.NumberInput(
                attrs={'step': '0.1'}))
    
    def clean(self):
        cleaned_data = super().clean()
        values = {}
        for option in cleaned_data.get('affected_metrics', []):
            values[option] = cleaned_data.get(option)
        cleaned_data['impact_factors'] = values
        return cleaned_data
            
class ScenarioReconfigForm(forms.Form):
    scenario_condition = forms.CharField(max_length=100, label='Scenario Condition')
    scenario_description = forms.CharField(max_length=500, label='Scenario Description', 
                                           widget=forms.Textarea)
    
    affected_metrics = forms.MultipleChoiceField(
        label='Scenario Parameters (Affected Metrics)', widget=forms.CheckboxSelectMultiple())

    def __init__(self, options, initials, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['affected_metrics'].choices = options.items()
        self.fields['scenario_condition'].initial = initials['condition']
        self.fields['scenario_description'].initial = initials['description']
        self.fields['affected_metrics'].initial = list(initials['parameters'].keys())
        for option in self.fields['affected_metrics'].choices:
            if option[0] in initials['parameters'].keys():
                init = float(initials['parameters'][option[0]])
            else:
                init = 1.0
            self.fields[option[0]] = forms.DecimalField(
                label=option[1] + ' Impact Factor', required=False, min_value=0, 
                max_value=10, initial=init, decimal_places=2, widget=forms.NumberInput(
                attrs={'step': '0.1'}))
    
    def clean(self):
        cleaned_data = super().clean()
        values = {}
        for option in cleaned_data.get('affected_metrics', []):
            values[option] = cleaned_data.get(option)
        cleaned_data['impact_factors'] = values
        return cleaned_data
    
class ScenarioExecForm(forms.Form):
    
    scenario = forms.ChoiceField()
    def __init__(self, options, *args, **kwargs):
        super(ScenarioExecForm, self).__init__(*args, **kwargs)
        self.fields['scenario'].choices = options
