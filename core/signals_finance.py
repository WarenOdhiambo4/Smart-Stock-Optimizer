import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Sale, Expense, Logistics
from .finance_services import AccountingError, create_income_from_sale, create_expense_from_core, create_logistics_from_core


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Sale)
def sync_sale_to_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    if not getattr(settings, 'ACCOUNTING_AUTO_POST_FROM_CORE', True):
        return
    try:
        create_income_from_sale(instance, user=instance.created_by)
    except AccountingError as exc:
        logger.warning("Auto-post sale failed: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Auto-post sale crashed: %s", exc)


@receiver(post_save, sender=Expense)
def sync_expense_to_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    if not getattr(settings, 'ACCOUNTING_AUTO_POST_FROM_CORE', True):
        return
    try:
        create_expense_from_core(instance, user=instance.created_by)
    except AccountingError as exc:
        logger.warning("Auto-post expense failed: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Auto-post expense crashed: %s", exc)


@receiver(post_save, sender=Logistics)
def sync_logistics_to_ledger(sender, instance, created, **kwargs):
    if not created:
        return
    if not getattr(settings, 'ACCOUNTING_AUTO_POST_FROM_CORE', True):
        return
    try:
        create_logistics_from_core(instance, user=instance.created_by)
    except AccountingError as exc:
        logger.warning("Auto-post logistics failed: %s", exc)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Auto-post logistics crashed: %s", exc)
