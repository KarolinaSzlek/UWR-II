import time
import numpy as np
from tqdm import trange
import matplotlib.pyplot as plt



def PMX(ind1, ind2, separator_no=2):
    new_ind1, new_ind2 = ind1.copy(), ind2.copy()
    idxs = sorted(np.random.choice(len(ind1), separator_no, replace=False))
    
    group = np.random.choice(separator_no-1)
    start, end = idxs[group], idxs[group+1]
    
    tmp = ind1[start:end].copy()
    ind1[start:end] = ind2[start:end]
    ind2[start:end] = tmp
    
    for i in range(len(ind1)):
        if start <= i < end:
            continue
            
        while ind1[i] in ind1[start:end]:
            # get elem from the other ind
            idx_of_elem = np.nonzero(ind1[start:end] == ind1[i])[0][0]
            ind1[i] = ind2[start+idx_of_elem]
        
        while ind2[i] in ind2[start:end]:
            # get elem from the other ind
            idx_of_elem = np.nonzero(ind2[start:end] == ind2[i])[0][0]
            ind2[i] = ind1[start+idx_of_elem]

    return ind1, ind2

def tsp_objective_function(p, dist):
    s = 0.0
    for i in range(len(p)):
        s += dist[p[i-1], p[i]]
    return s

def reverse_sequence_mutation(p, *args):
    a = np.random.choice(len(p), 2, False)
    i, j = a.min(), a.max()
    q = p.copy()
    q[i:j+1] = q[i:j+1][::-1]
    return q

def default_generate_population_function(chromosome_length, population_size):
    current_population = np.array([np.random.permutation(chromosome_length).astype(np.int64) 
                                       for _ in range(population_size)])
    return current_population


class SGA:
    
    def __init__(self, population_size, chromosome_length, distance_matrix, crossover_func=PMX, objective_func=tsp_objective_function, mutation_func=reverse_sequence_mutation, generate_population_func=default_generate_population_function, replace_method='mu+lambda', number_of_offspring=None, crossover_probability = 0.95, mutation_probability = 0.25, number_of_iterations = 250, no_groups=2):
        
        self.population_size = population_size
        self.chromosome_length = chromosome_length
        
        self.crossover_func = crossover_func
        self.objective_func = objective_func
        self.mutation_func = mutation_func
        self.generate_population_func = generate_population_func
        self.distance_matrix = distance_matrix
        
        if number_of_offspring is None:
            number_of_offspring = population_size
        self.number_of_offspring = number_of_offspring
        self.crossover_probability = crossover_probability
        self.mutation_probability = mutation_probability
        self.number_of_iterations = number_of_iterations
        assert replace_method in ['mu+lambda', 'lambda'], 'wrong replace_method: ["mu+lambda", "lambda"]'
        self.replace_method = replace_method
        self.no_groups = no_groups
        
        
    def run(self, verbose=False, with_tqdm=False):
        time0 = time.time()
        self.mean_costs = np.zeros(self.number_of_iterations)
        self.min_costs = np.zeros(self.number_of_iterations)
        self.max_costs = np.zeros(self.number_of_iterations)

        self.best_objective_value = np.Inf
        self.best_chromosome = np.zeros((1, self.chromosome_length))

        current_population = self._generate_random_population()
        objective_values = np.array(list(map(lambda ind: self.objective_func(ind, self.distance_matrix), current_population)))
        
        if with_tqdm:
            range_ = trange(self.number_of_iterations, position=0, leave=True)
        else:
            range_ = range(self.number_of_iterations)
    
        for t in range_:
            parent_indices = self._select_parent_indices(objective_values)

            children_population = self._generate_children_population(current_population, parent_indices)

            self._mutate_children_population(children_population)

            children_objective_values = self._eval_children(children_population)
            
            current_population, objective_values = self._replace_population(current_population, objective_values, children_population, children_objective_values)

            # recording some statistics
            if self.best_objective_value < objective_values[0]:
                self.best_objective_value = objective_values[0]
                self.best_chromosome = current_population[0, :]
                
            self.mean_costs[t] = objective_values.mean()
            self.min_costs[t] = objective_values.min()
            self.max_costs[t] = objective_values.max()
            
            if verbose:
                print('%3d %14.8f %12.8f %12.8f %12.8f %12.8f' % (t, time.time() - time0, objective_values.min(), objective_values.mean(), objective_values.max(), objective_values.std()))
    
    
    def plot_costs(self, title=''):
        plt.title(title)
        plt.plot(self.max_costs, label='max')
        plt.plot(self.min_costs, label='min')
        plt.plot(self.mean_costs, label='mean')
        plt.show()
        
    
    def _generate_random_population(self):
        return self.generate_population_func(self.chromosome_length, self.population_size)
    
    
    def _generate_children_population(self, current_population, parent_indices):
        children_population = np.zeros((self.number_of_offspring, self.chromosome_length), dtype=np.int64)
        
        for i in range(self.number_of_offspring//2):
            if np.random.random() < self.crossover_probability:
                children_population[2*i, :], children_population[2*i+1, :] = self.crossover_func(current_population[parent_indices[2*i], :].copy(), current_population[parent_indices[2*i+1], :].copy(), self.no_groups)
            else:
                children_population[2*i, :], children_population[2*i+1, :] = current_population[parent_indices[2*i], :].copy(), current_population[parent_indices[2*i+1]].copy()

        if np.mod(self.number_of_offspring, 2) == 1:
            children_population[-1, :] = current_population[parent_indices[-1], :]
        
        return children_population
    
    
    def _select_parent_indices(self, objective_values):
        fitness_values = objective_values.max() - objective_values
        
        if fitness_values.sum() > 0:
            fitness_values = fitness_values / fitness_values.sum()
        else:
            fitness_values = np.ones(self.population_size) / self.population_size
        parent_indices = np.random.choice(self.population_size, self.number_of_offspring, 
                                          True, fitness_values).astype(np.int64)
        return parent_indices
    
    
    def _mutate_children_population(self, children_population):
        for i in range(self.number_of_offspring):
            if np.random.random() < self.mutation_probability:
                children_population[i, :] = self.mutation_func(children_population[i, :], self.no_groups)
            
    
    def _eval_children(self, children_population):
        children_objective_values = np.zeros(self.number_of_offspring)
        for i in range(self.number_of_offspring):
            children_objective_values[i] = self.objective_func(children_population[i, :], self.distance_matrix)
        return children_objective_values
    
    
    def _replace_population(self, current_population, objective_values, children_population, children_objective_values):
        if self.replace_method == 'mu+lambda':
            objective_values = np.hstack([objective_values, children_objective_values])
            current_population = np.vstack([current_population, children_population])

            idxs = np.argsort(objective_values)
            current_population = current_population[idxs[:self.population_size], :]
            objective_values = objective_values[idxs[:self.population_size]]
        elif self.replace_method == 'lambda':
            current_population = children_population
            objective_values = children_objective_values
        
        return current_population, objective_values