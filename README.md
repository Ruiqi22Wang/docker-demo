# docker-demo

This is a demo for the usage of docker container and the deployment of a .py file. 

In the .py file,a synthetic dataset (with both features and targets) of 1000 data points is created using the make_moons module with the parameter noise=0.35. 

3 different data subsets are selected as 100 of the 1000 data points at random three times. For each of these 100-sample datasets, three k-Nearest Neighbor classifiers with: k = {1, 25, 50} are built. As a result, there are 9 combinations (3 datasets, with 3 trained classifiers). For each combination of dataset trained classifier, in a 3-by-3 grid, I plot the decision boundary to show the difference of the model performance.
