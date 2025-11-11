#!/usr/bin/env python3
"""
Creates a stub multitasking module so yfinance can import it
"""
import os
import site

# Multitasking stub code
multitasking_code = """# Stub multitasking module for yfinance compatibility
import threading
from functools import wraps

def task(func):
    '''Decorator that makes function run normally (not threaded)'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def set_max_threads(n):
    '''Dummy function'''
    pass

def set_engine(engine):
    '''Dummy function'''
    pass

def wait_for_tasks():
    '''Dummy function'''
    pass
"""

# Find site-packages
site_packages = site.getsitepackages()[0]
multitasking_dir = os.path.join(site_packages, 'multitasking')
os.makedirs(multitasking_dir, exist_ok=True)

# Write the stub
with open(os.path.join(multitasking_dir, '__init__.py'), 'w') as f:
    f.write(multitasking_code)

print(f'✅ Created multitasking stub module at: {multitasking_dir}')
