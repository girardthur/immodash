# Generated manually to preserve data when converting search_zone to search_zones

from django.db import migrations, models


def migrate_search_zone_to_search_zones(apps, schema_editor):
    """
    Migre les données de search_zone (ForeignKey) vers search_zones (ManyToMany)
    """
    Listing = apps.get_model('property_tracker', 'Listing')

    # Pour chaque listing, ajouter son search_zone aux search_zones
    for listing in Listing.objects.all():
        if listing.search_zone_id:  # Vérifier que search_zone existe
            listing.search_zones.add(listing.search_zone_id)


def reverse_migration(apps, schema_editor):
    """
    Fonction inverse pour revenir en arrière (optionnelle)
    """
    Listing = apps.get_model('property_tracker', 'Listing')

    # Pour chaque listing, prendre la première search_zone comme search_zone principal
    for listing in Listing.objects.all():
        first_zone = listing.search_zones.first()
        if first_zone:
            listing.search_zone = first_zone
            listing.save()


class Migration(migrations.Migration):

    dependencies = [
        ('property_tracker', '0003_usersearchpreferences'),
    ]

    operations = [
        # Étape 1: Supprimer l'index qui référence search_zone
        migrations.RemoveIndex(
            model_name='listing',
            name='property_tr_search__373fe7_idx',
        ),

        # Étape 2: Ajouter le nouveau champ ManyToMany (ne supprime pas encore search_zone)
        migrations.AddField(
            model_name='listing',
            name='search_zones',
            field=models.ManyToManyField(
                related_name='listings',
                to='property_tracker.searchzone',
                verbose_name='Zones de recherche'
            ),
        ),

        # Étape 3: Migrer les données de search_zone vers search_zones
        migrations.RunPython(
            migrate_search_zone_to_search_zones,
            reverse_code=reverse_migration
        ),

        # Étape 4: Supprimer l'ancien champ search_zone
        migrations.RemoveField(
            model_name='listing',
            name='search_zone',
        ),
    ]
