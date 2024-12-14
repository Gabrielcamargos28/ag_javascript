document.getElementById('run-algorithm').addEventListener('click', runAlgorithm);

function runAlgorithm() {
  const problemInput = document.getElementById('problem-input').value;
  const resultsDiv = document.getElementById('results');

  if (!problemInput.trim()) {
    resultsDiv.innerHTML = '<p>Insira um problema válido.</p>';
    return;
  }

  const solution = geneticAlgorithm(problemInput);
  displaySolution(solution);
}

function geneticAlgorithm(problem) {
  // Configurações fixas
  const populationSize = 100;
  const generations = 50;
  const crossoverRate = 0.8;
  const mutationRate = 0.1;

  let population = initializePopulation(populationSize);
  let bestSolution = null;

  for (let gen = 0; gen < generations; gen++) {
    population = evaluatePopulation(population, problem);

    const parents = selectParents(population);
    const offspring = crossover(parents, crossoverRate);
    const mutatedOffspring = mutate(offspring, mutationRate);

    population = reinsertion(population, mutatedOffspring);

    bestSolution = population[0]; // Melhor solução até agora
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
  const letterToDigit = mapLettersToDigits(individual);
  const [operand1, operand2, result] = parseProblem(problem, letterToDigit);

  return Math.abs(operand1 + operand2 - result);
}

function mapLettersToDigits(individual) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const mapping = {};
  individual.forEach((digit, index) => {
    mapping[alphabet[index]] = digit;
  });
  return mapping;
}

function parseProblem(problem, letterToDigit) {
  const parts = problem.toUpperCase().match(/\w+/g);

  return parts.map((word) =>
    parseInt(
      [...word].map((letter) => letterToDigit[letter]).join(''),
      10
    )
  );
}

function selectParents(population) {
  const tournamentSize = 3;
  const parents = [];

  for (let i = 0; i < population.length; i++) {
    const tournament = [];
    for (let j = 0; j < tournamentSize; j++) {
      const randomIndex = Math.floor(Math.random() * population.length);
      tournament.push(population[randomIndex]);
    }
    tournament.sort((a, b) => a.fitness - b.fitness);
    parents.push(tournament[0]);
  }

  return parents;
}

function crossover(parents, rate) {
  const offspring = [];

  for (let i = 0; i < parents.length; i += 2) {
    const parent1 = parents[i].individual;
    const parent2 = parents[(i + 1) % parents.length].individual;

    if (Math.random() < rate) {
      const size = parent1.length;
      const child1 = Array(size).fill(null);
      const child2 = Array(size).fill(null);

      const start = Math.floor(Math.random() * size);
      const end = Math.floor(Math.random() * (size - start)) + start;

      for (let j = start; j <= end; j++) {
        child1[j] = parent1[j];
        child2[j] = parent2[j];
      }

      for (let j = 0; j < size; j++) {
        if (!child1.includes(parent2[j])) {
          child1[child1.indexOf(null)] = parent2[j];
        }
        if (!child2.includes(parent1[j])) {
          child2[child2.indexOf(null)] = parent1[j];
        }
      }

      offspring.push({ individual: child1, fitness: Infinity });
      offspring.push({ individual: child2, fitness: Infinity });
    } else {
      offspring.push({ individual: parent1, fitness: Infinity });
      offspring.push({ individual: parent2, fitness: Infinity });
    }
  }

  return offspring;
}

function mutate(offspring, rate) {
  offspring.forEach((child) => {
    if (Math.random() < rate) {
      const size = child.individual.length;
      const index1 = Math.floor(Math.random() * size);
      const index2 = Math.floor(Math.random() * size);

      const temp = child.individual[index1];
      child.individual[index1] = child.individual[index2];
      child.individual[index2] = temp;
    }
  });

  return offspring;
}

function reinsertion(parents, offspring) {
  const combined = [...parents, ...offspring].sort((a, b) => a.fitness - b.fitness);
  const eliteCount = Math.floor(parents.length * 0.2);
  const newPopulation = combined.slice(0, eliteCount);

  return newPopulation.concat(combined.slice(eliteCount, parents.length));
}

function displaySolution(solution) {
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

function displaySolution2(solution) {
  const resultsDiv = document.getElementById('results2');
  const letterValuesDiv = document.getElementById('letter-values2');
  const letterMapping = mapLettersToDigits(solution.individual);

  resultsDiv.innerHTML = `
    <p>Melhor solução encontrada:</p>
    <p>Fitness: ${solution.fitness}</p>
  `;

  letterValuesDiv.innerHTML = '';
  for (const [letter, value] of Object.entries(letterMapping)) {
    const letterContainer = document.createElement('div');
    letterContainer.style.marginBottom = '8px';

    letterContainer.innerHTML = `
      <label for="${letter}">${letter}: </label>
      <input id="${letter}" type="text" value="${value}" readonly style="width: 50px; text-align: center;" />
    `;

    letterValuesDiv.appendChild(letterContainer);
  }
}
