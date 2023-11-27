import random
import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..')) 
from utils import *
import warnings
warnings.filterwarnings("ignore")
from enum import Enum
from math import sqrt
    
def abc_model_choice_normal(observedData, nullMean, variance, priorVarianceScale, distanceMetric, numComp = 3, abcIterations = 10_000_000):
    if distanceMetric == DistanceMetric.AUXILIARY:
        auxiliaryModel = fit_gaussian_mixture_EM(observedData, numComp)  
        weightMatrix = np.linalg.inv(gaussian_mixture_information(observedData, auxiliaryModel))
        
    if distanceMetric == DistanceMetric.WASS:
        observedData = np.sort(observedData)

    if distanceMetric == DistanceMetric.MMD:
        observedSqDistances = pdist(observedData, 'sqeuclidean')
        sigma = np.sqrt(np.median(observedSqDistances))
        
    modelChoices = np.zeros(abcIterations)  
    distances = np.zeros(abcIterations) 
    simulationSize = len(observedData)
    
    if variance is None:
        sd = None
        priorMeanSd = priorVarianceScale**0.5
    else:
        sd = variance**0.5
        priorMeanSd = (variance * priorVarianceScale)**0.5        

    for i in range(abcIterations): 
        # Selecting the model to sample from and defining the mean
        model = random.randint(0, 1)
        if model == 0:
            modelMean = nullMean
        else:
            modelMean = np.random.normal(nullMean, priorMeanSd)
            
        if sd is None:
            priorSd = np.random.gamma(0.1, 0.1)
        else: 
            priorSd = sd
        
        # Simulate sample from sampled model
        simulatedSample = normal_sample(modelMean, priorSd, simulationSize)
        
        # Calculate the chosen distance for the simulated sample
        if distanceMetric == DistanceMetric.AUXILIARY:            
            distance = auxiliary_distance(simulatedSample, auxiliaryModel, weightMatrix)
        elif distanceMetric == DistanceMetric.CVM:
            distance = cramer_von_mises_distance(observedData, simulatedSample)
        elif distanceMetric == DistanceMetric.WASS:
            distance = wasserstein_distance(observedData, simulatedSample)
        elif distanceMetric == DistanceMetric.MMD:
            distance = maximum_mean_discrepancy(observedData, simulatedSample, sigma, observedSqDistances)
        
        # Store current values   
        modelChoices[i] = model
        distances[i] = distance

    results = np.column_stack((modelChoices, distances))
    return results

def main(args):
    (nullMean, variance, priorVarianceScale, distanceMetric, observedPath, savePath) = args
    if os.path.exists(savePath):
        return
    observedData = np.load(observedPath)
    results = abc_model_choice_normal(observedData, nullMean, variance, priorVarianceScale, distanceMetric)
    np.save(savePath, results)
    
if __name__ == "__main__":
    args = parse_arguments()
    main(args)
