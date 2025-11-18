from django import forms
from .models import UserSearchPreferences, PropertyType


class UserSearchPreferencesForm(forms.ModelForm):
    """Formulaire pour les préférences de recherche utilisateur"""

    class Meta:
        model = UserSearchPreferences
        fields = ['city', 'radius_km', 'property_type']
        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Paris, Lyon, Marseille...'
            }),
            'radius_km': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '100',
                'placeholder': 'Ex: 10'
            }),
            'property_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'city': 'Ville',
            'radius_km': 'Rayon de recherche (km)',
            'property_type': 'Type de bien recherché',
        }
        help_texts = {
            'city': 'Entrez le nom de la ville où vous souhaitez rechercher des biens',
            'radius_km': 'Rayon de recherche autour de la ville (en kilomètres)',
            'property_type': 'Sélectionnez le type de bien que vous recherchez',
        }
