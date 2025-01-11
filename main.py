import numpy as np
import time
import sys
import os

"""

_________________________________________________________________________________________________________

This is entirely for learning purposes. There is no emphasis on accuracy or optimisation. Implementation
of CNN from scratch without resorting to any library such as PyTorch or Tensorflow is the aim here.

_________________________________________________________________________________________________________

"""

def cross_entropy_loss(predictions, labels):
    """
    Compute the cross-entropy loss for integer labels.
    :param predictions: Softmax probabilities, shape (batch_size, num_classes)
    :param labels: Integer labels, shape (batch_size,)
    :return: Loss (scalar)
    """
    batch_size = predictions.shape[0]
    # Extract the probabilities corresponding to the true labels
    correct_probs = predictions[np.arange(batch_size), labels]
    # Compute the loss
    return -np.sum(np.log(correct_probs + 1e-15)) / batch_size  # Add epsilon for numerical stability

def cross_entropy_gradient(predictions, labels):
    """
    Compute the gradient of the cross-entropy loss w.r.t. logits (softmax outputs).
    :param predictions: Softmax probabilities, shape (batch_size, num_classes)
    :param labels: Integer labels, shape (batch_size,)
    :return: Gradient of loss w.r.t. logits, shape (batch_size, num_classes)
    """
    batch_size = predictions.shape[0]
    gradient = predictions.copy()
    gradient[np.arange(batch_size), labels] -= 1  # Subtract 1 from the correct class probabilities
    return gradient / batch_size



class Conv2d:
    def __init__(self, input_channels, output_channels, kernel_size = (3, 3)):
        self.input = None
        self.relu_mask = None
        self.input_channels = input_channels
        self.output_channels = output_channels  # Number of filters
        self.kernel_size = kernel_size

        # Initialize kernels (filters) and biases
        self.weights = np.random.normal(0.0, 0.01, (self.output_channels, self.input_channels, self.kernel_size[0], self.kernel_size[1]))
        self.biases = np.zeros(output_channels)


    def forward(self, input):

        # Save input for backpropagation
        self.input = input

        batch_size, input_height, input_width, input_channels = input.shape

        # Calculate the output dimensions
        kernel_height, kernel_width = self.kernel_size

        output_height = input_height - kernel_height + 1
        output_width = input_width - kernel_width + 1

        output = np.zeros((batch_size, output_height, output_width, self.output_channels))

        for i in range(batch_size):
            for h in range(output_height):   # Loop over the height of the output
                for w in range(output_width):   # Loop over the width of the output
                    for oc in range(self.output_channels):   # Loop over the output channels
                        # Initialize the sum for this particular output location
                        sum_value = 0.0

                        # Loop through the input channels (RGB for example)
                        for ic in range(input_channels):   # Loop over each input channel
                            # Extract the region of the input image that corresponds to the filter
                            for kh in range(kernel_height):   # Loop over the kernel height
                                for kw in range(kernel_width):   # Loop over the kernel width
                                    input_value = input[i, h + kh, w + kw, ic]
                                    kernel_value = self.weights[oc, ic, kh, kw]

                                    # Multiply the input value with the kernel value and add to the sum
                                    sum_value += input_value * kernel_value
                        output[i, h, w, oc] = sum_value + self.biases[oc]

        # ReLU Activation: Apply activation and save mask
        self.relu_mask = (output > 0)  # Save mask for backward pass
        output = np.maximum(0, output)  # Apply ReLU
        return output


    def backward(self, dL_dout, learning_rate):

        batch_size, input_height, input_width, input_channels = self.input.shape
        kernel_height, kernel_width = self.kernel_size

        # Initialize gradients for weights, biases, and input
        dL_dweights = np.zeros_like(self.weights)
        dL_dbiases = np.zeros_like(self.biases)
        dL_din = np.zeros_like(self.input)

        # Apply ReLU mask to dL_dout
        dL_dout *= self.relu_mask

        # Calculate gradients for weights, biases, and input
        for i in range(batch_size):
            for h in range(dL_dout.shape[1]):   # Output height
                for w in range(dL_dout.shape[2]):   # Output width
                    for oc in range(self.output_channels):   #Output channels
                        # Gradient w.r.t. the bias (sum over all positions)
                        dL_dbiases[oc] += dL_dout[i, h, w, oc]

                        # Gradient w.r.t. the weights (input region * output gradient)
                        for ic in range(input_channels):
                            for kh in range(kernel_height):
                                for kw in range(kernel_width):
                                    input_value = self.input[i, h + kh, w + kw, ic]
                                    dL_dweights[oc, ic, kh, kw] += input_value * dL_dout[i, h, w, oc]

                                    # Gradient w.r.t. the input (reverse the convolution)
                                    dL_din[i, h + kh, w + kw, ic] += self.weights[oc, ic, kh, kw] * dL_dout[i, h, w, oc]

        # Update the weights and biases
        self.weights -= learning_rate * dL_dweights
        self.biases -= learning_rate * dL_dbiases
        return dL_din


class Dense:
    def __init__(self, input_channels, output_channels, activation):
        self.z = None
        self.input = None
        self.input_channels = input_channels
        self.output_channels = output_channels
        self.activation = activation
        self.weights = np.random.normal(0.0, .01, (input_channels, output_channels))  # Randomly initialized weights
        self.biases = np.zeros(output_channels)


    def forward(self, input):
        self.input = input
        output = []

        for row in input:
            row_output = np.dot(row, self.weights) + self.biases
            output.append(row_output)

        output = np.array(output)
        self.z = output
        output = self.activation_function(output)
        return output

    def backward(self, dL_dout, learning_rate):
        batch_size = self.input.shape[0]
        dL_din = np.zeros_like(self.input)  # Gradient w.r.t. input
        dL_dweights = np.zeros_like(self.weights)  # Gradient w.r.t. weights
        dL_dbiases = np.zeros_like(self.biases)  # Gradient w.r.t. biases

        # Gradients for weights and biases
        for i in range(batch_size):
            for oc in range(self.output_channels):
                dL_dbiases[oc] += dL_dout[i][oc]
                for ic in range(self.input.shape[1]):
                    dL_dweights[ic][oc] += dL_dout[i][oc] * self.input[i][ic]
                    dL_din[i][ic] += self.weights[ic][oc] * dL_dout[i][oc]

        dL_dweights /= batch_size
        dL_dbiases /= batch_size

        for oc in range(self.output_channels):
            self.biases[oc] -= learning_rate * dL_dbiases[oc]
            for ic in range(self.input.shape[1]):
                self.weights[ic][oc] -= learning_rate * dL_dweights[ic][oc]
        return dL_din  # Pass gradient to the previous layer



    def activation_function(self, values):
        """
        Apply the activation function.
        """
        if self.activation == "relu":
            return np.maximum(0, values)
        elif self.activation == "softmax":
            exp_values = np.exp(values - np.max(values, axis=1, keepdims=True))  # Numerical stability
            return exp_values / np.sum(exp_values, axis=1, keepdims=True)
        else:
            raise ValueError("Unsupported activation function: " + self.activation)



class MaxPooling2D:

    def __init__(self):
        self.input = None


    def forward(self, input):
        """
        :param input: is a 4D numpy array of shape  (batch_size, height, width, channel)
        :return: a 4D numpy array  (batch_size, height / 2, width / 2, channel)
        """

        # Save input for backpropagation
        self.input = input

        batch_size, height, width, channels = input.shape

        # Calculate the output dimensions
        output_height = height // 2
        output_width = width // 2

        # Initialize the output
        output = np.zeros((batch_size, output_height, output_width, channels))

        for i in range(batch_size):
            for j in range(output_height):  # Loop through the output height
                for k in range(output_width):  # Loop through the output width
                    for l in range(channels):  # Loop through the channels
                        # Define the 2x2 region for pooling
                        region = input[i, j*2:j*2+2, k*2:k*2+2, l]

                        # Get the maximum value in the region
                        output[i, j, k, l] = np.max(region)
        return output


    def backward(self, dL_dout, learning_rate):

        batch_size, input_height, input_width, input_channels = self.input.shape

        # Initialize gradients for input
        dL_din = np.zeros_like(self.input)

        # Calculate gradients and input
        for i in range(batch_size):
            for h in range(dL_dout.shape[1]):   # Output height
                for w in range(dL_dout.shape[2]):   # Output width
                    for oc in range(dL_dout.shape[3]):   # Output channels = Input channels

                        # Find the 2x2 region in the input corresponding to this output
                        region = self.input[i, h * 2:h * 2 + 2, w * 2:w * 2 + 2, oc]
                        # Find the index of the max value in the region
                        max_index = np.unravel_index(np.argmax(region), region.shape)
                        # The gradient is only propagated to the maximum element
                        dL_din[i, h * 2 + max_index[0], w * 2 + max_index[1], oc] += dL_dout[i, h, w, oc]
        return dL_din


class Sequential:
    def __init__(self):
        self.conv_pool_layers = []  # List to store convolutional and pooling layers
        self.dense_layers = []  # List to store dense layers
        self.conv_pool_outputs = []  # List to store outputs from convolutional layers
        self.dense_outputs = []  # List to store outputs from dense layers
        self.last_conv_output_shape = None

    def add_conv_pool_layer(self, layer):
        self.conv_pool_layers.append(layer)

    def add_dense_layer(self, dense_layer):
        self.dense_layers.append(dense_layer)

    def fit(self, epochs, input_images, labels, batch_size, learning_rate):

        for epoch in range(1, epochs + 1):
            original_stdout = sys.stdout
            # Disable print
            # sys.stdout = open(os.devnull, 'w')
            total_loss = 0
            for i in range(len(input_images)):
                start_index = i * batch_size
                end_index = min(start_index + batch_size, len(input_images))
                if start_index >= len(input_images):
                    break

                batch_predictions = self.forward(input_images[start_index: end_index])
                dL_dout = cross_entropy_gradient(batch_predictions, labels[start_index: end_index])
                self.backward(dL_dout, learning_rate)
                total_loss += cross_entropy_loss(batch_predictions, labels[start_index: end_index]) * (end_index - start_index + 1)

            sys.stdout = original_stdout

            if epoch % 10 == 1 or epoch == epochs:
                print(f"Epoch = {epoch:02}     Loss: {total_loss / len(input_images)}")

        predictions = self.forward(input_images)

        for prediction in predictions:
            print(*[f"{num:.12f}" for num in prediction])

        return predictions

    def forward(self, input):
        self.conv_pool_outputs.clear()
        self.dense_outputs.clear()

        current_input = input

        # Forward pass through convolutional layers
        for layer in self.conv_pool_layers:
            current_input = layer.forward(current_input)
            self.conv_pool_outputs.append(current_input)

        self.last_conv_output_shape = current_input.shape

        # Flatten the output from the last convolutional layer
        flat_input = [self.flatten(tensor) for tensor in current_input]

        # Forward pass through dense layers
        current_dense_input = np.array(flat_input)
        for dense_layer in self.dense_layers:
            current_dense_input = dense_layer.forward(current_dense_input)
            self.dense_outputs.append(current_dense_input)

        return current_dense_input

    def backward(self, dL_dout, learning_rate):
        current_dL_dout = dL_dout

        # Backward pass through dense layers (in reverse order)
        for i in range(len(self.dense_layers) - 1, -1, -1):
            current_dL_dout = self.dense_layers[i].backward(dL_dout=current_dL_dout, learning_rate=learning_rate)

        # Backward pass through convolutional layers (in reverse order)
        current_dL_dout_conv = self.unflatten(current_dL_dout)

        for i in range(len(self.conv_pool_layers) - 1, -1, -1):
            current_dL_dout_conv = self.conv_pool_layers[i].backward(dL_dout=current_dL_dout_conv, learning_rate=learning_rate)

    def flatten(self, tensor):
        return [value for matrix in tensor for row in matrix for value in row]

    def unflatten(self, flat):

        """
        get the output of the last conv layer
        """

        tensor = np.zeros(self.last_conv_output_shape)

        for i in range(self.last_conv_output_shape[0]):
            index = 0
            for j in range(self.last_conv_output_shape[1]):
                for k in range(self.last_conv_output_shape[2]):
                    for l in range(self.last_conv_output_shape[3]):
                        tensor[i, j, k, l] = flat[i][index]
                        index += 1
        return tensor


if __name__ == "__main__":

    np.set_printoptions(formatter={'float_kind': lambda x: f'{x:.7f}'})
    width = 20
    height = 20
    channels = 1

    total_images = 10
    classes = 5
    epochs = 20
    batch_size = 32

    # Create a 4x4 image with random pixel values between 0 and 1
    images = np.random.randint(0, 256, (total_images, height, width, channels), dtype=np.uint8)
    images = images / 255.0  # Normalize the image to [0, 1]

    # Label for the image
    labels = np.random.randint(0, classes, total_images)
    # labels = np.array([3, 1, 4, 2, 0])
    # labels = np.array([3, 3, 3, 3, 3])

    model = Sequential()

    trainable_parameters = 0

    conv_output_channels = [16, -1, 32, -1, 64]

    conv = None

    current_height = height
    current_width = width

    for i in range(len(conv_output_channels)):
        if conv_output_channels[i] > 0:
            conv = Conv2d(input_channels=channels if i == 0 else conv.output_channels, output_channels=conv_output_channels[i])
            model.add_conv_pool_layer(conv)
            trainable_parameters += conv.weights.size + conv.biases.size
            current_height -= 2
            current_width -= 2
        else:
            model.add_conv_pool_layer(MaxPooling2D())
            current_height = current_height // 2
            current_width = current_width // 2

        if current_height <= 0 or current_width <= 0:
            raise ValueError(f"Height or Width cannot be non-positive    height = {current_height}  width = {current_width}")

    dense1 = Dense(input_channels=current_height * current_width * conv.output_channels, output_channels=32, activation="relu")
    model.add_dense_layer(dense1)

    dense2 = Dense(input_channels=32, output_channels=classes, activation="softmax")
    model.add_dense_layer(dense2)

    for dense_layer in model.dense_layers:
        trainable_parameters += dense_layer.weights.size + dense_layer.biases.size

    print("Total trainable parameters = ", trainable_parameters)

    original_stdout = sys.stdout
    # Disable print
    # sys.stdout = open(os.devnull, 'w')

    start_time = time.time()
    predictions = model.fit(epochs=epochs, input_images=images, labels=labels, batch_size=batch_size, learning_rate=0.01)
    end_time = time.time()

    # Restore original stdout
    sys.stdout = original_stdout

    predicted_labels = np.argmax(predictions, axis=1)

    print("correct labels =     ", labels)
    print("predicted labels =   ", predicted_labels)

    correct_prediction = 0

    for predicted_label, correct_label in zip(predicted_labels, labels):
        if predicted_label == correct_label:
            correct_prediction += 1

    print(correct_prediction)
    print("Total time = ", end_time - start_time)

