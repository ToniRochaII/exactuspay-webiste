import logging
import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)

RESEND_BACKEND = "anymail.backends.resend.EmailBackend"
LOCAL_EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CONSOLE_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
FILEBASED_EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
DUMMY_EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

SAFE_NON_SENDING_BACKENDS = {
    LOCAL_EMAIL_BACKEND,
    CONSOLE_EMAIL_BACKEND,
    FILEBASED_EMAIL_BACKEND,
    DUMMY_EMAIL_BACKEND,
}

SAFE_MANAGEMENT_COMMANDS = {
    "collectstatic",
    "check",
    "makemigrations",
    "migrate",
    "test",
    "shell",
}


def _strip_optional_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_env_file(
    *,
    env_path: str | Path | None = None,
    override: bool = False,
    environ: dict | None = None,
) -> dict[str, str]:
    source = os.environ if environ is None else environ
    candidate = Path(env_path) if env_path is not None else Path(__file__).resolve().parent.parent / ".env"
    if not candidate.exists():
        return {}

    loaded: dict[str, str] = {}
    for raw_line in candidate.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = _strip_optional_quotes(value.strip())
        if not override and key in source:
            continue
        source[key] = value
        loaded[key] = value
    return loaded


def env_bool(name: str, default: bool = False, *, environ: dict | None = None) -> bool:
    source = os.environ if environ is None else environ
    value = source.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def env_required(name: str, *, environ: dict | None = None, allow_blank: bool = False) -> str:
    source = os.environ if environ is None else environ
    value = source.get(name)
    if value is None:
        raise ImproperlyConfigured(f"{name} environment variable is required.")

    value = str(value).strip()
    if not allow_blank and not value:
        raise ImproperlyConfigured(f"{name} environment variable cannot be blank.")
    return value


def is_safe_management_command(argv: list[str] | None = None) -> bool:
    active_argv = argv if argv is not None else sys.argv
    if len(active_argv) < 2:
        return False
    return str(active_argv[1]).strip().lower() in SAFE_MANAGEMENT_COMMANDS


def has_resend_settings(*, environ: dict | None = None) -> bool:
    source = os.environ if environ is None else environ
    return bool(str(source.get("RESEND_API_KEY", "") or "").strip())


def default_email_backend(
    *,
    debug: bool,
    environ: dict | None = None,
    argv: list[str] | None = None,
) -> str:
    if has_resend_settings(environ=environ):
        return RESEND_BACKEND
    if debug:
        return CONSOLE_EMAIL_BACKEND
    if is_safe_management_command(argv):
        return LOCAL_EMAIL_BACKEND
    return LOCAL_EMAIL_BACKEND


def build_email_config(
    *,
    debug: bool,
    environ: dict | None = None,
    argv: list[str] | None = None,
) -> dict[str, object]:
    source = os.environ if environ is None else environ
    configured_backend = str(source.get("EMAIL_BACKEND", "") or "").strip()
    backend = configured_backend or default_email_backend(debug=debug, environ=source, argv=argv)
    config: dict[str, object] = {"EMAIL_BACKEND": backend}

    if (
        not configured_backend
        and backend == LOCAL_EMAIL_BACKEND
        and not debug
        and not is_safe_management_command(argv)
    ):
        logger.warning(
            "No explicit EMAIL_BACKEND was configured while DEBUG is disabled; using %s "
            "as a safe non-sending fallback. Configure RESEND_API_KEY and DEFAULT_FROM_EMAIL "
            "to enable Resend delivery, or set EMAIL_BACKEND=%s explicitly.",
            LOCAL_EMAIL_BACKEND,
            RESEND_BACKEND,
        )

    if backend == RESEND_BACKEND:
        config["ANYMAIL"] = {
            "RESEND_API_KEY": env_required("RESEND_API_KEY", environ=source),
        }
        config["DEFAULT_FROM_EMAIL"] = env_required("DEFAULT_FROM_EMAIL", environ=source)
    elif backend in SAFE_NON_SENDING_BACKENDS:
        config["DEFAULT_FROM_EMAIL"] = str(
            source.get("DEFAULT_FROM_EMAIL", "ExactusPay <noreply@exactuspay.com>")
        ).strip()
        if backend == FILEBASED_EMAIL_BACKEND:
            config["EMAIL_FILE_PATH"] = str(source.get("EMAIL_FILE_PATH", "/tmp/exactuspay-emails")).strip()
    else:
        raise ImproperlyConfigured(
            f"Unsupported EMAIL_BACKEND '{backend}'. Configure Resend with RESEND_API_KEY or use one of: "
            f"{', '.join(sorted(SAFE_NON_SENDING_BACKENDS))}."
        )

    config["SERVER_EMAIL"] = str(source.get("SERVER_EMAIL") or config["DEFAULT_FROM_EMAIL"]).strip()
    return config
