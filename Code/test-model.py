import Model

d_in = Model.InputLayer(3)
d1 = Model.DenseLayer(3)
d2 = Model.DenseLayer(4)
d3 = Model.DenseLayer(2)

X = [10,2.222,13.4574,4]
weights = [-0.5269779407873274, -0.10167654360408651, 0.6189301541618253, 0.23700266484996846, 0.5574468791466884, -0.3905119048139203, 0.9400126715518587, 0.8461318014786008, 0.4226203626245758, -0.18427235776359796, -0.3008161224993775, -0.9452369012783766]
""" 
print(dl.Execute(X, weights))
print(dl.Execute2(X, weights))
 """
model = Model.Model([d_in, d1, d2, d3])
print(model.NumWeights())