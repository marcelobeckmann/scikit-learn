from types import GeneratorType

import numpy as np
from numpy import linalg

from scipy.sparse import dok_matrix, csr_matrix, issparse
from scipy.spatial.distance import cosine, cityblock, minkowski, wminkowski
from scipy.spatial.distance import cdist, pdist, squareform

import pytest

from sklearn import config_context

from sklearn.utils.testing import assert_array_almost_equal
from sklearn.utils.testing import assert_allclose
from sklearn.utils.testing import assert_almost_equal
from sklearn.utils.testing import assert_array_equal
from sklearn.utils.testing import assert_raises
from sklearn.utils.testing import assert_raises_regexp
from sklearn.utils.testing import ignore_warnings
from sklearn.utils.testing import assert_raise_message

from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics.pairwise import manhattan_distances
from sklearn.metrics.pairwise import haversine_distances
from sklearn.metrics.pairwise import linear_kernel
from sklearn.metrics.pairwise import chi2_kernel, additive_chi2_kernel
from sklearn.metrics.pairwise import polynomial_kernel
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.metrics.pairwise import laplacian_kernel
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import cosine_distances
from sklearn.metrics.pairwise import gower_distances
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.metrics.pairwise import pairwise_distances_chunked
from sklearn.metrics.pairwise import pairwise_distances_argmin_min
from sklearn.metrics.pairwise import pairwise_distances_argmin
from sklearn.metrics.pairwise import pairwise_kernels
from sklearn.metrics.pairwise import PAIRWISE_KERNEL_FUNCTIONS
from sklearn.metrics.pairwise import PAIRWISE_DISTANCE_FUNCTIONS
from sklearn.metrics.pairwise import PAIRWISE_BOOLEAN_FUNCTIONS
from sklearn.metrics.pairwise import PAIRED_DISTANCES
from sklearn.metrics.pairwise import check_pairwise_arrays
from sklearn.metrics.pairwise import check_paired_arrays
from sklearn.metrics.pairwise import paired_distances
from sklearn.metrics.pairwise import paired_euclidean_distances
from sklearn.metrics.pairwise import paired_manhattan_distances
from sklearn.metrics.pairwise import _euclidean_distances_upcast
from sklearn.preprocessing import normalize
from sklearn.exceptions import DataConversionWarning


def test_pairwise_distances():
    # Test the pairwise_distance helper function.
    rng = np.random.RandomState(0)

    # Euclidean distance should be equivalent to calling the function.
    X = rng.random_sample((5, 4))
    S = pairwise_distances(X, metric="euclidean")
    S2 = euclidean_distances(X)
    assert_array_almost_equal(S, S2)

    # Euclidean distance, with Y != X.
    Y = rng.random_sample((2, 4))
    S = pairwise_distances(X, Y, metric="euclidean")
    S2 = euclidean_distances(X, Y)
    assert_array_almost_equal(S, S2)

    # Test with tuples as X and Y
    X_tuples = tuple([tuple([v for v in row]) for row in X])
    Y_tuples = tuple([tuple([v for v in row]) for row in Y])
    S2 = pairwise_distances(X_tuples, Y_tuples, metric="euclidean")
    assert_array_almost_equal(S, S2)

    # Test haversine distance
    # The data should be valid latitude and longitude
    X = rng.random_sample((5, 2))
    X[:, 0] = (X[:, 0] - 0.5) * 2 * np.pi/2
    X[:, 1] = (X[:, 1] - 0.5) * 2 * np.pi
    S = pairwise_distances(X, metric="haversine")
    S2 = haversine_distances(X)
    assert_array_almost_equal(S, S2)

    # Test haversine distance, with Y != X
    Y = rng.random_sample((2, 2))
    Y[:, 0] = (Y[:, 0] - 0.5)*2*np.pi/2
    Y[:, 1] = (Y[:, 1] - 0.5)*2*np.pi
    S = pairwise_distances(X, Y, metric="haversine")
    S2 = haversine_distances(X, Y)
    assert_array_almost_equal(S, S2)

    # "cityblock" uses scikit-learn metric, cityblock (function) is
    # scipy.spatial.
    S = pairwise_distances(X, metric="cityblock")
    S2 = pairwise_distances(X, metric=cityblock)
    assert S.shape[0] == S.shape[1]
    assert S.shape[0] == X.shape[0]
    assert_array_almost_equal(S, S2)

    # The manhattan metric should be equivalent to cityblock.
    S = pairwise_distances(X, Y, metric="manhattan")
    S2 = pairwise_distances(X, Y, metric=cityblock)
    assert S.shape[0] == X.shape[0]
    assert S.shape[1] == Y.shape[0]
    assert_array_almost_equal(S, S2)

    # Test cosine as a string metric versus cosine callable
    # The string "cosine" uses sklearn.metric,
    # while the function cosine is scipy.spatial
    S = pairwise_distances(X, Y, metric="cosine")
    S2 = pairwise_distances(X, Y, metric=cosine)
    assert S.shape[0] == X.shape[0]
    assert S.shape[1] == Y.shape[0]
    assert_array_almost_equal(S, S2)

    # Test with sparse X and Y,
    # currently only supported for Euclidean, L1 and cosine.
    X_sparse = csr_matrix(X)
    Y_sparse = csr_matrix(Y)
    S = pairwise_distances(X_sparse, Y_sparse, metric="euclidean")
    S2 = euclidean_distances(X_sparse, Y_sparse)
    assert_array_almost_equal(S, S2)
    S = pairwise_distances(X_sparse, Y_sparse, metric="cosine")
    S2 = cosine_distances(X_sparse, Y_sparse)
    assert_array_almost_equal(S, S2)
    S = pairwise_distances(X_sparse, Y_sparse.tocsc(), metric="manhattan")
    S2 = manhattan_distances(X_sparse.tobsr(), Y_sparse.tocoo())
    assert_array_almost_equal(S, S2)
    S2 = manhattan_distances(X, Y)
    assert_array_almost_equal(S, S2)

    # Test with scipy.spatial.distance metric, with a kwd
    kwds = {"p": 2.0}
    S = pairwise_distances(X, Y, metric="minkowski", **kwds)
    S2 = pairwise_distances(X, Y, metric=minkowski, **kwds)
    assert_array_almost_equal(S, S2)

    # same with Y = None
    kwds = {"p": 2.0}
    S = pairwise_distances(X, metric="minkowski", **kwds)
    S2 = pairwise_distances(X, metric=minkowski, **kwds)
    assert_array_almost_equal(S, S2)

    # Test that scipy distance metrics throw an error if sparse matrix given
    assert_raises(TypeError, pairwise_distances, X_sparse, metric="minkowski")
    assert_raises(TypeError, pairwise_distances, X, Y_sparse,
                  metric="minkowski")

    # Test that a value error is raised if the metric is unknown
    assert_raises(ValueError, pairwise_distances, X, Y, metric="blah")


@pytest.mark.parametrize('metric', PAIRWISE_BOOLEAN_FUNCTIONS)
def test_pairwise_boolean_distance(metric):
    # test that we convert to boolean arrays for boolean distances
    rng = np.random.RandomState(0)
    X = rng.randn(5, 4)
    Y = X.copy()
    Y[0, 0] = 1 - Y[0, 0]

    # ignore conversion to boolean in pairwise_distances
    with ignore_warnings(category=DataConversionWarning):
        for Z in [Y, None]:
            res = pairwise_distances(X, Z, metric=metric)
            res[np.isnan(res)] = 0
            assert np.sum(res != 0) == 0

    # non-boolean arrays are converted to boolean for boolean
    # distance metrics with a data conversion warning
    msg = "Data was converted to boolean for metric %s" % metric
    with pytest.warns(DataConversionWarning, match=msg):
        pairwise_distances(X, metric=metric)

    # Check that the warning is raised if X is boolean by Y is not boolean:
    with pytest.warns(DataConversionWarning, match=msg):
        pairwise_distances(X.astype(bool), Y=Y, metric=metric)

    # Check that no warning is raised if X is already boolean and Y is None:
    with pytest.warns(None) as records:
        pairwise_distances(X.astype(bool), metric=metric)
    assert len(records) == 0


def test_no_data_conversion_warning():
    # No warnings issued if metric is not a boolean distance function
    rng = np.random.RandomState(0)
    X = rng.randn(5, 4)
    with pytest.warns(None) as records:
        pairwise_distances(X, metric="minkowski")
    assert len(records) == 0


@pytest.mark.parametrize('func', [pairwise_distances, pairwise_kernels])
def test_pairwise_precomputed(func):
    # Test correct shape
    assert_raises_regexp(ValueError, '.* shape .*',
                         func, np.zeros((5, 3)), metric='precomputed')
    # with two args
    assert_raises_regexp(ValueError, '.* shape .*',
                         func, np.zeros((5, 3)), np.zeros((4, 4)),
                         metric='precomputed')
    # even if shape[1] agrees (although thus second arg is spurious)
    assert_raises_regexp(ValueError, '.* shape .*',
                         func, np.zeros((5, 3)), np.zeros((4, 3)),
                         metric='precomputed')

    # Test not copied (if appropriate dtype)
    S = np.zeros((5, 5))
    S2 = func(S, metric="precomputed")
    assert S is S2
    # with two args
    S = np.zeros((5, 3))
    S2 = func(S, np.zeros((3, 3)), metric="precomputed")
    assert S is S2

    # Test always returns float dtype
    S = func(np.array([[1]], dtype='int'), metric='precomputed')
    assert 'f' == S.dtype.kind

    # Test converts list to array-like
    S = func([[1.]], metric='precomputed')
    assert isinstance(S, np.ndarray)


def test_pairwise_precomputed_non_negative():
    # Test non-negative values
    assert_raises_regexp(ValueError, '.* non-negative values.*',
                         pairwise_distances, np.full((5, 5), -1),
                         metric='precomputed')


_wminkowski_kwds = {'w': np.arange(1, 5).astype('double', copy=False), 'p': 1}


def callable_rbf_kernel(x, y, **kwds):
    # Callable version of pairwise.rbf_kernel.
    K = rbf_kernel(np.atleast_2d(x), np.atleast_2d(y), **kwds)
    return K


@pytest.mark.parametrize(
        'func, metric, kwds',
        [(pairwise_distances, 'euclidean', {}),
         (pairwise_distances, wminkowski, _wminkowski_kwds),
         (pairwise_distances, 'wminkowski', _wminkowski_kwds),
         (pairwise_kernels, 'polynomial', {'degree': 1}),
         (pairwise_kernels, callable_rbf_kernel, {'gamma': .1})])
@pytest.mark.parametrize('array_constr', [np.array, csr_matrix])
@pytest.mark.parametrize('dtype', [np.float64, int])
def test_pairwise_parallel(func, metric, kwds, array_constr, dtype):
    rng = np.random.RandomState(0)
    X = array_constr(5 * rng.random_sample((5, 4)), dtype=dtype)
    Y = array_constr(5 * rng.random_sample((3, 4)), dtype=dtype)

    try:
        S = func(X, metric=metric, n_jobs=1, **kwds)
    except (TypeError, ValueError) as exc:
        # Not all metrics support sparse input
        # ValueError may be triggered by bad callable
        if array_constr is csr_matrix:
            with pytest.raises(type(exc)):
                func(X, metric=metric, n_jobs=2, **kwds)
            return
        else:
            raise
    S2 = func(X, metric=metric, n_jobs=2, **kwds)
    assert_allclose(S, S2)

    S = func(X, Y, metric=metric, n_jobs=1, **kwds)
    S2 = func(X, Y, metric=metric, n_jobs=2, **kwds)
    assert_allclose(S, S2)


def test_pairwise_callable_nonstrict_metric():
    # paired_distances should allow callable metric where metric(x, x) != 0
    # Knowing that the callable is a strict metric would allow the diagonal to
    # be left uncalculated and set to 0.
    assert pairwise_distances([[1.]], metric=lambda x, y: 5)[0, 0] == 5


# Test with all metrics that should be in PAIRWISE_KERNEL_FUNCTIONS.
@pytest.mark.parametrize(
        'metric',
        ["rbf", "laplacian", "sigmoid", "polynomial", "linear",
         "chi2", "additive_chi2"])
def test_pairwise_kernels(metric):
    # Test the pairwise_kernels helper function.

    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((2, 4))
    function = PAIRWISE_KERNEL_FUNCTIONS[metric]
    # Test with Y=None
    K1 = pairwise_kernels(X, metric=metric)
    K2 = function(X)
    assert_array_almost_equal(K1, K2)
    # Test with Y=Y
    K1 = pairwise_kernels(X, Y=Y, metric=metric)
    K2 = function(X, Y=Y)
    assert_array_almost_equal(K1, K2)
    # Test with tuples as X and Y
    X_tuples = tuple([tuple([v for v in row]) for row in X])
    Y_tuples = tuple([tuple([v for v in row]) for row in Y])
    K2 = pairwise_kernels(X_tuples, Y_tuples, metric=metric)
    assert_array_almost_equal(K1, K2)

    # Test with sparse X and Y
    X_sparse = csr_matrix(X)
    Y_sparse = csr_matrix(Y)
    if metric in ["chi2", "additive_chi2"]:
        # these don't support sparse matrices yet
        assert_raises(ValueError, pairwise_kernels,
                      X_sparse, Y=Y_sparse, metric=metric)
        return
    K1 = pairwise_kernels(X_sparse, Y=Y_sparse, metric=metric)
    assert_array_almost_equal(K1, K2)


def test_pairwise_kernels_callable():
    # Test the pairwise_kernels helper function
    # with a callable function, with given keywords.
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((2, 4))

    metric = callable_rbf_kernel
    kwds = {'gamma': 0.1}
    K1 = pairwise_kernels(X, Y=Y, metric=metric, **kwds)
    K2 = rbf_kernel(X, Y=Y, **kwds)
    assert_array_almost_equal(K1, K2)

    # callable function, X=Y
    K1 = pairwise_kernels(X, Y=X, metric=metric, **kwds)
    K2 = rbf_kernel(X, Y=X, **kwds)
    assert_array_almost_equal(K1, K2)


def test_pairwise_kernels_filter_param():
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((2, 4))
    K = rbf_kernel(X, Y, gamma=0.1)
    params = {"gamma": 0.1, "blabla": ":)"}
    K2 = pairwise_kernels(X, Y, metric="rbf", filter_params=True, **params)
    assert_array_almost_equal(K, K2)

    assert_raises(TypeError, pairwise_kernels, X, Y, "rbf", **params)


@pytest.mark.parametrize('metric, func', PAIRED_DISTANCES.items())
def test_paired_distances(metric, func):
    # Test the pairwise_distance helper function.
    rng = np.random.RandomState(0)
    # Euclidean distance should be equivalent to calling the function.
    X = rng.random_sample((5, 4))
    # Euclidean distance, with Y != X.
    Y = rng.random_sample((5, 4))

    S = paired_distances(X, Y, metric=metric)
    S2 = func(X, Y)
    assert_array_almost_equal(S, S2)
    S3 = func(csr_matrix(X), csr_matrix(Y))
    assert_array_almost_equal(S, S3)
    if metric in PAIRWISE_DISTANCE_FUNCTIONS:
        # Check the pairwise_distances implementation
        # gives the same value
        distances = PAIRWISE_DISTANCE_FUNCTIONS[metric](X, Y)
        distances = np.diag(distances)
        assert_array_almost_equal(distances, S)


def test_paired_distances_callable():
    # Test the pairwise_distance helper function
    # with the callable implementation
    rng = np.random.RandomState(0)
    # Euclidean distance should be equivalent to calling the function.
    X = rng.random_sample((5, 4))
    # Euclidean distance, with Y != X.
    Y = rng.random_sample((5, 4))

    S = paired_distances(X, Y, metric='manhattan')
    S2 = paired_distances(X, Y, metric=lambda x, y: np.abs(x - y).sum(axis=0))
    assert_array_almost_equal(S, S2)

    # Test that a value error is raised when the lengths of X and Y should not
    # differ
    Y = rng.random_sample((3, 4))
    assert_raises(ValueError, paired_distances, X, Y)


def test_pairwise_distances_argmin_min():
    # Check pairwise minimum distances computation for any metric
    X = [[0], [1]]
    Y = [[-2], [3]]

    Xsp = dok_matrix(X)
    Ysp = csr_matrix(Y, dtype=np.float32)

    expected_idx = [0, 1]
    expected_vals = [2, 2]
    expected_vals_sq = [4, 4]

    # euclidean metric
    idx, vals = pairwise_distances_argmin_min(X, Y, metric="euclidean")
    idx2 = pairwise_distances_argmin(X, Y, metric="euclidean")
    assert_array_almost_equal(idx, expected_idx)
    assert_array_almost_equal(idx2, expected_idx)
    assert_array_almost_equal(vals, expected_vals)
    # sparse matrix case
    idxsp, valssp = pairwise_distances_argmin_min(Xsp, Ysp, metric="euclidean")
    assert_array_almost_equal(idxsp, expected_idx)
    assert_array_almost_equal(valssp, expected_vals)
    # We don't want np.matrix here
    assert type(idxsp) == np.ndarray
    assert type(valssp) == np.ndarray

    # euclidean metric squared
    idx, vals = pairwise_distances_argmin_min(X, Y, metric="euclidean",
                                              metric_kwargs={"squared": True})
    assert_array_almost_equal(idx, expected_idx)
    assert_array_almost_equal(vals, expected_vals_sq)

    # Non-euclidean scikit-learn metric
    idx, vals = pairwise_distances_argmin_min(X, Y, metric="manhattan")
    idx2 = pairwise_distances_argmin(X, Y, metric="manhattan")
    assert_array_almost_equal(idx, expected_idx)
    assert_array_almost_equal(idx2, expected_idx)
    assert_array_almost_equal(vals, expected_vals)
    # sparse matrix case
    idxsp, valssp = pairwise_distances_argmin_min(Xsp, Ysp, metric="manhattan")
    assert_array_almost_equal(idxsp, expected_idx)
    assert_array_almost_equal(valssp, expected_vals)

    # Non-euclidean Scipy distance (callable)
    idx, vals = pairwise_distances_argmin_min(X, Y, metric=minkowski,
                                              metric_kwargs={"p": 2})
    assert_array_almost_equal(idx, expected_idx)
    assert_array_almost_equal(vals, expected_vals)

    # Non-euclidean Scipy distance (string)
    idx, vals = pairwise_distances_argmin_min(X, Y, metric="minkowski",
                                              metric_kwargs={"p": 2})
    assert_array_almost_equal(idx, expected_idx)
    assert_array_almost_equal(vals, expected_vals)

    # Compare with naive implementation
    rng = np.random.RandomState(0)
    X = rng.randn(97, 149)
    Y = rng.randn(111, 149)

    dist = pairwise_distances(X, Y, metric="manhattan")
    dist_orig_ind = dist.argmin(axis=0)
    dist_orig_val = dist[dist_orig_ind, range(len(dist_orig_ind))]

    dist_chunked_ind, dist_chunked_val = pairwise_distances_argmin_min(
        X, Y, axis=0, metric="manhattan")
    np.testing.assert_almost_equal(dist_orig_ind, dist_chunked_ind, decimal=7)
    np.testing.assert_almost_equal(dist_orig_val, dist_chunked_val, decimal=7)


def _reduce_func(dist, start):
    return dist[:, :100]


def test_pairwise_distances_chunked_reduce():
    rng = np.random.RandomState(0)
    X = rng.random_sample((400, 4))
    # Reduced Euclidean distance
    S = pairwise_distances(X)[:, :100]
    S_chunks = pairwise_distances_chunked(X, None, reduce_func=_reduce_func,
                                          working_memory=2 ** -16)
    assert isinstance(S_chunks, GeneratorType)
    S_chunks = list(S_chunks)
    assert len(S_chunks) > 1
    # atol is for diagonal where S is explicitly zeroed on the diagonal
    assert_allclose(np.vstack(S_chunks), S, atol=1e-7)


@pytest.mark.parametrize('good_reduce', [
    lambda D, start: list(D),
    lambda D, start: np.array(D),
    lambda D, start: csr_matrix(D),
    lambda D, start: (list(D), list(D)),
    lambda D, start: (dok_matrix(D), np.array(D), list(D)),
    ])
def test_pairwise_distances_chunked_reduce_valid(good_reduce):
    X = np.arange(10).reshape(-1, 1)
    S_chunks = pairwise_distances_chunked(X, None, reduce_func=good_reduce,
                                          working_memory=64)
    next(S_chunks)


@pytest.mark.parametrize(('bad_reduce', 'err_type', 'message'), [
    (lambda D, s: np.concatenate([D, D[-1:]]), ValueError,
     r'length 11\..* input: 10\.'),
    (lambda D, s: (D, np.concatenate([D, D[-1:]])), ValueError,
     r'length \(10, 11\)\..* input: 10\.'),
    (lambda D, s: (D[:9], D), ValueError,
     r'length \(9, 10\)\..* input: 10\.'),
    (lambda D, s: 7, TypeError,
     r'returned 7\. Expected sequence\(s\) of length 10\.'),
    (lambda D, s: (7, 8), TypeError,
     r'returned \(7, 8\)\. Expected sequence\(s\) of length 10\.'),
    (lambda D, s: (np.arange(10), 9), TypeError,
     r', 9\)\. Expected sequence\(s\) of length 10\.'),
])
def test_pairwise_distances_chunked_reduce_invalid(bad_reduce, err_type,
                                                   message):
    X = np.arange(10).reshape(-1, 1)
    S_chunks = pairwise_distances_chunked(X, None, reduce_func=bad_reduce,
                                          working_memory=64)
    assert_raises_regexp(err_type, message, next, S_chunks)


def check_pairwise_distances_chunked(X, Y, working_memory, metric='euclidean'):
    gen = pairwise_distances_chunked(X, Y, working_memory=working_memory,
                                     metric=metric)
    assert isinstance(gen, GeneratorType)
    blockwise_distances = list(gen)
    Y = X if Y is None else Y
    min_block_mib = len(Y) * 8 * 2 ** -20

    for block in blockwise_distances:
        memory_used = block.nbytes
        assert memory_used <= max(working_memory, min_block_mib) * 2 ** 20

    blockwise_distances = np.vstack(blockwise_distances)
    S = pairwise_distances(X, Y, metric=metric)
    assert_array_almost_equal(blockwise_distances, S)


@pytest.mark.parametrize(
        'metric',
        ('euclidean', 'l2', 'sqeuclidean'))
def test_pairwise_distances_chunked_diagonal(metric):
    rng = np.random.RandomState(0)
    X = rng.normal(size=(1000, 10), scale=1e10)
    chunks = list(pairwise_distances_chunked(X, working_memory=1,
                                             metric=metric))
    assert len(chunks) > 1
    assert_array_almost_equal(np.diag(np.vstack(chunks)), 0, decimal=10)


@pytest.mark.parametrize(
        'metric',
        ('euclidean', 'l2', 'sqeuclidean'))
def test_parallel_pairwise_distances_diagonal(metric):
    rng = np.random.RandomState(0)
    X = rng.normal(size=(1000, 10), scale=1e10)
    distances = pairwise_distances(X, metric=metric, n_jobs=2)
    assert_allclose(np.diag(distances), 0, atol=1e-10)


@ignore_warnings
def test_pairwise_distances_chunked():
    # Test the pairwise_distance helper function.
    rng = np.random.RandomState(0)
    # Euclidean distance should be equivalent to calling the function.
    X = rng.random_sample((200, 4))
    check_pairwise_distances_chunked(X, None, working_memory=1,
                                     metric='euclidean')
    # Test small amounts of memory
    for power in range(-16, 0):
        check_pairwise_distances_chunked(X, None, working_memory=2 ** power,
                                         metric='euclidean')
    # X as list
    check_pairwise_distances_chunked(X.tolist(), None, working_memory=1,
                                     metric='euclidean')
    # Euclidean distance, with Y != X.
    Y = rng.random_sample((100, 4))
    check_pairwise_distances_chunked(X, Y, working_memory=1,
                                     metric='euclidean')
    check_pairwise_distances_chunked(X.tolist(), Y.tolist(), working_memory=1,
                                     metric='euclidean')
    # absurdly large working_memory
    check_pairwise_distances_chunked(X, Y, working_memory=10000,
                                     metric='euclidean')
    # "cityblock" uses scikit-learn metric, cityblock (function) is
    # scipy.spatial.
    check_pairwise_distances_chunked(X, Y, working_memory=1,
                                     metric='cityblock')
    # Test that a value error is raised if the metric is unknown
    assert_raises(ValueError, next,
                  pairwise_distances_chunked(X, Y, metric="blah"))

    # Test precomputed returns all at once
    D = pairwise_distances(X)
    gen = pairwise_distances_chunked(D,
                                     working_memory=2 ** -16,
                                     metric='precomputed')
    assert isinstance(gen, GeneratorType)
    assert next(gen) is D
    assert_raises(StopIteration, next, gen)


def test_euclidean_distances():
    # Check the pairwise Euclidean distances computation
    X = [[0]]
    Y = [[1], [2]]
    D = euclidean_distances(X, Y)
    assert_array_almost_equal(D, [[1., 2.]])

    X = csr_matrix(X)
    Y = csr_matrix(Y)
    D = euclidean_distances(X, Y)
    assert_array_almost_equal(D, [[1., 2.]])

    rng = np.random.RandomState(0)
    X = rng.random_sample((10, 4))
    Y = rng.random_sample((20, 4))
    X_norm_sq = (X ** 2).sum(axis=1).reshape(1, -1)
    Y_norm_sq = (Y ** 2).sum(axis=1).reshape(1, -1)

    # check that we still get the right answers with {X,Y}_norm_squared
    D1 = euclidean_distances(X, Y)
    D2 = euclidean_distances(X, Y, X_norm_squared=X_norm_sq)
    D3 = euclidean_distances(X, Y, Y_norm_squared=Y_norm_sq)
    D4 = euclidean_distances(X, Y, X_norm_squared=X_norm_sq,
                             Y_norm_squared=Y_norm_sq)
    assert_array_almost_equal(D2, D1)
    assert_array_almost_equal(D3, D1)
    assert_array_almost_equal(D4, D1)

    # check we get the wrong answer with wrong {X,Y}_norm_squared
    X_norm_sq *= 0.5
    Y_norm_sq *= 0.5
    wrong_D = euclidean_distances(X, Y,
                                  X_norm_squared=np.zeros_like(X_norm_sq),
                                  Y_norm_squared=np.zeros_like(Y_norm_sq))
    with pytest.raises(AssertionError):
        assert_allclose(wrong_D, D1)


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
@pytest.mark.parametrize("x_array_constr", [np.array, csr_matrix],
                         ids=["dense", "sparse"])
@pytest.mark.parametrize("y_array_constr", [np.array, csr_matrix],
                         ids=["dense", "sparse"])
def test_euclidean_distances(dtype, x_array_constr, y_array_constr):
    # check that euclidean distances gives same result as scipy cdist
    # when X and Y != X are provided
    rng = np.random.RandomState(0)
    X = rng.random_sample((100, 10)).astype(dtype, copy=False)
    X[X < 0.8] = 0
    Y = rng.random_sample((10, 10)).astype(dtype, copy=False)
    Y[Y < 0.8] = 0

    expected = cdist(X, Y)

    X = x_array_constr(X)
    Y = y_array_constr(Y)
    distances = euclidean_distances(X, Y)

    # the default rtol=1e-7 is too close to the float32 precision
    # and fails due too rounding errors.
    assert_allclose(distances, expected, rtol=1e-6)
    assert distances.dtype == dtype


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
@pytest.mark.parametrize("x_array_constr", [np.array, csr_matrix],
                         ids=["dense", "sparse"])
def test_euclidean_distances_sym(dtype, x_array_constr):
    # check that euclidean distances gives same result as scipy pdist
    # when only X is provided
    rng = np.random.RandomState(0)
    X = rng.random_sample((100, 10)).astype(dtype, copy=False)
    X[X < 0.8] = 0

    expected = squareform(pdist(X))

    X = x_array_constr(X)
    distances = euclidean_distances(X)

    # the default rtol=1e-7 is too close to the float32 precision
    # and fails due too rounding errors.
    assert_allclose(distances, expected, rtol=1e-6)
    assert distances.dtype == dtype


@pytest.mark.parametrize("batch_size", [None, 5, 7, 101])
@pytest.mark.parametrize("x_array_constr", [np.array, csr_matrix],
                         ids=["dense", "sparse"])
@pytest.mark.parametrize("y_array_constr", [np.array, csr_matrix],
                         ids=["dense", "sparse"])
def test_euclidean_distances_upcast(batch_size, x_array_constr,
                                    y_array_constr):
    # check batches handling when Y != X (#13910)
    rng = np.random.RandomState(0)
    X = rng.random_sample((100, 10)).astype(np.float32)
    X[X < 0.8] = 0
    Y = rng.random_sample((10, 10)).astype(np.float32)
    Y[Y < 0.8] = 0

    expected = cdist(X, Y)

    X = x_array_constr(X)
    Y = y_array_constr(Y)
    distances = _euclidean_distances_upcast(X, Y=Y, batch_size=batch_size)
    distances = np.sqrt(np.maximum(distances, 0))

    # the default rtol=1e-7 is too close to the float32 precision
    # and fails due too rounding errors.
    assert_allclose(distances, expected, rtol=1e-6)


@pytest.mark.parametrize("batch_size", [None, 5, 7, 101])
@pytest.mark.parametrize("x_array_constr", [np.array, csr_matrix],
                         ids=["dense", "sparse"])
def test_euclidean_distances_upcast_sym(batch_size, x_array_constr):
    # check batches handling when X is Y (#13910)
    rng = np.random.RandomState(0)
    X = rng.random_sample((100, 10)).astype(np.float32)
    X[X < 0.8] = 0

    expected = squareform(pdist(X))

    X = x_array_constr(X)
    distances = _euclidean_distances_upcast(X, Y=X, batch_size=batch_size)
    distances = np.sqrt(np.maximum(distances, 0))

    # the default rtol=1e-7 is too close to the float32 precision
    # and fails due too rounding errors.
    assert_allclose(distances, expected, rtol=1e-6)


@pytest.mark.parametrize(
    "dtype, eps, rtol",
    [(np.float32, 1e-4, 1e-5),
     pytest.param(
         np.float64, 1e-8, 0.99,
         marks=pytest.mark.xfail(reason='failing due to lack of precision'))])
@pytest.mark.parametrize("dim", [1, 1000000])
def test_euclidean_distances_extreme_values(dtype, eps, rtol, dim):
    # check that euclidean distances is correct with float32 input thanks to
    # upcasting. On float64 there are still precision issues.
    X = np.array([[1.] * dim], dtype=dtype)
    Y = np.array([[1. + eps] * dim], dtype=dtype)

    distances = euclidean_distances(X, Y)
    expected = cdist(X, Y)

    assert_allclose(distances, expected, rtol=1e-5)


def test_cosine_distances():
    # Check the pairwise Cosine distances computation
    rng = np.random.RandomState(1337)
    x = np.abs(rng.rand(910))
    XA = np.vstack([x, x])
    D = cosine_distances(XA)
    assert_array_almost_equal(D, [[0., 0.], [0., 0.]])
    # check that all elements are in [0, 2]
    assert np.all(D >= 0.)
    assert np.all(D <= 2.)
    # check that diagonal elements are equal to 0
    assert_array_almost_equal(D[np.diag_indices_from(D)], [0., 0.])

    XB = np.vstack([x, -x])
    D2 = cosine_distances(XB)
    # check that all elements are in [0, 2]
    assert np.all(D2 >= 0.)
    assert np.all(D2 <= 2.)
    # check that diagonal elements are equal to 0 and non diagonal to 2
    assert_array_almost_equal(D2, [[0., 2.], [2., 0.]])

    # check large random matrix
    X = np.abs(rng.rand(1000, 5000))
    D = cosine_distances(X)
    # check that diagonal elements are equal to 0
    assert_array_almost_equal(D[np.diag_indices_from(D)], [0.] * D.shape[0])
    assert np.all(D >= 0.)
    assert np.all(D <= 2.)


def test_gower_distances():
    # Test the pairwise Gower distances computation.
    # For each test, a set of (non optmized) simple python commands is
    # provided, to explain how those expected values are calculated,
    # and to provide proofs that the expected values are correct.
    #
    # The calculation formula for Gower similarity is available in the
    # user guide.

    with pytest.raises(TypeError):
        gower_distances(csr_matrix((2, 2)))
    with pytest.raises(ValueError):
        gower_distances(None)

    X = [['M', False, 222.22, 1],
         ['F', True, 333.22, 2],
         ['M', True, 1934.0, 4],
         [np.nan, np.nan, np.nan, np.nan]]

    with pytest.raises(TypeError):
        gower_distances(X, scale=1)

    with pytest.raises(ValueError):
        gower_distances(X, scale=[1])

    # No errors are expected to be raised here
    D = gower_distances(X, scale=[np.nan, np.nan])
    D = gower_distances(X, scale=np.array([1, 1]))

    D = gower_distances(X)

    # These are the normalized values for X above
    X = [['M', False, 0.0, 0.0],
         ['F', True, 0.06484477, 0.33333333],
         ['M', True, 1.0, 1.0],
         [np.nan, np.nan, np.nan, np.nan]]

    # Simplified calculation of Gower distance for expected values
    # This represents the number of non missing cols for each X, Y line
    non_missing_cols = [4, 4, 4, 0]
    D_expected = np.zeros((4, 4))
    for i in range(0, 4):
        for j in range(0, 4):
            # The calculations below shows how it compares observation
            # by observation, attribute by attribute.
            sum = ([1, 0][X[i][0] == X[j][0]] +
                   [1, 0][X[i][1] == X[j][1]] +
                   abs(X[i][2] - X[j][2]) +
                   abs(X[i][3] - X[j][3]))

            D_expected[i][j] = np.divide(sum, non_missing_cols[j],
                                         out=np.array([np.nan]),
                                         where=(non_missing_cols[j] != 0)
                                                & (non_missing_cols[i] != 0))

    assert_array_almost_equal(D_expected, D)

    # Calculates D with normalization, then results must be the same without
    # normalization
    assert_array_almost_equal(D, gower_distances(X, scale=False))

    # The values must be the same, when using the categorical_values
    # parameter
    D = gower_distances(X, categorical_features=[0, 1])

    assert_array_almost_equal(D_expected, D)

    D = gower_distances(X, categorical_features=[0, 1, 3])

    # These are the normalized values for the initial X above,
    # but the last column became categorical.
    X = [['M', False, 0.0, 1],
         ['F', True, 0.06484477, 2],
         ['M', True, 1.0, 4],
         [np.nan, np.nan, np.nan, np.nan]]

    # Simplified calculation of Gower distance for expected values
    # This represents the number of non missing cols for each X, Y line
    non_missing_cols = [4, 4, 4, 0]
    D_expected = np.zeros((4, 4))
    for i in range(0, 4):
        for j in range(0, 4):
            sum = ([1, 0][X[i][0] == X[j][0]] +
                   [1, 0][X[i][1] == X[j][1]] +
                   abs(X[i][2] - X[j][2]) +
                   [1, 0][X[i][3] == X[j][3]])

            D_expected[i][j] = np.divide(sum, non_missing_cols[j],
                                         out=np.array([np.nan]),
                                         where=(non_missing_cols[j] != 0)
                                                & (non_missing_cols[i] != 0))

    D = gower_distances(X, categorical_features=[True, True, False, True],
                        scale=False)

    assert_array_almost_equal(D_expected, D)

    # Two observations with same value
    X = [[1, 4141.22, False, 'ABC'],
         [1, 4141.22, False, 'ABC']]

    D = gower_distances(X)
    D_expected = [[0.0, 0.0], [0.0, 0.0]]
    # An array of zeros is expected as distance, when comparing two
    # observations with same values.
    assert_array_almost_equal(D_expected, D)

    # Only categorical values
    X = [['M', False],
         ['F', True],
         ['M', True],
         ['F', False]]

    X = np.array(X, dtype=np.object)

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((4, 4))
    for i in range(0, 4):
        for j in range(0, 4):
            D_expected[i][j] = ([1, 0][X[i][0] == X[j][0]] +
                                [1, 0][X[i][1] == X[j][1]]) / 2

    D = gower_distances(X)

    assert_array_almost_equal(D_expected, D)

    # Gower results for categorical values must be similar to Hamming.
    # It is necessary to digest it for current Hamming implementation.
    X = np.asarray(X, dtype=np.object)
    np.place(X[:, 0], X[:, 0] == 'M', 0)
    np.place(X[:, 0], X[:, 0] == 'F', 1)
    X = X.astype(np.int)

    assert_array_almost_equal(D, pairwise_distances(X, metric="hamming"))

    # Categorical values, with boolean represented as number 1,0
    X = [['M', 0],
         ['F', 1],
         ['M', 1],
         ['F', 0]]

    D = gower_distances(X, categorical_features=[True, True])

    assert_array_almost_equal(D_expected, D)

    # Categorical values, with boolean represented as 1 and 0,
    # and missing values
    X = [['M', 0],
         ['F', 1],
         ['M', 1],
         [np.nan, np.nan]]

    D = gower_distances(X, categorical_features=[True, True])

    D_expected = np.zeros((4, 4))
    # This represents the number of non missing cols for each X, Y line
    non_missing_cols = [2, 2, 2, 0]
    for i in range(0, 4):
        for j in range(0, 4):
            sum = ([1, 0][X[i][0] == X[j][0]] +
                   [1, 0][X[i][1] == X[j][1]])

            D_expected[i][j] = np.divide(sum, non_missing_cols[j],
                                         out=np.array([np.nan]),
                                         where=(non_missing_cols[j] != 0)
                                                & (non_missing_cols[i] != 0))

    assert_array_almost_equal(D_expected, D)

    # Tests numeric arrays with np.nan
    X = [[0.0, 0.0],
         [0.06484477, 0.33333333],
         [1.0, 1.0],
         [np.nan, np.nan]]

    D = gower_distances(X)

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((4, 4))
    # This represents the number of non missing cols for each X, Y line
    non_missing_cols = [2, 2, 2, 0]
    for i in range(0, 4):
        for j in range(0, 4):
            sum = abs(X[i][0] - X[j][0]) + abs(X[i][1] - X[j][1])
            D_expected[i][j] = np.divide(sum, non_missing_cols[i],
                                         out=np.array([np.nan]),
                                         where=non_missing_cols[i] != 0)

    assert_array_almost_equal(D_expected, D)

    # Tests only numeric arrays, no missing values
    X = [[0.11444388, 0.0],
         [0.17186758, 0.33333334],
         [1.0, 1.0],
         [0.0, 0.0]]

    D = gower_distances(X)

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((4, 4))
    for i in range(0, 4):
        for j in range(0, 4):
            D_expected[i][j] = (abs(X[i][0] - X[j][0]) +
                                abs(X[i][1] - X[j][1])) / 2

    assert_array_almost_equal(D_expected, D)

    # Gower results for numerical values must be similar to Manhattan.
    assert_array_almost_equal(D * 2, manhattan_distances(X))

    # Test to obtain a non-squared distance matrix
    X = np.array([['Syria', 1.0, 0.0, 0.0, True],
                  ['Ireland', 0.181818, 0.0, 1, False],
                  ['United Kingdom', 0.0, 0.0, 0.160377, False]],
                 dtype=object)

    Y = np.array([['United Kingdom', 0.090909, 0.0, 0.500109, True]],
                 dtype=object)

    D = gower_distances(X, Y)

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((3, 1))
    for i in range(0, 3):
        for j in range(0, 1):
            D_expected[i][j] = \
                ([1, 0][X[i][0] == Y[j][0]] +
                 abs(X[i][1] - Y[j][1]) +
                 abs(X[i][2] - Y[j][2]) +
                 abs(X[i][3] - Y[j][3]) +
                 [1, 0][X[i][4] == Y[j][4]]) / 5

    assert_array_almost_equal(D_expected, D)

    # Test to obtain a non-squared distance matrix with numeric data only
    X = np.array([[1.0, 0.0, 0.0],
                  [0.181818, 0.0, 1],
                  [0.0, 0.0, 0.160377]],
                 dtype=object)

    Y = np.array([[0.090909, 0.0, 0.500109]], dtype=object)
    D = gower_distances(X, Y)

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((3, 1))
    for i in range(0, 3):
        for j in range(0, 1):
            D_expected[i][j] = \
                (abs(X[i][0] - Y[j][0]) +
                 abs(X[i][1] - Y[j][1]) +
                 abs(X[i][2] - Y[j][2])) / 3

    assert_array_almost_equal(D_expected, D)

    # Tests a range of negative and positive numeric values
    # Range starting with zero
    X = np.array([[0.0], [0.75], [1.0]])

    D = gower_distances(X)

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((3, 3))
    for i in range(0, 3):
        for j in range(0, 3):
            D_expected[i][j] = (abs(X[i][0] - X[j][0])) / 1

    assert_array_almost_equal(D_expected, D)

    # Range of positive and negative values
    X = X - 0.5
    D = gower_distances(X)
    assert_array_almost_equal(D_expected, D)

    # Range with positive values
    X = X + 10
    D = gower_distances(X)
    assert_array_almost_equal(D_expected, D)

    # Range of negative values
    X = X - 15
    D = gower_distances(X)
    assert_array_almost_equal(D_expected, D)

    # Test warnings for unexpected non-normalized data
    X = [[1, 20], [0, -10.0]]
    with pytest.raises(ValueError):
        gower_distances(X, scale=False)

    # Test X and Y with diferent ranges of numeric values
    X = [[9222.22, -11],
         [41934.0, -44],
         [1, 1]]

    Y = [[-222.22, 1],
         [1934.0, 4],
         [3000, 3000]]

    D = gower_distances(X, Y)

    # The expected normalized values above are:
    Xn = [[0.22403432, 0.010841],
          [1.0, 0.0],
          [0.00529507, 0.01478318]]

    Yn = [[0.0, 0.01478318],
          [0.05114832, 0.01576873],
          [0.07643522, 1.0]]

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((3, 3))
    for i in range(0, 3):
        for j in range(0, 3):
            D_expected[i][j] = (abs(Xn[i][0] - Yn[j][0]) +
                                abs(Xn[i][1] - Yn[j][1])) / 2

    assert_array_almost_equal(D_expected, D)
    # Test the use of range parameters
    D = gower_distances(X, Y, scale=[42156.22, 3044.0])
    assert_array_almost_equal(D_expected, D)
    # same without scale, as long the entire data is present
    D = gower_distances(X, Y)
    assert_array_almost_equal(D_expected, D)

    # Test gower robustness after slice the data, with its original ranges
    D = gower_distances(X, Y[1:2],  scale=[42156.22, 3044.0])
    assert_array_almost_equal(D_expected[:, 1:2], D)

    # an assertion error is expected here, because there is no scale
    D = gower_distances(X, Y[1:2])
    with pytest.raises(AssertionError):
        assert_array_almost_equal(D_expected[:, 1:2], D)

    D = gower_distances(X, Y[0:1], scale=[42156.22, 3044.0])
    assert_array_almost_equal(D_expected[:, 0:1], D)

    # an assertion error is expected here, because there is no scale
    D = gower_distances(X, Y[0:1])
    with pytest.raises(AssertionError):
        assert_array_almost_equal(D_expected[:, 0:1], D)

    # Test gower under pairwise_distances
    D = pairwise_distances(X, Y, metric='gower', n_jobs=2)
    assert_array_almost_equal(D_expected, D)

    # Test X and Y with diferent ranges of numeric values, categorical values,
    # and using pairwise_distances
    X = [[9222.22, -11, 'M', 1],
         [41934.0, -44, 'F', 1],
         [1, 1, np.nan, 0]]

    Y = [[-222.22, 1, 'F', 0],
         [1934.0, 4, 'M', 0],
         [3000, 3000, 'F', 0]]

    # The expected normalized values above are:
    Xn = [[0.22403432, 0.010841, 'M', 1],
          [1.0, 0.0, 'F', 1],
          [0.00529507, 0.01478318, np.nan, 0]]

    Yn = [[0.0, 0.01478318, 'F', 0],
          [0.05114832, 0.01576873, 'M', 0],
          [0.07643522, 1.0, 'F', 0]]

    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((3, 3))
    # This represents the number of non missing cols for each X, Y line
    non_missing_cols = [4, 4, 3]

    for i in range(0, 3):
        for j in range(0, 3):
            # The calculations below shows how it compares observation
            # by observation, attribute by attribute.
            D_expected[i][j] = ((abs(Xn[i][0] - Yn[j][0]) +
                                 abs(Xn[i][1] - Yn[j][1]) +
                                 [1, 0][Xn[i][2] == Yn[j][2]] +
                                 abs(Xn[i][3] - Yn[j][3])) /
                                 non_missing_cols[i])

    D = pairwise_distances(X, Y, metric='gower', n_jobs=2)
    assert_array_almost_equal(D_expected, D)

    # Test categorical_values passed in kwargs
    # Simplified calculation of Gower distance for expected values
    D_expected = np.zeros((3, 3))
    for i in range(0, 3):
        for j in range(0, 3):
            # The calculations below shows how it compares observation
            # by observation, attribute by attribute.
            D_expected[i][j] = ((abs(Xn[i][0] - Yn[j][0]) +
                                 abs(Xn[i][1] - Yn[j][1]) +
                                 [1, 0][Xn[i][2] == Yn[j][2]] +
                                 [1, 0][Xn[i][3] == Yn[j][3]]) /
                                 non_missing_cols[i])

    D = pairwise_distances(X, Y, metric='gower', n_jobs=2,
                           categorical_features=[False, False, True, True])

    assert_array_almost_equal(D_expected, D)

    X = np.random.randn(1000).reshape(200, -1) * 10
    X = np.append(X, np.random.randn(1000).reshape(200, -1) * 10000, axis=1)

    D_expected = gower_distances(X)
    D = pairwise_distances(X, metric='gower', n_jobs=2)
    assert_array_almost_equal(D_expected, D)

    D_expected = pairwise_distances(X, metric='gower')
    D = pairwise_distances(X, metric='gower', n_jobs=2)
    assert_array_almost_equal(D_expected, D)

    X = [[np.nan, np.nan], [np.nan, np.nan]]
    D = gower_distances(X)
    assert_array_almost_equal(X, D)

    X = np.random.normal(size=(10, 5)) * 10
    Y = np.random.normal(size=(10, 5)) * 100
    D = pairwise_distances(X, Y, metric='gower', n_jobs=2)
    D_expected = gower_distances(X, Y)
    assert_array_almost_equal(D_expected, D)

    # test if method is "division by zero" proof
    X = [[0, 0], [0, 0]]
    D = gower_distances(X)
    assert_array_almost_equal(X, D)
    D = gower_distances(X, scale=[0, 0])
    assert_array_almost_equal(X, D)


def test_haversine_distances():
    # Check haversine distance with distances computation
    def slow_haversine_distances(x, y):
        diff_lat = y[0] - x[0]
        diff_lon = y[1] - x[1]
        a = np.sin(diff_lat / 2) ** 2 + (
            np.cos(x[0]) * np.cos(y[0]) * np.sin(diff_lon/2) ** 2
        )
        c = 2 * np.arcsin(np.sqrt(a))
        return c
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 2))
    Y = rng.random_sample((10, 2))
    D1 = np.array([[slow_haversine_distances(x, y) for y in Y] for x in X])
    D2 = haversine_distances(X, Y)
    assert_array_almost_equal(D1, D2)
    # Test haversine distance does not accept X where n_feature != 2
    X = rng.random_sample((10, 3))
    assert_raise_message(ValueError,
                         "Haversine distance only valid in 2 dimensions",
                         haversine_distances, X)



# Paired distances

def test_paired_euclidean_distances():
    # Check the paired Euclidean distances computation
    X = [[0], [0]]
    Y = [[1], [2]]
    D = paired_euclidean_distances(X, Y)
    assert_array_almost_equal(D, [1., 2.])


def test_paired_manhattan_distances():
    # Check the paired manhattan distances computation
    X = [[0], [0]]
    Y = [[1], [2]]
    D = paired_manhattan_distances(X, Y)
    assert_array_almost_equal(D, [1., 2.])


def test_chi_square_kernel():
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((10, 4))
    K_add = additive_chi2_kernel(X, Y)
    gamma = 0.1
    K = chi2_kernel(X, Y, gamma=gamma)
    assert K.dtype == np.float
    for i, x in enumerate(X):
        for j, y in enumerate(Y):
            chi2 = -np.sum((x - y) ** 2 / (x + y))
            chi2_exp = np.exp(gamma * chi2)
            assert_almost_equal(K_add[i, j], chi2)
            assert_almost_equal(K[i, j], chi2_exp)

    # check diagonal is ones for data with itself
    K = chi2_kernel(Y)
    assert_array_equal(np.diag(K), 1)
    # check off-diagonal is < 1 but > 0:
    assert np.all(K > 0)
    assert np.all(K - np.diag(np.diag(K)) < 1)
    # check that float32 is preserved
    X = rng.random_sample((5, 4)).astype(np.float32)
    Y = rng.random_sample((10, 4)).astype(np.float32)
    K = chi2_kernel(X, Y)
    assert K.dtype == np.float32

    # check integer type gets converted,
    # check that zeros are handled
    X = rng.random_sample((10, 4)).astype(np.int32)
    K = chi2_kernel(X, X)
    assert np.isfinite(K).all()
    assert K.dtype == np.float

    # check that kernel of similar things is greater than dissimilar ones
    X = [[.3, .7], [1., 0]]
    Y = [[0, 1], [.9, .1]]
    K = chi2_kernel(X, Y)
    assert K[0, 0] > K[0, 1]
    assert K[1, 1] > K[1, 0]

    # test negative input
    assert_raises(ValueError, chi2_kernel, [[0, -1]])
    assert_raises(ValueError, chi2_kernel, [[0, -1]], [[-1, -1]])
    assert_raises(ValueError, chi2_kernel, [[0, 1]], [[-1, -1]])

    # different n_features in X and Y
    assert_raises(ValueError, chi2_kernel, [[0, 1]], [[.2, .2, .6]])

    # sparse matrices
    assert_raises(ValueError, chi2_kernel, csr_matrix(X), csr_matrix(Y))
    assert_raises(ValueError, additive_chi2_kernel,
                  csr_matrix(X), csr_matrix(Y))


@pytest.mark.parametrize(
        'kernel',
        (linear_kernel, polynomial_kernel, rbf_kernel,
         laplacian_kernel, sigmoid_kernel, cosine_similarity))
def test_kernel_symmetry(kernel):
    # Valid kernels should be symmetric
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    K = kernel(X, X)
    assert_array_almost_equal(K, K.T, 15)


@pytest.mark.parametrize(
        'kernel',
        (linear_kernel, polynomial_kernel, rbf_kernel,
         laplacian_kernel, sigmoid_kernel, cosine_similarity))
def test_kernel_sparse(kernel):
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    X_sparse = csr_matrix(X)
    K = kernel(X, X)
    K2 = kernel(X_sparse, X_sparse)
    assert_array_almost_equal(K, K2)


def test_linear_kernel():
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    K = linear_kernel(X, X)
    # the diagonal elements of a linear kernel are their squared norm
    assert_array_almost_equal(K.flat[::6], [linalg.norm(x) ** 2 for x in X])


def test_rbf_kernel():
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    K = rbf_kernel(X, X)
    # the diagonal elements of a rbf kernel are 1
    assert_array_almost_equal(K.flat[::6], np.ones(5))


def test_laplacian_kernel():
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    K = laplacian_kernel(X, X)
    # the diagonal elements of a laplacian kernel are 1
    assert_array_almost_equal(np.diag(K), np.ones(5))

    # off-diagonal elements are < 1 but > 0:
    assert np.all(K > 0)
    assert np.all(K - np.diag(np.diag(K)) < 1)


@pytest.mark.parametrize('metric, pairwise_func',
                         [('linear', linear_kernel),
                          ('cosine', cosine_similarity)])
def test_pairwise_similarity_sparse_output(metric, pairwise_func):
    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((3, 4))
    Xcsr = csr_matrix(X)
    Ycsr = csr_matrix(Y)

    # should be sparse
    K1 = pairwise_func(Xcsr, Ycsr, dense_output=False)
    assert issparse(K1)

    # should be dense, and equal to K1
    K2 = pairwise_func(X, Y, dense_output=True)
    assert not issparse(K2)
    assert_array_almost_equal(K1.todense(), K2)

    # show the kernel output equal to the sparse.todense()
    K3 = pairwise_kernels(X, Y=Y, metric=metric)
    assert_array_almost_equal(K1.todense(), K3)


def test_cosine_similarity():
    # Test the cosine_similarity.

    rng = np.random.RandomState(0)
    X = rng.random_sample((5, 4))
    Y = rng.random_sample((3, 4))
    Xcsr = csr_matrix(X)
    Ycsr = csr_matrix(Y)

    for X_, Y_ in ((X, None), (X, Y),
                   (Xcsr, None), (Xcsr, Ycsr)):
        # Test that the cosine is kernel is equal to a linear kernel when data
        # has been previously normalized by L2-norm.
        K1 = pairwise_kernels(X_, Y=Y_, metric="cosine")
        X_ = normalize(X_)
        if Y_ is not None:
            Y_ = normalize(Y_)
        K2 = pairwise_kernels(X_, Y=Y_, metric="linear")
        assert_array_almost_equal(K1, K2)


def test_check_dense_matrices():
    # Ensure that pairwise array check works for dense matrices.
    # Check that if XB is None, XB is returned as reference to XA
    XA = np.resize(np.arange(40), (5, 8))
    XA_checked, XB_checked = check_pairwise_arrays(XA, None)
    assert XA_checked is XB_checked
    assert_array_equal(XA, XA_checked)


def test_check_XB_returned():
    # Ensure that if XA and XB are given correctly, they return as equal.
    # Check that if XB is not None, it is returned equal.
    # Note that the second dimension of XB is the same as XA.
    XA = np.resize(np.arange(40), (5, 8))
    XB = np.resize(np.arange(32), (4, 8))
    XA_checked, XB_checked = check_pairwise_arrays(XA, XB)
    assert_array_equal(XA, XA_checked)
    assert_array_equal(XB, XB_checked)

    XB = np.resize(np.arange(40), (5, 8))
    XA_checked, XB_checked = check_paired_arrays(XA, XB)
    assert_array_equal(XA, XA_checked)
    assert_array_equal(XB, XB_checked)


def test_check_different_dimensions():
    # Ensure an error is raised if the dimensions are different.
    XA = np.resize(np.arange(45), (5, 9))
    XB = np.resize(np.arange(32), (4, 8))
    assert_raises(ValueError, check_pairwise_arrays, XA, XB)

    XB = np.resize(np.arange(4 * 9), (4, 9))
    assert_raises(ValueError, check_paired_arrays, XA, XB)


def test_check_invalid_dimensions():
    # Ensure an error is raised on 1D input arrays.
    # The modified tests are not 1D. In the old test, the array was internally
    # converted to 2D anyways
    XA = np.arange(45).reshape(9, 5)
    XB = np.arange(32).reshape(4, 8)
    assert_raises(ValueError, check_pairwise_arrays, XA, XB)
    XA = np.arange(45).reshape(9, 5)
    XB = np.arange(32).reshape(4, 8)
    assert_raises(ValueError, check_pairwise_arrays, XA, XB)


def test_check_sparse_arrays():
    # Ensures that checks return valid sparse matrices.
    rng = np.random.RandomState(0)
    XA = rng.random_sample((5, 4))
    XA_sparse = csr_matrix(XA)
    XB = rng.random_sample((5, 4))
    XB_sparse = csr_matrix(XB)
    XA_checked, XB_checked = check_pairwise_arrays(XA_sparse, XB_sparse)
    # compare their difference because testing csr matrices for
    # equality with '==' does not work as expected.
    assert issparse(XA_checked)
    assert abs(XA_sparse - XA_checked).sum() == 0
    assert issparse(XB_checked)
    assert abs(XB_sparse - XB_checked).sum() == 0

    XA_checked, XA_2_checked = check_pairwise_arrays(XA_sparse, XA_sparse)
    assert issparse(XA_checked)
    assert abs(XA_sparse - XA_checked).sum() == 0
    assert issparse(XA_2_checked)
    assert abs(XA_2_checked - XA_checked).sum() == 0


def tuplify(X):
    # Turns a numpy matrix (any n-dimensional array) into tuples.
    s = X.shape
    if len(s) > 1:
        # Tuplify each sub-array in the input.
        return tuple(tuplify(row) for row in X)
    else:
        # Single dimension input, just return tuple of contents.
        return tuple(r for r in X)


def test_check_tuple_input():
    # Ensures that checks return valid tuples.
    rng = np.random.RandomState(0)
    XA = rng.random_sample((5, 4))
    XA_tuples = tuplify(XA)
    XB = rng.random_sample((5, 4))
    XB_tuples = tuplify(XB)
    XA_checked, XB_checked = check_pairwise_arrays(XA_tuples, XB_tuples)
    assert_array_equal(XA_tuples, XA_checked)
    assert_array_equal(XB_tuples, XB_checked)


def test_check_preserve_type():
    # Ensures that type float32 is preserved.
    XA = np.resize(np.arange(40), (5, 8)).astype(np.float32)
    XB = np.resize(np.arange(40), (5, 8)).astype(np.float32)

    XA_checked, XB_checked = check_pairwise_arrays(XA, None)
    assert XA_checked.dtype == np.float32

    # both float32
    XA_checked, XB_checked = check_pairwise_arrays(XA, XB)
    assert XA_checked.dtype == np.float32
    assert XB_checked.dtype == np.float32

    # mismatched A
    XA_checked, XB_checked = check_pairwise_arrays(XA.astype(np.float),
                                                   XB)
    assert XA_checked.dtype == np.float
    assert XB_checked.dtype == np.float

    # mismatched B
    XA_checked, XB_checked = check_pairwise_arrays(XA,
                                                   XB.astype(np.float))
    assert XA_checked.dtype == np.float
    assert XB_checked.dtype == np.float


@pytest.mark.parametrize("n_jobs", [1, 2])
@pytest.mark.parametrize("metric", ["seuclidean", "mahalanobis"])
@pytest.mark.parametrize("dist_function",
                         [pairwise_distances, pairwise_distances_chunked])
@pytest.mark.parametrize("y_is_x", [True, False], ids=["Y is X", "Y is not X"])
def test_pairwise_distances_data_derived_params(n_jobs, metric, dist_function,
                                                y_is_x):
    # check that pairwise_distances give the same result in sequential and
    # parallel, when metric has data-derived parameters.
    with config_context(working_memory=0.1):  # to have more than 1 chunk
        rng = np.random.RandomState(0)
        X = rng.random_sample((100, 10))

        if y_is_x:
            Y = X
            expected_dist_default_params = squareform(pdist(X, metric=metric))
            if metric == "seuclidean":
                params = {'V': np.var(X, axis=0, ddof=1)}
            else:
                params = {'VI': np.linalg.inv(np.cov(X.T)).T}
        else:
            Y = rng.random_sample((100, 10))
            expected_dist_default_params = cdist(X, Y, metric=metric)
            if metric == "seuclidean":
                params = {'V': np.var(np.vstack([X, Y]), axis=0, ddof=1)}
            else:
                params = {'VI': np.linalg.inv(np.cov(np.vstack([X, Y]).T)).T}

        expected_dist_explicit_params = cdist(X, Y, metric=metric, **params)
        dist = np.vstack(tuple(dist_function(X, Y,
                                             metric=metric, n_jobs=n_jobs)))

        assert_allclose(dist, expected_dist_explicit_params)
        assert_allclose(dist, expected_dist_default_params)
