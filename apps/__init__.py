# __init__.py inside apps folder
# apps/__init__.py

from apps.user.models import User, AccessToken
from apps.zombie.models import Zombie, File, Command, Log, Notification

# Export them in __all__ to be clean (optional)
__all__ = ["User", "Zombie", "File", "Command", "Log", "AccessToken", "Notification"]
