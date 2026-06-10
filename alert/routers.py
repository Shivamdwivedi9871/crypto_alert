import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class PrimaryReplicaRouter:
    """
    Production-Grade Database Router for Enterprise High-Load Architecture.
    Handles Write operations to 'default' (Master) and Read operations to 'replica' (Slave).
    """
    # Jo apps target karni hain unka naam list mein rakho (e.g., 'alert', 'auth')
    ROUTER_APP_LABEL = {'alert', 'auth', 'contenttypes', 'sessions'}

    def db_for_read(self, model, **hints):
        """
        Saari Read/Fetch (SELECT) queries replica database par delegate karta hai.
        Agar hints mein specific instance diya ho, toh use safe routing milti hai.
        """

        if model._meta.app_label in self.ROUTER_APP_LABEL:
            # Production check: Agar settings mein replica config missing hai toh master par fall back karo
            
            if 'replica' in settings.DATABASES:
                logger.info(f"PRODUCTION ROUTER [READ]: Routing '{model._meta.model_name}' querty to Slave (replica)")
                return 'replica'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Saari Write/Save/Delete (INSERT, UPDATE, DELETE) queries sirf Master (default) par bhejta hai.
        """
        if model._meta.app_label in self.ROUTER_APP_LABEL:
            logger.info(f"PRODUCTION ROUTER [WRITE]: Routing '{model._meta.model_name}' modification to Master (default)")
            return 'default'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Dono databases ke beech foreign key relations ya database level operations allow karta hai,
        kyunki replication stream continuously data ko sync rakh rahi hai.
        """
        if (obj1._meta.app_label in self.ROUTER_APP_LABEL or
            obj1._meta.app_label in self.ROUTER_APP_LABEL
            ) or obj1._state.db in ['default', 'replica'] and obj2._state.db in ['default', 'replica']:
            return True
        return None

    def allow_migrations(self, db, app_label, model_name=None, **hints):
        """
        CRITICAL FOR PRODUCTION: Migrations NEVER run on Replica/Slave.
        Agar replica par migrations chala di, toh replication chain break ho jayegi (Split-brain issue).
        """
        if app_label in self.ROUTER_APP_LABEL:
            # Data migrations aur table structures sirf Master ('default') par hone chahiye
            if db == 'replica':
                logger.warning(
                    f"BLOCKING MIGRATE: Migration for '{model_name}' blocked on slave (replica)")
                return False
            return db == 'default'
        return None
