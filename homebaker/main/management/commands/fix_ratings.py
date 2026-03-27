from django.core.management.base import BaseCommand
from main.models import BakerProfile, Cake, Review
from django.db.models import Avg

class Command(BaseCommand):
    help = 'Recalibrate all baker and cake ratings based on existing reviews'

    def handle(self, *args, **options):
        self.stdout.write('Starting rating recalibration...')

        # 1. Fix Cake Ratings
        cakes = Cake.objects.all()
        for cake in cakes:
            cake.update_rating()
            self.stdout.write(f'Updated Cake: {cake.name} - {cake.average_rating} ({cake.total_reviews} reviews)')

        # 2. Fix Baker Ratings
        bakers = BakerProfile.objects.all()
        for baker in bakers:
            baker.update_rating()
            self.stdout.write(f'Updated Baker: {baker.shop_name} - {baker.average_rating} ({baker.total_reviews} reviews)')

        self.stdout.write(self.style.SUCCESS('All ratings have been recalibrated successfully!'))
