            Cálculo do "Potencial de Gols" do 1º Tempo

Primeiro, calculamos uma métrica que eu chamei de potencial_gols_1T. Ela representa a "expectativa" de gols no primeiro tempo da partida, somando quatro médias fundamentais:

    Média de gols que o Time da Casa MARCA em casa no 1ºT. (Força de ataque do Time A)

    Média de gols que o Time da Casa SOFRE em casa no 1ºT. (Fraqueza defensiva do Time A)

    Média de gols que o Time de Fora MARCA fora no 1ºT. (Força de ataque do Time B)

    Média de gols que o Time de Fora SOFRE fora no 1ºT. (Fraqueza defensiva do Time B)

A fórmula no código é esta:
Python

potencial_gols_1T = (analise_a.media_placar_casa_1t + 
                     medias_sofridas_a['gols_1t'] + 
                     analise_b.media_placar_fora_1t + 
                     medias_sofridas_b['gols_1t'])

A ideia é que, quanto maior for a força de ataque de um time e a fraqueza defensiva do outro, maior será o "potencial" de gols na partida.

        Conversão para Porcentagem de Probabilidade

O "Potencial de Gols" que calculamos é um número (ex: 1.85). Para transformá-lo na porcentagem que você vê no card (ex: 98%), nós o multiplicamos por um "fator de ajuste" e aplicamos um teto de segurança.

Veja o código para o 1º Tempo:
Python

prob_gols_1T = {
    'over_0_5': min(98, int(potencial_gols_1T * 60)),
    'over_1_5': min(95, int(potencial_gols_1T * 25)),
}

Vamos analisar a linha de "Mais de 0.5 Gols (1T)": min(98, int(potencial_gols_1T * 60))

    potencial_gols_1T * 60: Pegamos o potencial de gols e o multiplicamos por 60. Este multiplicador (60) é o coração da heurística. É um peso que ajustamos para converter a expectativa de gols em uma probabilidade percentual. Um multiplicador maior significa que a probabilidade sobe mais rápido.

    int(...): Apenas para garantir que o resultado seja um número inteiro.

    min(98, ...): Esta é uma trava de segurança. Ela diz: "O resultado do cálculo nunca pode ser maior que 98%". Isso evita que a probabilidade chegue a valores irreais como 150%, por exemplo.

Para "Mais de 1.5 Gols (1T)", a lógica é a mesma, mas o multiplicador é bem menor (25), pois a chance de saírem dois ou mais gols é naturalmente menor do que a de sair pelo menos um.

Exemplo Prático:

Vamos supor os seguintes dados para o 1º tempo:

    Média de gols marcados do time da casa: 0.8

    Média de gols sofridos do time da casa: 0.5

    Média de gols marcados do time de fora: 0.6

    Média de gols sofridos do time de fora: 0.7

    Cálculo do Potencial:
    potencial_gols_1T = 0.8 + 0.5 + 0.6 + 0.7 = 2.6

    Cálculo das Probabilidades:

        Mais de 0.5 Gols (1T):
        int(2.6 * 60) = int(156) = 156.
        min(98, 156) = 98%. (A trava de segurança foi ativada).

        Mais de 1.5 Gols (1T):
        int(2.6 * 25) = int(65) = 65.
        min(95, 65) = 65%.