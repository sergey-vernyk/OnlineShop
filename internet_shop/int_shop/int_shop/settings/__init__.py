import os
from .base import *

# выбор настроек для сервера
if os.environ.get('DEV_OR_PROD') == 'prod':
    from .prod import *
else:
    from .dev import *
