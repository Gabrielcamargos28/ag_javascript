document.getElementById('run-algorithm').addEventListener('click', runAlgorithm);

function runAlgorithm() {
    const problemInput = document.getElementById('problem-input').value;
    const resultsDiv = document.getElementById('results');

    if (!problemInput.trim()) {
        resultsDiv.innerHTML = '<p>Insira um problema válido.</p>';
        return;
    }

    const solutions = [];
    const config = {
        populationSize: 100,
        generations: 50,
        crossoverRate: 0.8,
        mutationRate: 0.1,
        selectionMethod: 'roulette', // Pode ser 'tournament'
        reinsertionMethod: 'elitism' // Pode ser 'ordered'
    };

    for (let i = 0; i < 1000; i++) {
        const solution = geneticAlgorithm(problemInput, config);
        solutions.push(solution);
    }

    exportToExcel(solutions);
    resultsDiv.innerHTML = '<p>Resultados exportados para Excel.</p>';
    displaySolution(solutions)
    console.log(solutions[0])

}

function geneticAlgorithm(problem, config) {
    let population = initializePopulation(config.populationSize);
    let bestSolution = null;

    for (let gen = 0; gen < config.generations; gen++) {
        population = evaluatePopulation(population, problem);

        const parents = selectParents(population, config.selectionMethod);
        const offspring = crossover(parents, config.crossoverRate);
        const mutatedOffspring = mutate(offspring, config.mutationRate);

        population = reinsertion(population, mutatedOffspring, config.reinsertionMethod);
        bestSolution = population[0]; // Melhor solução até agora

        if (bestSolution.fitness === 0) break; // Solução perfeita encontrada
    }

    return bestSolution;
}

function initializePopulation(size) {
    const population = [];
    while (population.length < size) {
        const individual = [...Array(10).keys()].sort(() => Math.random() - 0.5);
        population.push({ individual, fitness: Infinity });
    }
    return population;
}

function evaluatePopulation(population, problem) {
    return population
        .map((ind) => {
            const fitness = evaluateFitness(ind.individual, problem);
            return { ...ind, fitness };
        })
        .sort((a, b) => a.fitness - b.fitness);
}

function evaluateFitness(individual, problem) {
    const letterToDigit = mapLettersToDigits(individual, problem);
    const { operand1, operand2, result } = parseProblem(problem, letterToDigit);

    const calculatedValue = operand1 + operand2;
    return Math.abs(calculatedValue - result);
}

function mapLettersToDigits(individual, problem) {
    const letters = Array.from(new Set(problem.replace(/[^A-Z]/g, '')));
    return Object.fromEntries(letters.map((letter, i) => [letter, individual[i]]));
}

function parseProblem(problem, letterToDigit) {
    const [operands, result] = problem.split('=').map((s) => s.trim());
    const [op1, op2] = operands.split('+').map((s) => s.trim());

    const operand1 = parseInt(op1.split('').map((l) => letterToDigit[l]).join(''));
    const operand2 = parseInt(op2.split('').map((l) => letterToDigit[l]).join(''));
    const resultValue = parseInt(result.split('').map((l) => letterToDigit[l]).join(''));

    return { operand1, operand2, result: resultValue };
}

function selectParents(population, method) {
    if (method === 'roulette') {
        return rouletteSelection(population);
    } else if (method === 'tournament') {
        return tournamentSelection(population);
    }
    return [];
}

function rouletteSelection(population) {
    const totalFitness = population.reduce((sum, ind) => sum + 1 / (1 + ind.fitness), 0);
    const probabilities = population.map((ind) => 1 / (1 + ind.fitness) / totalFitness);

    const selected = [];
    for (let i = 0; i < population.length; i++) {
        const rand = Math.random();
        let acc = 0;
        for (let j = 0; j < population.length; j++) {
            acc += probabilities[j];
            if (rand <= acc) {
                selected.push(population[j]);
                break;
            }
        }
    }
    return selected;
}

function tournamentSelection(population, tournamentSize = 3) {
    const selected = [];
    for (let i = 0; i < population.length; i++) {
        const tournament = [];
        for (let j = 0; j < tournamentSize; j++) {
            tournament.push(population[Math.floor(Math.random() * population.length)]);
        }
        tournament.sort((a, b) => a.fitness - b.fitness);
        selected.push(tournament[0]);
    }
    return selected;
}

function crossover(parents, crossoverRate) {
    const offspring = [];
    for (let i = 0; i < parents.length; i += 2) {
        if (Math.random() < crossoverRate) {
            const parent1 = parents[i].individual;
            const parent2 = parents[i + 1]?.individual || parents[0].individual;

            const cutPoint = Math.floor(Math.random() * parent1.length);
            const child1 = parent1.slice(0, cutPoint).concat(parent2.slice(cutPoint));
            const child2 = parent2.slice(0, cutPoint).concat(parent1.slice(cutPoint));

            offspring.push({ individual: child1, fitness: Infinity });
            offspring.push({ individual: child2, fitness: Infinity });
        } else {
            offspring.push(parents[i]);
            if (parents[i + 1]) offspring.push(parents[i + 1]);
        }
    }
    return offspring;
}

function mutate(offspring, mutationRate) {
    return offspring.map((child) => {
        if (Math.random() < mutationRate) {
            const index1 = Math.floor(Math.random() * child.individual.length);
            const index2 = Math.floor(Math.random() * child.individual.length);

            const mutated = [...child.individual];
            [mutated[index1], mutated[index2]] = [mutated[index2], mutated[index1]];

            return { individual: mutated, fitness: Infinity };
        }
        return child;
    });
}

function reinsertion(population, offspring, method) {
    if (method === 'elitism') {
        const combined = [...population, ...offspring];
        return combined.sort((a, b) => a.fitness - b.fitness).slice(0, population.length);
    } else if (method === 'ordered') {
        return offspring.sort((a, b) => a.fitness - b.fitness).slice(0, population.length);
    }
    return population;
}

function exportToExcel(solutions) {
    const workbook = XLSX.utils.book_new();
    const data = solutions.map((s, index) => ({
        Execucao: index + 1,
        Fitness: s.fitness,
        Individuo: s.individual.join(',')
    }));

    const worksheet = XLSX.utils.json_to_sheet(data);
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Resultados');
    XLSX.writeFile(workbook, 'resultados_geneticos.xlsx');
}

function displaySolution2(solution) {
  const resultsDiv = document.getElementById('results');
  const letterMapping = mapLettersToDigits(solution.individual);
  const problemInput = document.getElementById('problem-input').value;

  const [operand1, operand2, result] = parseProblem(problemInput, letterMapping);

  const letterDetails = Object.entries(letterMapping)
    .map(([letter, value]) => `${letter}: ${value}`)
    .join('<br>');

  resultsDiv.innerHTML = `
    <p>Melhor solução encontrada:</p>
    <pre>${letterDetails}</pre>
    <p>Expressão resolvida: ${operand1} + ${operand2} = ${result}</p>
    <p>Fitness: ${solution.fitness}</p>
  `;
}

function displaySolution(solution) {
    const resultsDiv = document.getElementById('results');
    const letterMapping = mapLettersToDigits(solution.individual);
    const problemInput = document.getElementById('problem-input').value;
  
    // Parse do problema para obter os operandos e o resultado
    const { operand1, operand2, result } = parseProblem(problemInput, letterMapping);
  
    // Detalhes dos valores das letras
    const letterDetails = Object.entries(letterMapping)
      .map(([letter, value]) => `${letter}: ${value}`)
      .join('<br>');
  
    // Cálculo da expressão
    const calculatedValue = operand1 + operand2;
  
    // Exibindo os resultados no HTML
    resultsDiv.innerHTML = `
      <p><strong>Melhor solução encontrada:</strong></p>
      <p><strong>Valores das letras:</strong><br>${letterDetails}</p>
      <p><strong>Operação resolvida:</strong><br>${operand1} + ${operand2} = ${calculatedValue}</p>
      <p><strong>Fitness:</strong> ${solution.fitness}</p>
      <p><strong>Valor esperado:</strong> ${result}</p>
    `;
  }
  