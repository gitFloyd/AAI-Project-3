import random
import math
from Activation import Activation as Act

class Layer:
	"""An abstract class for all types of Layers to inherit from. 
	"""
	SOFTMAX = 1
	RELU = 2

	def __init__(self, size:int, activation:int = None) -> None:
		"""The constructor sets up the number of neurons and the activation used for each

		Args:
			size (int): The number of neurons in the layer.
			activation (int, optional): Currently, there are two types of activation
			functions to choose from, Layer.SOFTMAX or Layer.RELU. If using the default
			value of None, then RELU is used. (Note that we cannot put Layer.RELU as
			the default, hence using None and then setting a proper default layer.)
		"""
		self.size_ = size
		if (activation == None or activation not in [Layer.SOFTMAX, Layer.RELU]):
			activation = Layer.RELU
		self.activation_ = activation
	
	def Execute(self, X:list[float], weights:list[float]) -> list[float]:
		"""Normally the Model.Execute function is invoked, which then causes all
		of the layers in the model to have their Layer.Execute method invoked.
		Thus, this method will normally only be explicitly called outside of a
		model when testing the layer.

		Args:
			X (list[float]): The vector of inputs.
			weights (list[float]): The vector of weights.

		Returns:
			list[float]: The vector of outputs.
		"""
		return []

	def Size(self) -> int:
		"""How many neurons are in this layer?

		Returns:
			int: The number of neurons in the layer.
		"""
		return self.size_

	def NumWeights(self, numInputs:int) -> int:
		"""Different types of layers require different amounts of weights. And,
		the number of weights normally depends on the number of inputs as well.

		Args:
			numInputs (int): The number of items in the input vector.

		Returns:
			int: The number of weights that the weight vector should contain.
		"""
		return numInputs
	
class FuzzyMembershipLayer(Layer):
	"""This layer implements a fuzzy neural network layer.
	"""

	def __init__(self, num_in:int, num_out:int, activation:int = None) -> None:
		super().__init__(num_out, activation)
		self.num_in_ = num_in
		self.sparseLayer = None

	def XGen(self, X):
		for i, x in enumerate(X):
			yield i, x

	def Execute(self, X:list[float], weights:list[float]) -> list[float]:
		"""Simply output the input.

		Args:
			X (list[float]): A vector of inputs.

		Returns:
			list[float]: The vector of inputs.
		"""
		xgen = self.XGen(X)
		outputs = []
		connections = {}
		x = None
		for i in range(self.size_):
			try:
				j, x = next(xgen)
			except StopIteration:
				xgen = self.XGen(X)
				j, x = next(xgen)

			# Fuzzy Set Membership Function
			outputs.append(1 / (1 + (( (x - weights[3 * i + 2]) / weights[3 * i])**2)**weights[3 * i + 1]))
			if j not in connections:
				connections[j] = [i]
			else:
				connections[j].append(i)

		if self.sparseLayer == None:
			self.sparseLayer = SparseLayer(connections, self.activation_)
		outputs = self.sparseLayer.Execute(outputs, weights[3 * self.size_:])

		return outputs

	def NumWeights(self, _) -> int:
		"""The InputLayer requires no weights.

		Returns:
			int: 0
		"""
		return self.size_ * 4
	
class InputLayer(Layer):
	"""Use this layer as the first layer of any model. This layer does not compute
	any outputs. It simply outputs the input. No weights are needed for this layer.
	"""
	
	def Execute(self, X:list[float], _) -> list[float]:
		"""Simply output the input.

		Args:
			X (list[float]): A vector of inputs.

		Returns:
			list[float]: The vector of inputs.
		"""
		#return [x / max(max(X), -min(X)) for x in X]
		return X

	def NumWeights(self, _) -> int:
		"""The InputLayer requires no weights.

		Returns:
			int: 0
		"""
		return 0
	
class DenseLayer(Layer):
	"""In this layer, every input is sent to every neuron.
	"""
	
	def Execute(self, X:list[float], weights:list[float]) -> list[float]:
		"""There are two branches to this method, one each for the two types of
		activation functions we are supporting. The main difference is ReLU does
		not need the sum of all the input*weight pairs, but Softmax does. 

		Args:
			X (list[float]): A vector of inputs.
			weights (list[float]): A vector of weights.

		Returns:
			list[float]: A vector of outputs.
		"""


		# print('{}, {}, {}'.format(len(X), self.size_, len(weights)))



		if len(X) * self.size_ != self.NumWeights(len(X)):
			raise Exception("The number of weights is incorrect. len(X) = ", len(X), ", len(weights) = ", len(weights), ", and numWeights() = ", self.NumWeights(len(X)))

		if self.activation_ == Layer.RELU:


			#for i in range(self.size_):
			#	for (j, x) in enumerate(X):
			#		if j + i * len(X) >= len(weights):
			#			print('{} + {} * {} >= {}'.format(j, i, len(X), len(weights)))

			return [
				Act.ReLU(sum([
					x * weights[j + i * len(X)] for (j, x) in enumerate(X)
				])) for i in range(self.size_)
			]
		else:
			i = 0
			j = 0
			outputs = [
				sum([
					x * weights[j + i * len(X)] for (j, x) in enumerate(X)
				]) for i in range(self.size_)
			]
			return [Act.Softmax(outputs, i) for i in range(self.size_)]

	def NumWeights(self, numInputs:int) -> int:
		"""The number of weights required is the size of the input vector
		times the number of neurons.

		Args:
			numInputs (int): The size of the input vector.

		Returns:
			int: The number of elements needed in the weight vector.
		"""
		return self.size_ * numInputs
	
class SparseLayer(Layer):
	"""This layer allows specifying which input is mapped to which neuron. If I have inputs
	x1 and x2 and neurons n1, n2, and n3, then connections can be specified as such:
	connections = [(0, [0, 1]), (1, [1, 2])]. In this case, x1 is mapped to n1 and n2 and
	x2 is mapped to n2 and n3.
	"""
	def __init__(self, connections:dict[int:list[int]], activation:int = None) -> None:
		"""The constructor for SparseLayer has a different signature than the abstract Layer. It takes
		a connections parameter instead of size. We dynamically determine a value for size using the
		connections parameter. In other words, the connections parameter defines the number of neurons.

		Args:
			connections (list[tuple[int, list[int]]], optional): A data structure that specifies the
			connections from inputs to neurons.
			activation (int, optional): The type of activation function to use. See the comments
			for the constructor of Layer for more details. Defaults to None.
		"""
		neuron_ids = set()
		self.connections_ = connections

		# This layer cannot accomodate variable size inputs. Hence, we can determine
		# the number of weights now.
		self.numWeights_ = 0
		for input_id in connections:
			# Count the neurons
			neuron_ids = neuron_ids.union(connections[input_id])
			# Count the weights
			if input_id != None:
				self.numWeights_ += len(connections[input_id])
		super().__init__(len(neuron_ids), activation)
	
	def Execute(self, X:list[float], weights:list[float]) -> list[float]:
		"""Executes the SparseLayer.

		Args:
			X (list[float]): A vector of inputs.
			weights (list[float]): A vector of weights.

		Returns:
			list[float]: A vector of outputs.
		"""

		values = [0] * self.size_
		for input_id in self.connections_:
			if input_id != None:
				for neuron_id in self.connections_[input_id]:
					values[neuron_id] += X[input_id] * weights[neuron_id]

		if self.activation_ == Layer.RELU: 
			return [Act.ReLU(value) for value in values]
		else:
			return [Act.Softmax(values, i) for (i, _) in enumerate(values)]

	def NumWeights(self, _) -> int:
		"""The number of weights is determined when the object is instantiated.

		Returns:
			int: The number of weights required.
		"""
		return self.numWeights_

	@staticmethod
	def AddConnection(connections:dict[int:list[int]], neuron:int, i:int):
		# max(1, i) --- If len(.) == 0 or len(.) < i

		if i in connections:
			connections[i].append(neuron)
		else:
			connections[i] = [neuron]
	
	@staticmethod
	def CountConnections(connections):
		return sum([len(connections[i]) for i in connections])

	@classmethod
	def RandConnections(cls, num_in:int, num_connections:int, num_out:int):
		connections = {}
		neurons = set()
		neuron_ids = list(range(num_in))
		while cls.CountConnections(connections) < num_connections:
			random.shuffle(neuron_ids)
			for i in neuron_ids:
				connect_to = random.randint(0, num_out-1)
				neurons.add(connect_to)
				cls.AddConnection(connections, connect_to, i)
				if cls.CountConnections(connections) == num_connections:
					break
		if len(neurons) < num_out:
			for neuron in set(range(num_out)).difference(neurons):
				cls.AddConnection(connections, neuron, None)
		return connections
				


class Model:
	"""The Model contains all of the Layers in the neural network. It also handles
	executing the network from input to hidden layers to output.
	"""

	def __init__(self, layers:list[Layer] = []) -> None:
		"""The Model can have its Layers specified when it is instantiated. Or they
		can be added later. The only requirement here is that the first layer must
		be an InputLayer. If no layers are passed in, then the AddLayer method will
		check if the first Layer is an InputLayer.

		Args:
			layers (list[Layer], optional): A list of Layers to add to the model. Defaults to [].

		Raises:
			Exception: When the first layer, if given, is not an InputLayer.
		"""
		if len(layers) > 0:
			if not isinstance(layers[0], InputLayer):
				raise Exception("Model requires the first layer to be an InputLayer.")
		self.layers_ = layers

	def AddLayer(self, layer:Layer) -> None:
		"""Layers can be added after instantiating the object. Layers always get added
		to the end of the network.

		Args:
			layer (Layer): A Layer to add to the model.

		Raises:
			Exception: When the first layer is not an InputLayer.
		"""
		self.layers_.append(layer)
		if not isinstance(self.layers_[0], InputLayer):
			raise Exception("Model requires the first layer to be an InputLayer.")

	def Execute(self, X:list[float], weights:list[float] = None) -> list[float]:
		"""Executes the entire neural network.

		Args:
			X (list[float]): A vector of inputs.
			weights (list[float]): A vector of weights. The Model.NumWeights method
			can be used to determine how many weights are needed.

		Returns:
			list[float]: A vector of outputs for the neural network.
		"""

		if weights == None:
			weights = [random.randint(-1,0) + random.random() for _ in range(self.NumWeights()) ]
		start = 0
		end = 0
		results = X
		for layer in self.layers_:
			start = end
			end += layer.NumWeights(len(results))
			results = layer.Execute(results, weights[start:end])
		return results

	def NumWeights(self) -> int:
		"""Determines the number of weights needed given the network structure.

		Returns:
			int: The number of weights needed for the entire network.
		"""
		count = 0
		# The InputLayer ignores the size passed into NumWeights.
		size = 0
		for layer in self.layers_:
			count += layer.NumWeights(size)
			size = layer.Size()
		return count