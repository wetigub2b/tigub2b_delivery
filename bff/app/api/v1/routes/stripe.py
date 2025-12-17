"""
Stripe Connect routes for driver payment onboarding.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.driver import Driver
from app.models.user import User
from app.schemas.driver import StripeConnectResponse, StripeStatusResponse
from app.services.stripe_service import StripeService, verify_webhook_signature
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/connect", response_model=StripeConnectResponse)
async def initiate_stripe_connect(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> StripeConnectResponse:
    """
    Initiate Stripe Connect onboarding for a driver.
    Creates a Stripe Express account and returns the onboarding URL.
    """
    # Find driver by phone number
    result = await session.execute(
        select(Driver).where(Driver.phone == current_user.phonenumber)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )

    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured"
        )

    try:
        stripe_service = StripeService(session)
        result = await stripe_service.create_connect_account(driver)

        return StripeConnectResponse(
            onboarding_url=result["onboarding_url"],
            stripe_account_id=result["stripe_account_id"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Stripe account: {str(e)}"
        )


@router.get("/status", response_model=StripeStatusResponse)
async def get_stripe_status(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> StripeStatusResponse:
    """
    Get the current Stripe Connect status for a driver.
    Checks with Stripe API and updates local database.
    """
    # Find driver by phone number
    result = await session.execute(
        select(Driver).where(Driver.phone == current_user.phonenumber)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )

    # If no Stripe account, return pending status
    if not driver.stripe_account_id:
        return StripeStatusResponse(
            stripe_status="pending",
            stripe_payouts_enabled=False,
            stripe_details_submitted=False,
            stripe_connected_at=None,
            can_receive_payouts=False,
            requirements_due=None
        )

    if not settings.stripe_secret_key:
        # Return cached status if Stripe not configured
        return StripeStatusResponse(
            stripe_status=driver.stripe_status or "pending",
            stripe_payouts_enabled=driver.stripe_payouts_enabled or False,
            stripe_details_submitted=driver.stripe_details_submitted or False,
            stripe_connected_at=driver.stripe_connected_at,
            can_receive_payouts=driver.stripe_payouts_enabled and driver.stripe_status == "verified",
            requirements_due=None
        )

    try:
        stripe_service = StripeService(session)
        status_data = await stripe_service.check_account_status(driver)

        return StripeStatusResponse(**status_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Stripe status: {str(e)}"
        )


@router.post("/refresh-link", response_model=StripeConnectResponse)
async def refresh_stripe_link(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> StripeConnectResponse:
    """
    Generate a new Stripe onboarding link for a driver.
    Used when the previous link has expired.
    """
    # Find driver by phone number
    result = await session.execute(
        select(Driver).where(Driver.phone == current_user.phonenumber)
    )
    driver = result.scalars().first()

    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )

    if not driver.stripe_account_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Stripe account found. Please initiate setup first."
        )

    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured"
        )

    try:
        stripe_service = StripeService(session)
        result = await stripe_service.create_account_link(driver.stripe_account_id)

        return StripeConnectResponse(
            onboarding_url=result["onboarding_url"],
            stripe_account_id=result["stripe_account_id"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Stripe link: {str(e)}"
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Handle Stripe webhook events.
    Updates driver payment status based on account changes.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )

    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret not configured"
        )

    try:
        event = verify_webhook_signature(payload, signature)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signature: {str(e)}"
        )

    try:
        stripe_service = StripeService(session)
        await stripe_service.handle_webhook_event(event)
        return {"status": "success"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )
