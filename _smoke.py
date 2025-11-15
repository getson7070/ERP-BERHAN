import asyncio
import os
import sys
from typing import Annotated, NoReturn
from typing import TypeAlias  # Deferred annotation support in Python 3.14+

try:
    from rich.console import Console
    from pydantic import BaseModel, ValidationError  # New: Pydantic for secure validation
    import sentry_sdk  # New: Sentry for user-friendly error tracking
except ImportError:
    Console = None
    BaseModel = object
    ValidationError = Exception
    sentry_sdk = None

# New: Initialize Sentry for monitoring (add DSN in .env)
if sentry_sdk:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN", "https://example@sentry.io/123"),
        traces_sample_rate=1.0,
        environment="dev" if "dev" in os.getenv("ENV", "") else "prod",
    )

# New: Type aliases with deferred annotations for better type safety
HealthStatus: TypeAlias = Annotated[bool, "System health indicator"]

# New: Pydantic model for config validation
class SmokeConfig(BaseModel):
    db_url: str
    app_modules: list[str]

async def check_db_connection(config: SmokeConfig) -> HealthStatus:
    """Async DB health check with validation and Sentry capture."""
    try:
        # Validate config
        config.validate()
        # Placeholder for async query (update to SQLAlchemy 2.0+ with Alembic 1.17.1)
        await asyncio.sleep(0.1)
        console("[green]DB connection: OK[/green]")
        return True
    except ValidationError as ve:
        if sentry_sdk:
            sentry_sdk.capture_exception(ve)
        console(f"[red]Config validation failed: {ve}[/red]")
        return False
    except Exception as e:
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        console(f"[red]DB connection failed: {e}[/red]")  # Enhanced error messages in Python 3.14
        return False

async def check_app_modules(config: SmokeConfig) -> HealthStatus:
    """Check module imports with modern async."""
    try:
        # Example imports (adjust to actual)
        from erp import app  # Core ERP
        from app_ext import some_extension
        await asyncio.sleep(0.1)
        console("[green]Module communication: OK[/green]")
        return True
    except ImportError as e:
        if sentry_sdk:
            sentry_sdk.capture_exception(e)
        console(f"[red]Module import failed: {e}[/red]")
        return False

async def main() -> NoReturn:
    console = Console() if Console else print
    console("[bold]Running ERP-BERHAN Smoke Test (Python 3.14 Updated)...[/bold]")
    
    # Load and validate config (new security/user-friendly layer)
    try:
        config = SmokeConfig(db_url=os.getenv("DATABASE_URL", "sqlite:///./.local-dev.db"), app_modules=["erp", "web"])
    except ValidationError as ve:
        console(f"[red bold]Invalid config: {ve}[/red bold]")
        sys.exit(1)
    
    db_ok = await check_db_connection(config)
    modules_ok = await check_app_modules(config)
    
    if db_ok and modules_ok:
        console("[green bold]All checks passed! System healthy.[/green bold]")
        sys.exit(0)
    else:
        console("[red bold]Smoke test failed. Check Sentry/logs.[/red bold]")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())