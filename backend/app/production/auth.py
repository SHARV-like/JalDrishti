from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.production.config import get_settings
from app.production.database import get_session
from app.production.models import Membership, Role, User


@dataclass(frozen=True)
class Principal:
    user_id: str
    organisation_id: str
    role: Role


def current_principal(
    authorization: str | None = Header(default=None),
    x_development_user: str | None = Header(default=None),
    x_organisation_id: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> Principal:
    settings = get_settings()
    if settings.auth_mode == "development" and x_development_user and x_organisation_id:
        membership = session.scalar(select(Membership).where(Membership.user_id == x_development_user, Membership.organisation_id == x_organisation_id))
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No membership for the requested organisation")
        return Principal(x_development_user, x_organisation_id, Role(membership.role))
    if settings.auth_mode == "oidc":
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            jwks_client = jwt.PyJWKClient(f"{settings.oidc_issuer.rstrip('/')}/.well-known/jwks.json")
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience=settings.oidc_audience,
                issuer=settings.oidc_issuer,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity token") from exc
        user_id = claims.get("sub")
        organisation_id = claims.get(settings.oidc_organisation_claim)
        if not isinstance(user_id, str) or not isinstance(organisation_id, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identity token is missing required subject or organisation claims")
        membership = session.scalar(select(Membership).where(Membership.user_id == user_id, Membership.organisation_id == organisation_id))
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active organisation membership")
        return Principal(user_id, organisation_id, Role(membership.role))
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def require_roles(*roles: Role):
    def dependency(principal: Principal = Depends(current_principal)) -> Principal:
        if principal.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action")
        return principal
    return dependency


def ensure_user(session: Session, user_id: str) -> None:
    if not session.get(User, user_id):
        session.add(User(id=user_id, display_name="Development user"))
