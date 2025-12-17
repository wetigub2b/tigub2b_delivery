"""
Stripe Connect service for driver payment onboarding.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.driver import Driver

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for handling Stripe Connect operations"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_driver_by_phone(self, phone: str) -> Optional[Driver]:
        """Get driver by phone number"""
        result = await self.session.execute(
            select(Driver).where(Driver.phone == phone)
        )
        return result.scalars().first()

    async def create_connect_account(self, driver: Driver) -> dict:
        """
        Create a Stripe Connect Express account for a driver.
        Returns the account ID and onboarding URL.
        """
        if not settings.stripe_secret_key:
            raise ValueError("Stripe is not configured. Please set STRIPE_SECRET_KEY.")

        # If driver already has a Stripe account, just create a new onboarding link
        if driver.stripe_account_id:
            return await self.create_account_link(driver.stripe_account_id)

        try:
            # Create new Express account
            account = stripe.Account.create(
                type="express",
                country="CA",
                email=driver.email,
                capabilities={
                    "transfers": {"requested": True},
                },
                business_type="individual",
                metadata={
                    "driver_id": str(driver.id),
                    "driver_phone": driver.phone,
                }
            )

            # Save account ID to driver
            driver.stripe_account_id = account.id
            driver.stripe_status = "onboarding"

            # Create onboarding link
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=settings.stripe_connect_refresh_url,
                return_url=settings.stripe_connect_return_url,
                type="account_onboarding",
            )

            driver.stripe_onboarding_url = account_link.url
            await self.session.commit()

            logger.info(f"Created Stripe account {account.id} for driver {driver.id}")

            return {
                "stripe_account_id": account.id,
                "onboarding_url": account_link.url,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account for driver {driver.id}: {e}")
            raise

    async def create_account_link(self, stripe_account_id: str) -> dict:
        """Create a new onboarding/update link for an existing account"""
        if not settings.stripe_secret_key:
            raise ValueError("Stripe is not configured. Please set STRIPE_SECRET_KEY.")

        try:
            account_link = stripe.AccountLink.create(
                account=stripe_account_id,
                refresh_url=settings.stripe_connect_refresh_url,
                return_url=settings.stripe_connect_return_url,
                type="account_onboarding",
            )

            return {
                "stripe_account_id": stripe_account_id,
                "onboarding_url": account_link.url,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account link: {e}")
            raise

    async def check_account_status(self, driver: Driver) -> dict:
        """
        Check the status of a driver's Stripe Connect account.
        Updates the local database with current status.
        """
        if not settings.stripe_secret_key:
            raise ValueError("Stripe is not configured. Please set STRIPE_SECRET_KEY.")

        if not driver.stripe_account_id:
            return {
                "stripe_status": "pending",
                "stripe_payouts_enabled": False,
                "stripe_details_submitted": False,
                "stripe_connected_at": None,
                "can_receive_payouts": False,
                "requirements_due": None,
            }

        try:
            account = stripe.Account.retrieve(driver.stripe_account_id)

            # Update driver record
            driver.stripe_details_submitted = account.details_submitted
            driver.stripe_payouts_enabled = account.payouts_enabled

            # Determine status
            if account.payouts_enabled and account.details_submitted:
                driver.stripe_status = "verified"
                if not driver.stripe_connected_at:
                    driver.stripe_connected_at = datetime.utcnow()
            elif account.details_submitted:
                # Details submitted but payouts not enabled - might need verification
                if account.requirements and account.requirements.currently_due:
                    driver.stripe_status = "restricted"
                else:
                    driver.stripe_status = "onboarding"
            else:
                driver.stripe_status = "onboarding"

            await self.session.commit()

            # Get requirements if any
            requirements_due = None
            if account.requirements and account.requirements.currently_due:
                requirements_due = list(account.requirements.currently_due)

            return {
                "stripe_status": driver.stripe_status,
                "stripe_payouts_enabled": driver.stripe_payouts_enabled,
                "stripe_details_submitted": driver.stripe_details_submitted,
                "stripe_connected_at": driver.stripe_connected_at,
                "can_receive_payouts": driver.stripe_payouts_enabled and driver.stripe_status == "verified",
                "requirements_due": requirements_due,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error checking account status: {e}")
            raise

    async def handle_webhook_event(self, event: dict) -> bool:
        """
        Handle incoming Stripe webhook events.
        Returns True if event was processed successfully.
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        logger.info(f"Processing Stripe webhook: {event_type}")

        if event_type == "account.updated":
            account_id = data.get("id")
            if account_id:
                # Find driver by stripe account ID
                result = await self.session.execute(
                    select(Driver).where(Driver.stripe_account_id == account_id)
                )
                driver = result.scalars().first()

                if driver:
                    # Update driver status based on account data
                    driver.stripe_details_submitted = data.get("details_submitted", False)
                    driver.stripe_payouts_enabled = data.get("payouts_enabled", False)

                    if driver.stripe_payouts_enabled and driver.stripe_details_submitted:
                        driver.stripe_status = "verified"
                        if not driver.stripe_connected_at:
                            driver.stripe_connected_at = datetime.utcnow()
                    elif driver.stripe_details_submitted:
                        requirements = data.get("requirements", {})
                        if requirements.get("currently_due"):
                            driver.stripe_status = "restricted"
                        else:
                            driver.stripe_status = "onboarding"
                    else:
                        driver.stripe_status = "onboarding"

                    await self.session.commit()
                    logger.info(f"Updated driver {driver.id} Stripe status to {driver.stripe_status}")
                    return True

        return False


def verify_webhook_signature(payload: bytes, signature: str) -> dict:
    """Verify webhook signature and return event data"""
    if not settings.stripe_webhook_secret:
        raise ValueError("Stripe webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, settings.stripe_webhook_secret
        )
        return event
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise
