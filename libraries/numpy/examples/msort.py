import numpy as np

myArray = np.array([[0.434, 0.768, 0.54900530],
                    [0.36211, 0.3784, 0.2415],
                    [0.258, 0.52929049, 0.39172155]])

sorted = np.msort(myArray)

print(f"Min element is {sorted[0][0]}")

