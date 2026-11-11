# Code and model provenance

The four scientific core modules in `src/` are copied byte-for-byte from the
implementation used by the paper. Their hashes and original source locations
are recorded in `provenance/core_sources.json`. Portable loaders and entry points
replace local experiment-directory dependencies; the classifier algorithms are
unchanged. A registered cache records whether it is the exact paper cache or a
fresh extraction.

No additional open-source license is assigned by this extraction. The authors
should select the intended license before granting reuse permissions. Dependency
and dataset licenses remain separate. UNI and CONCH code/weights are obtained
from their providers under their own conditions; this repository grants no model
access and redistributes no checkpoints or medical images.
