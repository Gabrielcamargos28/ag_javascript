from flask import Flask, request, jsonify
import random
import time
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

letras = []
def corrigir_individuo(individuo, tamanho, letras_nao_zero=None):
    global letras
    numeros_disponiveis = set(range(10))
    corrigido = list(individuo)
    usados = set()
    
    for i in range(tamanho):
        if corrigido[i] in usados:
            novo_numero = numeros_disponiveis - usados
            if not novo_numero:
                raise ValueError("Não há números suficientes para corrigir o indivíduo.")
            corrigido[i] = (novo_numero).pop()
        usados.add(corrigido[i])

    return corrigido

def identificar_letras_nao_zero(palavras):
    letras_nao_zero = set()
    for palavra in palavras:
        if palavra: 
            letras_nao_zero.add(palavra[0]) 
    return list(letras_nao_zero)


def calcular_fitness(individuo, letras, palavras):

    letter_to_digit = {letras[i]: individuo[i] for i in range(len(letras))}

    for palavra in palavras:
        if palavra and letter_to_digit[palavra[0]] == 0:
            print(f"Erro: A letra '{palavra[0]}' não pode ser associada ao dígito 0.")
            return float('inf')  

    def palavra_para_numero(palavra):
        numero = ''.join(str(letter_to_digit[letra]) for letra in palavra)
        return int(numero)


    valores_palavras = []
    for palavra in palavras:
        try:
            numero = palavra_para_numero(palavra)
            valores_palavras.append(numero)
        except Exception as e:
            print(f"Erro ao processar a palavra {palavra}: {e}")
            return float('inf')
        
    soma = sum(valores_palavras[:-1])
    resultado = valores_palavras[-1]

    if not validar_soma_carry_over(palavras, valores_palavras, letter_to_digit):
        return float('inf')

    return abs(soma - resultado)


def validar_soma_carry_over(palavras, valores_palavras, letter_to_digit):
    
    palavras_revertidas = [palavra[::-1] for palavra in palavras]
    max_len = max(len(palavra) for palavra in palavras_revertidas)

    carry = 0
    for i in range(max_len):
        soma = carry
        for j in range(len(palavras_revertidas) - 1): 
            if i < len(palavras_revertidas[j]):
                letra = palavras_revertidas[j][i]
                soma += letter_to_digit[letra]

        if i < len(palavras_revertidas[-1]):  
            letra = palavras_revertidas[-1][i]
            soma -= letter_to_digit[letra]

        if soma >= 10:
            carry = 1
        else:
            carry = 0

        if carry == 1 and i == max_len - 1:
            return False 
    return True


def gerar_populacao_inicial(tamanho, letras):
    if len(letras) > 10:
        raise ValueError(f"O número de letras ({len(letras)}) é maior do que o número de dígitos disponíveis (10).")
    populacao = []
    while len(populacao) < tamanho:
        individuo = random.sample(range(10), len(letras))
        populacao.append(individuo)
    return populacao

def mutacao(individuo, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(individuo)), 2)
        individuo[i], individuo[j] = individuo[j], individuo[i]
    return corrigir_individuo(individuo, len(individuo))

def crossover_ciclico(pai1, pai2):
    filho1 = pai1.copy()
    filho2 = pai2.copy()

    visitados1 = [False] * len(pai1)
    visitados2 = [False] * len(pai2)

    i = 0

    while not all(visitados1):
        if not visitados1[i]:
            filho1[i] = pai2[i]
            visitados1[i] = True
            i = pai1.index(filho1[i]) if filho1[i] in pai1 else (i + 1) % len(pai1)
        else:
            i = (i + 1) % len(pai1)

    for j in range(len(pai2)):
        if not visitados2[j]:
            filho2[j] = pai1[j]

    return corrigir_individuo(filho1, len(filho1)), corrigir_individuo(filho2, len(filho2))

def crossover_pmx(pai1, pai2):
    size = len(pai1)
    filho1, filho2 = [-1] * size, [-1] * size
    ponto1, ponto2 = sorted(random.sample(range(size), 2))

    for i in range(ponto1, ponto2 + 1):
        filho1[i] = pai2[i]
        filho2[i] = pai1[i]

    def mapear(filho, pai):
        for i in range(size):
            if filho[i] == -1:
                gene = pai[i]
                while gene in filho:
                    gene = pai[filho.index(gene)]
                filho[i] = gene

    mapear(filho1, pai1)
    mapear(filho2, pai2)
    return corrigir_individuo(filho1, size), corrigir_individuo(filho2, size)

# Seleção: Roleta (S1) ou Torneio (S2)
def selecao_roleta(populacao, fitness):
    return random.choices(populacao, weights=[1 / (f + 1e-6) for f in fitness], k=2)

def selecao_torneio(populacao, fitness, k=3):
    torneio = random.sample(list(zip(populacao, fitness)), k)
    return [sorted(torneio, key=lambda x: x[1])[i][0] for i in range(2)]

# Reinserção: Ordenada (R1) ou Elitismo 20% (R2)
def reinsercao_ordenada(populacao, filhos, fitness, letras, palavras):
    populacao_total = populacao + filhos
    fitness_total = [calcular_fitness(ind, letras, palavras) for ind in populacao_total]
    return [ind for _, ind in sorted(zip(fitness_total, populacao_total))[:len(populacao)]]

def reinsercao_elitismo(populacao, filhos, fitness, letras, palavras):
    elitismo = 0.2
    elite_size = int(len(populacao) * elitismo)
    elite = sorted(populacao, key=lambda ind: calcular_fitness(ind, letras, palavras))[:elite_size]
    return elite + filhos[:len(populacao) - elite_size]

def algoritmo_genetico(palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao, metodo_selecao, tipo_crossover, metodo_reinsercao):
    global letras
    letras = list(set(''.join(palavras))) 
    letras_nao_zero = identificar_letras_nao_zero(palavras)  
    populacao = gerar_populacao_inicial(tamanho_pop, letras)

    populacao_corrigida = [corrigir_individuo(individuo, len(individuo), letras_nao_zero) for individuo in populacao]

    melhor_fitness, melhor_individuo = float('inf'), None
    geracao_melhor = 0

    inicio = time.time()

    for g in range(geracoes):
        fitness = [calcular_fitness(ind, letras, palavras) for ind in populacao_corrigida]

        if metodo_selecao == 'S1':
            selecao = selecao_roleta
        else:
            selecao = lambda pop, fit: selecao_torneio(pop, fit, k=3)

        nova_populacao = []
        while len(nova_populacao) < tamanho_pop:
            pai1, pai2 = selecao(populacao_corrigida, fitness)
            if random.random() < taxa_crossover:
                if tipo_crossover == 'C1':
                    filho1, filho2 = crossover_ciclico(pai1, pai2)
                else:
                    filho1, filho2 = crossover_pmx(pai1, pai2)
            else:
                filho1, filho2 = pai1.copy(), pai2.copy()
            nova_populacao.extend([mutacao(filho1, taxa_mutacao), mutacao(filho2, taxa_mutacao)])

        if metodo_reinsercao == 'R1':
            populacao_corrigida = reinsercao_ordenada(populacao_corrigida, nova_populacao, fitness, letras, palavras)
        else:
            populacao_corrigida = reinsercao_elitismo(populacao_corrigida, nova_populacao, fitness, letras, palavras)

        melhor_atual = min(fitness)

        if melhor_atual < melhor_fitness:
            melhor_fitness = melhor_atual
            melhor_individuo = populacao_corrigida[fitness.index(melhor_fitness)]
            geracao_melhor = g
        
        print(f"Geração {g + 1}/{geracoes}, Melhor Fitness: {melhor_fitness}")
        if melhor_fitness == 0:
            print("Solução encontrada!")
            break

    tempo_execucao = time.time() - inicio
    return dict(zip(letras, melhor_individuo)), melhor_fitness, geracao_melhor, tempo_execucao

@app.route('/solucao', methods=['POST'])
def obter_solucao():
    data = request.get_json()
    palavras = data['palavras']
    geracoes = data['geracoes']
    tamanho_pop = data['tamanho_pop']
    taxa_crossover = data['taxa_crossover']
    taxa_mutacao = data['taxa_mutacao']
    metodo_selecao = data['metodo_selecao']
    tipo_crossover = data['tipo_crossover']
    metodo_reinsercao = data['metodo_reinsercao']

    convergencia_encontrada = False
    num_execucoes = 0
    inicio = time.time()

    while not convergencia_encontrada and num_execucoes < 1000:
        num_execucoes += 1
        print(f"Execução {num_execucoes}/1000")

        solucao, fitness, geracao_melhor, tempo_execucao = algoritmo_genetico(
            palavras, geracoes, tamanho_pop, taxa_crossover, taxa_mutacao,
            metodo_selecao, tipo_crossover, metodo_reinsercao)

        if fitness == 0:
            convergencia_encontrada = True

    if convergencia_encontrada:
        print(solucao)
        return jsonify({'solucao': solucao, 'fitness': fitness, 'geracao_melhor': geracao_melhor, 'tempo_execucao': tempo_execucao})
    else:
        return jsonify({'error': 'Solução não encontrada após 1000 execuções'}), 500


@app.route('/report', methods=['GET'])
def executar_testes():
    print("INICIANDO")
    palavras_problema1 = ['SEND', 'MORE', 'MONEY']
    geracoes = 50
    tamanho_pop = 100

    # Parâmetros das configurações
    taxas_crossover = [0.6, 0.8]
    taxas_mutacao = [0.05, 0.1]
    metodos_selecao = ['S1', 'S2']
    tipos_crossover = ['C1', 'C2']
    metodos_reinsercao = ['R1', 'R2']

    configuracoes = []
    dados_completos = []

    # 1. Executar 24 configurações com 1000 execuções cada
    for tc in taxas_crossover:
        for tm in taxas_mutacao:
            for sel in metodos_selecao:
                for cx in tipos_crossover:
                    for rein in metodos_reinsercao:
                        taxa_crossover = 0.8 if rein == 'R2' else tc

                        configuracao = {
                            'taxa_crossover': taxa_crossover,
                            'taxa_mutacao': tm,
                            'metodo_selecao': sel,
                            'tipo_crossover': cx,
                            'metodo_reinsercao': rein
                        }
                        print(f"Executando configuração: {configuracao}")

                        convergencias = 0
                        tempos_execucao = []
                        for i in range(1000):  # 1000 execuções
                            print(f"Executando {i + 1}/1000")
                            inicio = time.time()
                            solucao, fitness, geracao_melhor, tempo_execucao = algoritmo_genetico(
                            palavras_problema1, geracoes, tamanho_pop,
                            taxa_crossover, tm, sel, cx, rein
                            )

                            fim = time.time()
                            tempo_execucao = fim - inicio
                            tempos_execucao.append(tempo_execucao)

                            if fitness == 0:  # Considera convergência válida
                                convergencias += 1

                            dados_completos.append({
                                'configuracao': str(configuracao),
                                'execucao': i + 1,
                                'fitness': fitness,
                                'tempo_execucao': tempo_execucao,
                                'geracao_melhor': geracao_melhor
                            })

                        percentual_convergencia = (convergencias / 1000) * 100
                        tempo_medio = sum(tempos_execucao) / len(tempos_execucao)

                        configuracoes.append({
                            'configuracao': configuracao,
                            'percentual_convergencia': percentual_convergencia,
                            'tempo_medio': tempo_medio
                        })

    # Salvar todas as execuções em um Excel
    df_dados = pd.DataFrame(dados_completos)
    df_dados.to_excel('execucoes_24_configuracoes.xlsx', index=False)

    print("Resultados completos salvos em 'execucoes_24_configuracoes.xlsx'.")

    # 2. Selecionar as 4 melhores configurações com base em convergência e tempo
    melhores_configuracoes = sorted(configuracoes, key=lambda x: (x['percentual_convergencia'], -x['tempo_medio']), reverse=True)[:4]
    print("4 melhores configurações selecionadas:")
    for i, config in enumerate(melhores_configuracoes, start=1):
        print(f"{i}: {config}")

    # 3. Executar as 4 melhores configurações nos 5 problemas
    problemas = [
        ['SEND', 'MORE', 'MONEY'],
        ['PARA', 'AMAPA', 'GOIAS'],
        ['CROSS', 'ROADS', 'DANGER'],
        ['EAT', 'THAT', 'APPLE'],
        ['DONALD', 'GERALD', 'ROBERT']
    ]

    resultados_finais = []

    for melhor_config in melhores_configuracoes:
        for palavras in problemas:
            convergencias = 0
            tempos_execucao = []
            for i in range(1000):
                print(f"Executando no laço das 4 melhores {i + 1}/1000")
                inicio = time.time()
                solucao, fitness, geracao_melhor = algoritmo_genetico(
                    palavras, geracoes, tamanho_pop,
                    melhor_config['configuracao']['taxa_crossover'],
                    melhor_config['configuracao']['taxa_mutacao'],
                    melhor_config['configuracao']['metodo_selecao'],
                    melhor_config['configuracao']['tipo_crossover'],
                    melhor_config['configuracao']['metodo_reinsercao']
                )
                fim = time.time()
                tempo_execucao = fim - inicio
                tempos_execucao.append(tempo_execucao)

                if fitness == 0:
                    convergencias += 1

            percentual_convergencia = (convergencias / 1000) * 100
            tempo_medio = sum(tempos_execucao) / len(tempos_execucao)

            resultados_finais.append({
                'configuracao': melhor_config['configuracao'],
                'problema': palavras,
                'percentual_convergencia': percentual_convergencia,
                'tempo_medio': tempo_medio,
                'fitness': fitness,
                'palabras': palavras
            })

    # Salvar os resultados finais das 4 melhores configurações
    df_resultados_finais = pd.DataFrame(resultados_finais)
    df_resultados_finais.to_excel('resultados_finais_4_configuracoes.xlsx', index=False)

    print("Resultados finais salvos em 'resultados_finais_4_configuracoes.xlsx'.")


if __name__ == '__main__':
    #executar_testes()
    app.run(debug=True)
