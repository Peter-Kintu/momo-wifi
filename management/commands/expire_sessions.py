# wifi_hotspot/core/management/commands/expire_sessions.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import WifiSession
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Django management command to check for and deactivate expired WiFi sessions.
    This command should be run periodically by a scheduler (e.g., Windows Task Scheduler).
    """
    help = 'Deactivates expired WiFi sessions based on their end_time.'

    def handle(self, *args, **options):
        """
        The main logic for the management command.
        """
        self.stdout.write(self.style.SUCCESS('Starting session expiration check...'))
        logger.info("Starting session expiration check...")

        now = timezone.now()
        
        # Find all active sessions where the end_time is in the past
        expired_sessions = WifiSession.objects.filter(is_active=True, end_time__lt=now)
        
        deactivated_count = 0

        if not expired_sessions.exists():
            self.stdout.write('No expired sessions found.')
            logger.info("No expired sessions found.")
            return

        for session in expired_sessions:
            try:
                # Use the deactivate method on the model to handle the logic
                session.deactivate()
                deactivated_count += 1
                self.stdout.write(self.style.WARNING(f"Deactivated session for IP '{session.ip_address}'."))
                logger.info(f"Deactivated session for IP '{session.ip_address}'.")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error deactivating session {session.id}: {e}"))
                logger.error(f"Error deactivating session {session.id}: {e}")
            
        self.stdout.write(self.style.SUCCESS(f"Finished session check. Deactivated {deactivated_count} expired sessions."))
        logger.info(f"Finished session check. Deactivated {deactivated_count} expired sessions.")

