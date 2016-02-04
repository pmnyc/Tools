from __future__ import division
import math
import json
import numpy as np
from sklearn.base import BaseEstimator

from rbm import RBM
from layers import SigmoidLayer
from copper.utils import opti as MBOpti
from utils import sigmoid
from sklearn.neural_network import BernoulliRBM

from copper.utils.progress import ProgressBar  # import last


def cost(weights, X, y, layers, num_labels):
    output = layers[0].output(X)
    for layer in layers[1:]:
        output = layer.output(output)

    Y = np.eye(num_labels)[y]
    h = output
    costPositive = -Y * np.log(h)
    costNegative = (1 - Y) * np.log(1 - h)
    return np.sum(costPositive - costNegative) / X.shape[0]


def cost_prime(weights, X, y, layers, num_labels):
    Y = np.eye(num_labels)[y]
    Deltas = [np.zeros((l.n_in + 1, l.n_out)) for l in layers]

    for i, row in enumerate(X):
        # Forward
        output = row
        activations = (output, )
        for layer in layers:
            output = layer.output(output)
            activations = activations + (output, )

        # Backprop
        prev_delta = activations[-1] - Y[i, :].T
        deltas = (prev_delta, )

        for act, layer in zip(reversed(activations[1:-1]), reversed(layers)):
            delta = np.dot(layer.W, prev_delta) * (act * (1 - act)).T
            deltas = (delta, ) + deltas
            prev_delta = delta

        # Accumulate errors
        for delta, act, i in zip(deltas, activations[:-1], range(len(Deltas))):
            act = np.append(1, act)  # Bias unit = 1
            Deltas[i] = Deltas[i] + np.dot(delta[np.newaxis].T, act[np.newaxis]).T

    for i in range(len(Deltas)):
        Deltas[i] = Deltas[i] / X.shape[0]

    return np.concatenate(tuple([D.reshape(-1) for D in Deltas]))


class DBN(BaseEstimator):

    def __init__(self, hidden_layers, coef0=None, random_state=None,
                 progress_bars=False,
                 pretrain_batch_size=100,
                 pretrain_epochs=0, pretrain_batches_per_epoch=-1,
                 pretrain_callback=None,
                 finetune_method='GD', finetune_batch_size=50,
                 finetune_epochs=1, finetune_batches_per_epoch=-1,
                 finetune_options=None, finetune_callback=None):
        self.hidden_layers = hidden_layers
        self.coef_ = None if coef0 is None else np.copy(coef0)

        if random_state is None:
            self.rnd = np.random.RandomState()
        elif isinstance(random_state, int):
            self.rnd = np.random.RandomState(random_state)
        else:
            self.rnd = random_state

        self.progress_bars = progress_bars

        self.pretrain_batch_size = pretrain_batch_size
        self.pretrain_epochs = pretrain_epochs
        self.pretrain_batches_per_epoch = pretrain_batches_per_epoch
        self.pretrain_callback = pretrain_callback
        self.finetune_method = finetune_method
        self.finetune_batch_size = finetune_batch_size
        self.finetune_epochs = finetune_epochs
        self.finetune_batches_per_epoch = finetune_batches_per_epoch

        self.finetune_options = {} if finetune_options is None else finetune_options
        self.finetune_callback = finetune_callback

    def build_net(self, n_in, n_out):
        layers = [n_in]
        layers.extend(self.hidden_layers)
        layers.append(n_out)
        self.weights_info = [(layers[i], layers[i + 1]) for i in range(len(layers) - 1)]

        self.layers = list()
        for w_info in self.weights_info:
            n_in = w_info[0]
            n_out = w_info[1]
            self.layers.append(SigmoidLayer(n_in=n_in, n_out=n_out, random_state=self.rnd))

    def assign_weights(self):
        start_pos = 0
        for layer in self.layers:
            n_in = layer.W.shape[0]
            n_out = layer.W.shape[1]

            end_pos = start_pos + n_out
            layer.b = self.coef_[start_pos:end_pos]

            start_pos = end_pos
            end_pos = start_pos + n_in * n_out
            layer.W = self.coef_[start_pos:end_pos].reshape((n_in, n_out))
            start_pos = end_pos

    def save(self, filepath):
        info = {}
        info['metadata'] = self.weights_info
        info['weights'] = self.coef_.tolist()
        with open(filepath, 'w') as outfile:
            json.dump(info, outfile)

    def load(self, filepath):
        with open(filepath, 'r') as infile:
            info = json.load(infile)
            weight_info = info['metadata']
            n_in = weight_info[0][0]
            n_out = weight_info[-1][1]
            self.build_net(n_in, n_out)
            self.coef_ = np.array(info['weights'])
            self.assign_weights()

    def fit(self, X, y):
        self.build_net(X.shape[1], len(np.unique(y)))

        # Assign weights of layers as views of the big weights
        if self.coef_ is None:
            ws = list()
            for layer in self.layers:
                ws.append(layer.b.reshape(-1))
                ws.append(layer.W.reshape(-1))
            self.coef_ = np.concatenate(tuple(ws))
            self.assign_weights()

        # Pretrain
        if self.pretrain_epochs > 0:
            if self.progress_bars:
                if self.pretrain_batches_per_epoch == -1:
                    batches_per_epoch = int(X.shape[0] / self.pretrain_batch_size)
                else:
                    batches_per_epoch = self.pretrain_batches_per_epoch

                maxiters = self.pretrain_epochs * batches_per_epoch * len(self.layers)
                pt_bar = ProgressBar(max=maxiters, desc='Pretrain')

            if self.pretrain_batch_size == -1:
                # Use full-batch
                self.pretrain_batch_size = X.shape[0]

            # Create RBM layers using the same weights
            self.rbm_layers = []
            for i, layer in enumerate(self.layers):
                n_hid = layer.W.shape[1]
                new = RBM(layer)
                self.rbm_layers.append(new)

            # Actual pretrain
            for i, rbm_layer in enumerate(self.rbm_layers):
                for epoch in range(self.pretrain_epochs):
                    mb = MBOpti.minibatches(X, batch_size=self.pretrain_batch_size,
                                 batches=self.pretrain_batches_per_epoch,
                                 random_state=self.rnd)

                    for j, batch in enumerate(mb):
                        if i == 0:
                            input = batch
                        else:
                            # input = self.layers[i - 1].output(batcn)
                            try:
                                input = self.layers[i - 1].sample_h_given_v(input)
                            except:
                                print input.shape, self.layers[i-1].W.shape
                                raise Exception('1')

                        rbm_layer.contrastive_divergence(input)
                        if self.progress_bars:
                            pt_bar.next()
                        if self.pretrain_callback is not None:
                            stop = self.pretrain_callback(self, layer, epoch + 1, j + 1)
                            if stop == True:
                                break

            if self.progress_bars:
                pt_bar.complete()

        # Finetune
        if self.finetune_epochs > 0:
            if self.progress_bars:
                if self.finetune_batches_per_epoch == -1:
                    batches_per_epoch = int(X.shape[0] / self.finetune_batch_size)
                else:
                    batches_per_epoch = self.finetune_batches_per_epoch

                maxiters = self.finetune_epochs * batches_per_epoch
                ft_bar = ProgressBar(max=maxiters, desc='Finetune')
            def _callback(epoch, i):
                if self.progress_bars:
                    ft_bar.next()
                if self.finetune_callback is not None:
                    return self.finetune_callback(self, epoch, i)

            self.finetune_options = self.finetune_options.copy()
            args = (self.layers, len(np.unique(y)))
            MBOpti.minimize(self.coef_, X, y, fun=cost, grad=cost_prime, weights=self.coef_,
                            method=self.finetune_method,
                            epochs=self.finetune_epochs, batch_size=self.finetune_batch_size,
                            batches_per_epoch=self.finetune_batches_per_epoch,
                            options=self.finetune_options, args=args, callback=_callback,
                            random_state=self.rnd)

            if self.progress_bars:
                ft_bar.complete()

    def predict_proba(self, X):
        output = self.layers[0].output(X)
        for layer in self.layers[1:]:
            output = layer.output(output)
        return output

    def predict(self, X):
        return self.predict_proba(X).argmax(1)
