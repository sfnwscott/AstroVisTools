import numpy as np

sky = np.zeros((10,10))
# for i in range(len(sky)):
#     print(sky[i].tostring())
# #     for j in range(len(sky[i])):
# #         print(sky[i][j])
arr = np.array([1, 2, 3, 4, 5, 6])
ts = arr.tobytes()
print(np.fromstring(ts, dtype=int))