import matplotlib.pyplot as plt

x = [i for i in range(1,11)]
game_ticks = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5']

sc1 = [2.81,4.0,3.61,3.81,2.61]
rf1 = [0.66,0.59,0.72,0.64,0.65]

sc2 = [3.57, 3.82, 3.29, 4.23, 3.86]
rf2 = [0.8,0.72,0.91,1.02,0.86]

sc = sc1 + sc2
rf = rf1 + rf2

# plt.plot(x, sc, 'b^-')
# plt.xticks(x, game_ticks)
# plt.xlabel('Environment Used')
# plt.ylabel('Average strategic points covered')
# plt.ylim([2.4,4.5])
# plt.xlim([-0.2,10.3])
# plt.show()

plt.plot(x, rf, 'r*-')
plt.xticks(x, game_ticks)
plt.xlabel('Environment Used')
plt.ylabel('Reduction factor')
plt.ylim([0.5,1.1])
plt.xlim([-0.2,10.3])
plt.show()
