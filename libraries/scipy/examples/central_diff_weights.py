from scipy.misc import central_diff_weights

def g(x):
    return 2 * x**2 + 3

point = 10.0 
step = 0.1 
point_number = 3
weights = central_diff_weights(point_number) 
vals = [g(point + (i - point_number/2) * step) for i in range(point_number)]
sum(w * v for (w, v) in zip(weights, vals))/step