import os
from .base import *

# select settings for server
if os.environ.get('DEV_OR_PROD') == 'prod':
    from .prod import *
else:
    from .dev import *
