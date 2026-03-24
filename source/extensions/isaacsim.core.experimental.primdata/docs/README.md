# Isaac Sim Core Experimental Prim Data

## Overview

`isaacsim.core.experimental.primdata` hosts the default provider implementation for:

- `isaacsim::core::experimental::prims::IPrimDataReader`
- `isaacsim::core::experimental::prims::IPrimDataReaderManager`

The interface contracts remain in `isaacsim.core.experimental.prims` so consumer extensions can depend on stable shared Carbonite interfaces while selecting the concrete provider through extension enablement.
