"""Invalid resampling requests must fail before bootstrap or singleton fallback."""
import pytest
from src.research.evaluation.stats import StatisticsError, cluster_bootstrap_ci


@pytest.mark.parametrize("differences,clusters,options", [
    ([], [], {}), ([[1., 2.]], [["a", "b"]], {}),
    ([1.], ["a"], {"n_boot": 0}), ([1.], ["a"], {"alpha": 1.}),
    ([1.], ["a"], {"statistic": "typo"}),
])
def test_invalid_bootstrap_request(differences, clusters, options):
    with pytest.raises(StatisticsError):
        cluster_bootstrap_ci(differences, clusters, **options)
