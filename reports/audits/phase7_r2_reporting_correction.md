# Phase 7-R2 Reporting Correction

The `kub_size_v1` taxonomy remains unchanged. Patient stratum diversity is defined from all FULL_FIELD component-level assignments per patient, not only each image's dominant stratum.

The earlier value 69 counted patients whose **image-level dominant strata** varied across samples. The correct component-exposure definition yields 133 patients with components in at least two strata.

Among 771 FULL_FIELD training images, 206 (26.72%) contained multiple connected components. Of these 206 images, 135 (65.53%) contained components spanning more than one dataset-relative size stratum. Those 135 images represent 17.51% of all FULL_FIELD training images. Forty-four multi-component images contained a TINY component together with at least one larger component.
