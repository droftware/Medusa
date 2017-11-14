* Cluster map into regions based on visibility value using DBSCAN
* Split any region which is greater than a threshold into smaller regions
* Create a regions graph in which each region is a node and there is an edge between two nodes if their corresponding regions are adjacent to each other. Each node stores the average visibility value of its corresponding region.
* As mentioned before, each team(hider/seeker) is divided into groups. A plan needs to be created at a higher level. This plan encompasses smaller atomic plans such as change behavior of a group, instruct a group to go to a specific region.
* At any time step, an enormous number of plans having various combinations of change behavior and goto region kind of atomic plans are possible.
* We need to evaluate the relative merit of each plan and choose the one which has the most merit.
* We evaluate the plans using MCTS