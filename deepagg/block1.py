import numpy as np
import theano
import theano.tensor as T
import lasagne
import time
import sys


class Block1:
    """
    Defines the Block1 Neural network
    """

    def __init__(self, input_dimension):
        """
        input_dimension - number of dimensions of input to Block1,
                                          in our case, probably 8
        """
        self.input_dimension = input_dimension

    def define_network(self, learning_rate=0.01, momentum=0.9):
        """
        Define the theano functions
        """
        input_var = T.matrix('inputs')
        target_var = T.matrix('targets')
        self.network = self.get_network_layers(input_var)
        prediction = lasagne.layers.get_output(self.network)
        loss = lasagne.objectives.categorical_crossentropy(
            prediction, target_var)
        loss = loss.mean()
        params = lasagne.layers.get_all_params(self.network, trainable=True)
        updates = lasagne.updates.nesterov_momentum(loss, params,
                                                    learning_rate=learning_rate, momentum=momentum)
        test_prediction = lasagne.layers.get_output(
            self.network, deterministic=True)
        test_loss = lasagne.objectives.categorical_crossentropy(
            test_prediction, target_var)
        test_loss = test_loss.mean()
        test_acc = T.mean(T.eq(T.argmax(test_prediction, axis=0),
                               target_var), dtype=theano.config.floatX)
        self.train_fn = theano.function(
            [input_var, target_var], loss, updates=updates)
        self.val_fn = theano.function(
            [input_var, target_var], [test_loss, test_acc])
        self.test_fn = theano.function([input_var], prediction)

    def get_network_layers(self, input_var):
        """
        Define the network architecture
        """
        input_layer = lasagne.layers.InputLayer(
            (None, self.input_dimension), input_var=input_var)
        dense1 = lasagne.layers.DenseLayer(
            input_layer, num_units=10, nonlinearity=lasagne.nonlinearities.tanh)
        dense2 = lasagne.layers.DenseLayer(
            dense1, num_units=10, nonlinearity=lasagne.nonlinearities.tanh)
        dense3 = lasagne.layers.DenseLayer(
            dense2, num_units=10, nonlinearity=lasagne.nonlinearities.tanh)
        result = lasagne.layers.DenseLayer(
            dense3, num_units=1, nonlinearity=lasagne.nonlinearities.sigmoid)
        return result

    def train(self, train_X, train_y, val_X, val_y, num_epochs, batch_size, learning_rate=0.01, momentum=0.9):
        """
        Train the network. This is the function to call from outside
        Adapted from https://github.com/Lasagne/Lasagne/blob/master/examples/mnist.py#L234
        """
        train_y = np.reshape(train_y, (-1, 1))
        val_y = np.reshape(val_y, (-1, 1))
        self.define_network(learning_rate, momentum)
        for epoch in range(num_epochs):
            train_err = 0
            train_batches = 0
            start_time = time.time()
            for batch in self.iterate_minibatches(train_X, train_y, batch_size, bshuffle=True):
                inputs, targets = batch
                train_err += self.train_fn(inputs, targets)
                train_batches += 1
            val_err = 0
            val_acc = 0
            val_batches = 0
            for batch in self.iterate_minibatches(val_X, val_y, batch_size, bshuffle=False):
                inputs, targets = batch
                err, acc = self.val_fn(inputs, targets)
                val_err += err
                val_acc += acc
                val_batches += 1

            print("Epoch {} of {} took {:.3f}s".format(
                epoch + 1, num_epochs, time.time() - start_time))
            print("  training loss:\t\t{:.6f}".format(
                train_err / train_batches))
            print("  validation loss:\t\t{:.6f}".format(val_err / val_batches))
            print("  validation accuracy:\t\t{:.2f} %".format(
                val_acc / val_batches * 100))

    def save_weights(self, file_name):
        """
        Save the weights to a file. This should be called after train()
        """
        np.save(file_name, lasagne.layers.get_all_param_values(self.network))

    def load_weights(self, file_name):
        """
        Load the weights from a file
        """
        params = np.load(file_name)
        self.define_network()
        lasagne.layers.set_all_param_values(self.network, params)

    def predict(self, test_X):
        """
        Get predictions for an input
        """
        predictions = self.test_fn(test_X)
        return predictions

    def iterate_minibatches(self, inputs, targets, batchsize, bshuffle=False):
        """
        Helper to iterate over minibatches, taken from mnist example of lasagne
        """
        assert len(inputs) == len(targets)
        if bshuffle:
            indices = np.arange(len(inputs))
            np.random.shuffle(indices)
        for start_idx in range(0, len(inputs) - batchsize + 1, batchsize):
            if bshuffle:
                excerpt = indices[start_idx:start_idx + batchsize]
            else:
                excerpt = slice(start_idx, start_idx + batchsize, 1)
            yield inputs[excerpt], targets[excerpt].astype(np.int32)

if __name__ == "__main__":
    block1 = Block1(100)
    block1.define_network()
    print "Defined Block1 of DeepAgg"
