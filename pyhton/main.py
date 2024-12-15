import random
import pandas as pd

def validate_problem(problem):
    try:
        left, right = problem.split('=')
        if '+' not in left or not right:
            return False
        return True
    except ValueError:
        return False


def run_algorithm(problem):
    if not problem:
        print("Insira um problema válido.")
        return

    print("Problema inputado:", problem)

    solutions = []
    config = {
        'population_size': 100,
        'generations': 1000,
        'crossover_rate': 0.8,
        'mutation_rate': 0.1,
        'selection_method': 'roulette',
        'reinsertion_method': 'elitism'
    }

    for _ in range(config['generations']):  
        solution = genetic_algorithm(problem, config)
        solutions.append(solution)

    # Exportar resultados para Excel
    export_to_excel(solutions)
    
    # Exibir a melhor solução encontrada
    best_solution = solutions[0]
    display_solution(best_solution, problem)


def genetic_algorithm(problem, config):
    population = initialize_population(config['population_size'], problem)
    best_solution = None

    for gen in range(config['generations']):
        population = evaluate_population(population, problem)

        parents = select_parents(population, config['selection_method'])
        offspring = crossover(parents, config['crossover_rate'])
        mutated_offspring = mutate(offspring, config['mutation_rate'])

        population = reinsertion(population, mutated_offspring, config['reinsertion_method'])
        best_solution = population[0]

        # A execução pode ser parada caso a solução ideal seja encontrada
        if best_solution['fitness'] == 0:
            break

    return best_solution


def initialize_population(size, problem):
    letters = sorted(set(c for c in problem if c.isalpha()))  # Identificar as letras únicas no problema
    population = []
    while len(population) < size:
        # Gerar uma permutação aleatória dos números para as letras
        individual = random.sample(range(10), len(letters))
        population.append({'individual': individual, 'fitness': float('inf'), 'letters': letters})
    return population


def evaluate_population(population, problem):
    for individual in population:
        fitness = evaluate_fitness(individual['individual'], problem, individual['letters'])
        individual['fitness'] = fitness

    return sorted(population, key=lambda x: x['fitness'])


def evaluate_fitness(individual, problem, letters):
    letter_to_digit = map_letters_to_digits(individual, letters)

    try:
        operand1, operand2, result = parse_problem(problem, letter_to_digit)

        # Penalizar soluções inválidas
        if operand1 is None or operand2 is None or result is None:
            return float('inf')
        if operand1 + operand2 == result:
            return 0  # Solução ideal encontrada
        return abs((operand1 + operand2) - result)
    except ValueError:
        # Penalizar configurações inválidas
        return float('inf')



def map_letters_to_digits(individual, letters):
    return dict(zip(letters, individual))


def parse_problem(problem, letter_to_digit):
    try:
        operands, result = problem.split('=')
        operand1, operand2 = operands.split('+')

        operand1_value = int(''.join(str(letter_to_digit[letter]) for letter in operand1.strip()))
        operand2_value = int(''.join(str(letter_to_digit[letter]) for letter in operand2.strip()))
        result_value = int(''.join(str(letter_to_digit[letter]) for letter in result.strip()))

        # Verificar 0 inicial
        if (str(operand1_value)[0] == '0' or
            str(operand2_value)[0] == '0' or
            str(result_value)[0] == '0'):
            return None, None, None

        return operand1_value, operand2_value, result_value
    except KeyError:
        return None, None, None


def select_parents(population, method):
    if method == 'roulette':
        return roulette_selection(population)
    return []


def roulette_selection(population):
    total_fitness = sum(1 / (1 + ind['fitness']) for ind in population)
    probabilities = [1 / (1 + ind['fitness']) / total_fitness for ind in population]

    selected = []
    for _ in range(len(population)):
        rand = random.random()
        acc = 0
        for i, prob in enumerate(probabilities):
            acc += prob
            if rand <= acc:
                selected.append(population[i])
                break
    return selected


def crossover(parents, crossover_rate):
    offspring = []
    for i in range(0, len(parents), 2):
        if random.random() < crossover_rate:
            parent1, parent2 = parents[i]['individual'], parents[i+1]['individual']
            cut_point = random.randint(1, len(parent1)-1)
            child1 = parent1[:cut_point] + parent2[cut_point:]
            child2 = parent2[:cut_point] + parent1[cut_point:]
            offspring.append({'individual': child1, 'fitness': float('inf')})
            offspring.append({'individual': child2, 'fitness': float('inf')})
        else:
            offspring.append(parents[i])
            offspring.append(parents[i+1])
    return offspring


def mutate(offspring, mutation_rate):
    for child in offspring:
        if random.random() < mutation_rate:
            index1, index2 = random.sample(range(len(child['individual'])), 2)
            child['individual'][index1], child['individual'][index2] = child['individual'][index2], child['individual'][index1]
    return offspring


def reinsertion(population, offspring, method):
    if method == 'elitism':
        combined = population + offspring
        return sorted(combined, key=lambda x: x['fitness'])[:len(population)]
    return population


def export_to_excel(solutions):
    data = []
    for idx, solution in enumerate(solutions):
        data.append({
            'Execucao': idx + 1,
            'Fitness': solution['fitness'],
            'Individuo': ','.join(map(str, solution['individual']))
        })

    df = pd.DataFrame(data)
    df.to_excel('resultados_geneticos.xlsx', index=False)
    print("Resultados exportados para Excel.")


def display_solution(solution, problem):
    letter_mapping = map_letters_to_digits(solution['individual'], solution['letters'])
    operand1, operand2, result = parse_problem(problem, letter_mapping)

    letter_details = "<br>".join([f"{letter}: {value}" for letter, value in letter_mapping.items()])
    calculated_value = operand1 + operand2

    print(f"Melhor solução encontrada:")
    print(f"Valores das letras:\n{letter_details}")
    print(f"Operação resolvida: {operand1} + {operand2} = {calculated_value}")
    print(f"Fitness: {solution['fitness']}")
    print(f"Valor esperado: {result}")


if __name__ == '__main__':
    problem_input = input("Digite o problema (ex: A+B=C): ").strip()
    run_algorithm(problem_input)
