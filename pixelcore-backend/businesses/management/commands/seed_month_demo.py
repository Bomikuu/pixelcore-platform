from django.conf import settings
from django.core.management.base import BaseCommand

from businesses.demo.common import FIXTURE
from businesses.demo.importer import import_month, restore_media


class Command(BaseCommand):
    help = "Import the bundled fictional business and a connected month of sample activity."

    def add_arguments(self, parser):
        parser.add_argument("--month", help="YYYY-MM; defaults to the current month in Asia/Manila.")
        parser.add_argument("--slug", default="northline-monthly-demo", help="Dedicated demonstration business slug.")
        parser.add_argument("--owner-email", help="Attach the demo business to an existing account without changing its password.")
        parser.add_argument("--fixture", default=str(FIXTURE), help="Monthly dataset JSON file with an adjacent images directory.")
        parser.add_argument("--media-only", action="store_true", help="Restore demo images in this environment without refreshing orders or other activity.")

    def handle(self, *args, **options):
        if options["media_only"]:
            ctx = restore_media(slug=options["slug"], fixture=options["fixture"])
            self.stdout.write(self.style.SUCCESS(f"Demo media ready: {len(ctx.assets)} assets; {len(ctx.new_files)} missing files restored."))
            self.stdout.write("Existing accounts and monthly activity were not refreshed.")
            return
        ctx = import_month(month=options["month"], slug=options["slug"], owner_email=options["owner_email"], fixture=options["fixture"])
        self.stdout.write(self.style.SUCCESS(f"Monthly demonstration imported: {ctx.month}"))
        self.stdout.write(f"Business: {ctx.business.display_name} ({ctx.business.slug})")
        self.stdout.write(f"Orders: {len(ctx.data['orders'])}; bookings: {len(ctx.data['bookings'])}; customers: {len(ctx.customers)}; staff: {len(ctx.staff)}")
        self.stdout.write(f"Login email: {ctx.owner.email}")
        if options["owner_email"]:
            self.stdout.write("Use your existing password and select the demo business in the workspace.")
        else:
            self.stdout.write("Initial demo password: PixelCoreDemo123! (existing passwords are preserved)")
        origin = settings.PIXELCORE_FRONTEND_URL.rstrip("/")
        self.stdout.write(f"Storefront: {origin}/site/{ctx.business.slug}")
        self.stdout.write("All data and imagery are fictional. No email, payment, or calendar requests were sent.")
