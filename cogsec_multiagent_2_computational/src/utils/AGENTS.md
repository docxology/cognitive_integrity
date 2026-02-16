# Utilities Package - Agent Reference

Configuration, logging, timing, and types.

## Modules

### config.py

Configuration management.

**Key Classes:**

- `Config` - Global configuration
- `ExperimentConfig` - Experiment parameters

### logging_setup.py

Logging configuration.

**Key Functions:**

- `setup_logging()` - Configure logging
- `get_logger()` - Get module logger

### timing.py

Timing utilities.

**Key Classes:**

- `Timer` - Context manager for timing
- `TimingStats` - Aggregate timing statistics

**Key Functions:**

- `timed()` - Decorator for timing functions

### random_seed.py

Random seed management.

**Key Functions:**

- `set_seed()` - Set global seed
- `get_seed()` - Get current seed

### types.py

Type definitions.

**Key Types:**

- `AgentId` - Agent identifier
- `TrustScore` - Bounded [0,1] trust
- `Classification` - Firewall result

## Usage

```python
from src.utils import Timer, set_seed, Config

set_seed(42)

with Timer("experiment") as t:
    run_experiment()
print(f"Elapsed: {t.elapsed:.2f}s")
```
