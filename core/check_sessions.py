# wifi_hotspot/core/management/commands/check_sessions.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from ...core.models import WifiSession
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Checks for and deactivates expired WiFi sessions.'

    def handle(self, *args, **options):
        """
        The main logic for the management command.
        It finds all active sessions that have passed their end_time and deactivates them.
        """
        now = timezone.now()
        
        # Find all active sessions where the end_time is in the past
        expired_sessions = WifiSession.objects.filter(is_active=True, end_time__lt=now)
        
        deactivated_count = 0
        for session in expired_sessions:
            try:
                # Use the deactivate method on the model to handle the logic
                session.deactivate()
                deactivated_count += 1
            except Exception as e:
                logger.error(f"Error deactivating session {session.id}: {e}")
                self.stdout.write(self.style.ERROR(f"Error deactivating session {session.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully deactivated {deactivated_count} expired sessions."))
        logger.info(f"Scheduled task finished. Deactivated {deactivated_count} expired sessions.")

