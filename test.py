import unittest
import numpy as np
from tffm import TFFMClassifier
from scipy import sparse as sp
import tensorflow as tf



class TestFM(unittest.TestCase):

    def setUp(self):
        # Reproducibility.
        np.random.seed(0)

        self.X = np.random.randn(20, 10)
        self.y = np.random.binomial(1, 0.5, size=20)

    def decision_function_order_4(self, input_type):
        # Explanation for init_std=1.0.
        # With small init_std the contribution of higher order terms is
        # neglectable, so we would essentially test only low-order implementation.
        # That's why a relatively high init_std=1.0 here.
        model = TFFMClassifier(
            order=4,
            rank=10,
            optimizer=tf.train.AdamOptimizer(learning_rate=0.1),
            n_epochs=0,
            input_type=input_type,
            init_std=1.0,
            seed=0
        )

        if input_type == 'dense':
            X = self.X
        else:
            X = sp.csr_matrix(self.X)

        model.fit(X, self.y)
        b = model.intercept
        w = model.weights

        desired = self.bruteforce_inference(self.X, w, b)

        actual = model.decision_function(X)
        model.destroy()
        np.testing.assert_almost_equal(actual, desired, decimal=4)

    def test_dense(self):
        self.decision_function_order_4('dense')

    def test_sparse(self):
        self.decision_function_order_4('sparse')


    def bruteforce_inference_one_interaction(self, X, w, order):
        n_obj, n_feat = X.shape
        ans = np.zeros(n_obj)
        if order == 2:
            for i in range(n_feat):
                for j in range(i+1, n_feat):
                    x_prod = X[:, i] * X[:, j]
                    w_prod = np.sum(w[1][i, :] * w[1][j, :])
                    ans += x_prod * w_prod
        elif order == 3:
            for i in range(n_feat):
                for j in range(i+1, n_feat):
                    for k in range(j+1, n_feat):
                        x_prod = X[:, i] * X[:, j] * X[:, k]
                        w_prod = np.sum(w[2][i, :] * w[2][j, :] * w[2][k, :])
                        ans += x_prod * w_prod
        elif order == 4:
            for i in range(n_feat):
                for j in range(i+1, n_feat):
                    for k in range(j+1, n_feat):
                        for ell in range(k+1, n_feat):
                            x_prod = X[:, i] * X[:, j] * X[:, k] * X[:, ell]
                            w_prod = np.sum(w[3][i, :] * w[3][j, :] * w[3][k, :] * w[3][ell, :])
                            ans += x_prod * w_prod
        else:
            assert False
        return ans

    def bruteforce_inference(self, X, w, b):
        assert len(w) <= 4
        ans = X.dot(w[0]).flatten() + b
        if len(w) > 1:
            ans += self.bruteforce_inference_one_interaction(X, w, 2)
        if len(w) > 2:
            ans += self.bruteforce_inference_one_interaction(X, w, 3)
        if len(w) > 3:
            ans += self.bruteforce_inference_one_interaction(X, w, 4)
        return ans


if __name__ == '__main__':
    unittest.main()
