from flask import Flask, request, jsonify
import random
from flask_cors import CORS  

app = Flask(__name__)
CORS(app)  # Permitir CORS em todas as rotas

# Função para calcular o fitness de um indivíduo
def calcular_fitness(individuo, letras, palavras):
    letter_to_digit = {letras[i]: individuo[i] for i in range(len(letras))}

    def palavra_para_numero(palavra):
        numero = ''.join([str(letter_to_digit[letra]) for letra in palavra])
        if numero[0] == '0':  # Não pode começar com zero
            return None
        return int(numero)

    valores_palavras = [palavra_para_numero(palavra) for palavra in palavras]
    if None in valores_palavras:
        return float('inf')  # Fitness alto se houver número inválido

    soma = sum(valores_palavras[:-1])
    resultado = valores_palavras[-1]
    return abs(soma - resultado)

# Função para gerar uma população inicial
def gerar_populacao_inicial(tamanho, letras):
    populacao = []
    while len(populacao) < tamanho:
        individuo = random.sample(range(10), len(letras))  # Evita repetição de números
        populacao.append(individuo)
    return populacao

# Função de mutação
def mutacao(individuo, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
    return individuo

# Função de crossover cíclico
def crossover_ciclico(pai1, pai2):
    filho1 = pai1.copy()
    filho2 = pai2.copy()
    
    # Marcadores para saber quais genes já foram tratados
    visitados1 = [False] * len(pai1)
    visitados2 = [False] * len(pai2)
    
    i = 0
    while not all(visitados1):  # Continua até todos os genes de filho1 serem preenchidos
        if not visitados1[i]:
            # Preenche o gene do filho1 com o gene correspondente do pai2
            filho1[i] = pai2[i]
            visitados1[i] = True
            
            # Busca a próxima posição no ciclo
            i = pai1.index(filho1[i]) if filho1[i] in pai1 else (i + 1) % len(pai1)
        else:
            # Se o gene de filho1 já foi visitado, passa para o próximo
            i = (i + 1) % len(pai1)
    
    # Preenche os genes restantes do filho2
    for j in range(len(pai2)):
        if not visitados2[j]:
            filho2[j] = pai1[j]
    
    return filho1, filho2

# Função de crossover PMX
def crossover_pmx(pai1, pai2):
    size = len(pai1)
    filho1 = [-1] * size
    filho2 = [-1] * size
    
    ponto1, ponto2 = sorted(random.sample(range(size), 2))

    for i in range(ponto1, ponto2 + 1):
        filho1[i] = pai2[i]
        filho2[i] = pai1[i]
    
    def mapear(filho, pai, ponto1, ponto2):
        for i in range(size):
            if filho[i] == -1:
                gene = pai[i]
                while gene in filho:
                    gene = pai[filho.index(gene)]
                filho[i] = gene
    
    mapear(filho1, pai1, ponto1, ponto2)
    mapear(filho2, pai2, ponto1, ponto2)

    return filho1, filho2

# Função de crossover
def crossover(pai1, pai2, tipo_crossover):
    if tipo_crossover == 'C1':
        return crossover_ciclico(pai1, pai2)
    elif tipo_crossover == 'C2':
        return crossover_pmx(pai1, pai2)
    else:
        return crossover_ciclico(pai1, pai2)  # Default to Ciclico if no valid type is given

# Algoritmo genético principal
def algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover):
    letras = list(set(''.join(palavras)))  # Obter as letras únicas
    populacao = gerar_populacao_inicial(tamanho_pop, letras)

    for _ in range(geracoes):
        fitness = [calcular_fitness(individuo, letras, palavras) for individuo in populacao]
        
        # Encontrar o melhor indivíduo
        melhor_fitness = min(fitness)
        if melhor_fitness == 0:
            melhor_individuo = populacao[fitness.index(melhor_fitness)]
            return dict(zip(letras, melhor_individuo))
        
        # Seleção
        nova_populacao = []
        for _ in range(tamanho_pop // 2):
            pai1, pai2 = random.choices(populacao, weights=[1 / (f + 1e-6) for f in fitness], k=2)
            filho1, filho2 = crossover(pai1, pai2, tipo_crossover)
            nova_populacao.extend([mutacao(filho1, taxa_mutacao), mutacao(filho2, taxa_mutacao)])
        
        populacao = nova_populacao

    # Retornar a melhor solução após as gerações
    fitness = [calcular_fitness(individuo, letras, palavras) for individuo in populacao]
    melhor_individuo = populacao[fitness.index(min(fitness))]
    return dict(zip(letras, melhor_individuo))

@app.route('/solucao', methods=['POST'])
def obter_solucao():
    data = request.get_json()
    palavras = data['palavras']
    geracoes = data['geracoes']
    tamanho_pop = data['tamanho_pop']
    taxa_crossover = data['taxa_crossover']
    taxa_mutacao = data['taxa_mutacao']
    tipo_crossover = data.get('tipo_crossover', 'C1')  # Valor padrão 'C1'

    solucao = algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, tipo_crossover)

    return jsonify(solucao)

if __name__ == '__main__':
    app.run(debug=True)
