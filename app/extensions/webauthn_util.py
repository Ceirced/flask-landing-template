from flask_security import WebauthnUtil
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from flask import current_app


class PasskeyWebauthnUtil(WebauthnUtil):
    """Custom WebauthnUtil for first-factor-only passkey registration.

    The default Flask-Security WebauthnUtil forces CROSS_PLATFORM attachment for
    first-factor registration. This prevents modern platform authenticators
    (Touch ID, Face ID, Windows Hello) from being registered as first-factor keys.

    Since modern passkeys sync across devices via iCloud Keychain, Google Password
    Manager, etc., platform authenticators work great as first-factor credentials.
    We remove the CROSS_PLATFORM restriction and let the browser/user decide.

    Note: WebAuthn requires the application to be served over HTTPS in production
    environments. Localhost is exempt from this requirement.
    """

    def authenticator_selection(self, user, usage):
        select_criteria = AuthenticatorSelectionCriteria()
        select_criteria.user_verification = UserVerificationRequirement.PREFERRED

        if not current_app.config.get("SECURITY_WAN_ALLOW_USER_HINTS"):
            select_criteria.resident_key = ResidentKeyRequirement.REQUIRED
        else:
            select_criteria.resident_key = ResidentKeyRequirement.PREFERRED

        return select_criteria
