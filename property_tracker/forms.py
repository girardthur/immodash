from django import forms
from .models import UserSearchPreferences, SearchZone, PropertyType


class UserSearchPreferencesForm(forms.ModelForm):
    """Formulaire pour les préférences de recherche utilisateur (sélection d'une zone existante)"""

    class Meta:
        model = UserSearchPreferences
        fields = ['selected_zone']
        widgets = {
            'selected_zone': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'selected_zone': 'Zone de recherche',
        }
        help_texts = {
            'selected_zone': 'Sélectionnez la zone de recherche pour voir les annonces correspondantes',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les zones actives
        self.fields['selected_zone'].queryset = SearchZone.objects.filter(is_active=True).order_by('city', 'radius_km')


class SearchZoneForm(forms.ModelForm):
    """Formulaire pour créer une zone de recherche (admins uniquement)"""

    class Meta:
        model = SearchZone
        fields = ['city', 'radius_km', 'property_type', 'is_active']
        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Paris, Lyon 69001, Kourou...'
            }),
            'radius_km': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Ex: 15'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'city': 'Ville',
            'radius_km': 'Rayon de recherche (km)',
            'property_type': 'Type de bien',
            'is_active': 'Zone active',
        }
        help_texts = {
            'city': 'Entrez le nom de la ville (optionnel: code postal pour plus de précision)',
            'radius_km': 'Rayon de recherche autour de la ville (en kilomètres)',
            'property_type': 'Type de bien à scraper dans cette zone',
            'is_active': 'Si décoché, cette zone ne sera pas scrapée',
        }
