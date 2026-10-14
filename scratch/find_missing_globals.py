import sys
import os
import types
import importlib
import dis
import builtins

sys.path.insert(0, os.path.abspath('.'))

modules_to_test = [
    'config.database',
    'models.schemas',
    'services.payments',
    'services.pricing',
    'services.machines',
    'services.queuing',
    'services.analytics_engine',
    'services.audit_service',
    'services.email_service',
    'routes.auth',
    'routes.appointments',
    'routes.dashboard',
    'routes.machines',
    'routes.pos',
    'routes.payments',
    'app'
]

potential_bugs = []
builtin_names = set(dir(builtins))

for mod_name in modules_to_test:
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        potential_bugs.append(f"ImportError in {mod_name}: {e}")
        continue

    # Inspect all functions defined in the module
    for attr_name in dir(mod):
        attr = getattr(mod, attr_name)
        if isinstance(attr, types.FunctionType) and attr.__module__ == mod_name:
            for instr in dis.get_instructions(attr):
                if instr.opname in ('LOAD_GLOBAL',):
                    name = instr.argval
                    if name not in attr.__globals__ and name not in builtin_names:
                        potential_bugs.append(f"{mod_name}.{attr_name} (line {instr.starts_line}): Global '{name}' is MISSING!")

print("=== CHECKING BYTECODE FOR MISSING LOAD_GLOBAL ===")
if potential_bugs:
    for b in set(potential_bugs):
        print("True Bug found:", b)
else:
    print("All function globals verified! Zero missing imports or global NameErrors.")
